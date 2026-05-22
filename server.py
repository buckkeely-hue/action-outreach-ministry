#!/usr/bin/env python3
"""Action Outreach Ministry — standalone web server. No pip dependencies."""

import hashlib, hmac, json, os, secrets, smtplib, threading, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
from pathlib import Path
from urllib.parse import urlparse

PORT      = 8000
BASE_DIR  = Path(__file__).parent

USERS_FILE        = BASE_DIR / 'ministry_users.json'
SESSIONS_FILE     = BASE_DIR / 'ministry_sessions.json'
TXNS_FILE         = BASE_DIR / 'ministry_transactions.json'
SMTP_FILE         = BASE_DIR / 'smtp_config.json'
INFO_REQUESTS_FILE = BASE_DIR / 'info_requests.json'

KASEY_EMAIL = 'kasey.carruthers@gmail.com'

ADMIN_RECOVERY_CODE = 'outreach2024reset'

SESSIONS      = {}
SESSIONS_LOCK = threading.Lock()

RESET_TOKENS      = {}   # token -> {username, expires}
RESET_TOKENS_LOCK = threading.Lock()

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css':  'text/css',
    '.js':   'application/javascript',
    '.json': 'application/json',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.ico':  'image/x-icon',
    '.svg':  'image/svg+xml',
    '.txt':  'text/plain',
}

# ── File helpers ──────────────────────────────────────────────────────────────

def _load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    tmp = str(path) + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def _load_users():        return _load_json(USERS_FILE, {})
def _save_users(u):       _save_json(USERS_FILE, u)
def _load_txns():         return _load_json(TXNS_FILE, [])
def _save_txns(t):        _save_json(TXNS_FILE, t)
def _load_smtp():         return _load_json(SMTP_FILE, {})
def _save_smtp(cfg):      _save_json(SMTP_FILE, cfg)
def _load_info_requests(): return _load_json(INFO_REQUESTS_FILE, [])
def _save_info_requests(r): _save_json(INFO_REQUESTS_FILE, r)

# ── Email ─────────────────────────────────────────────────────────────────────

def _send_email(smtp_cfg, to_addr, subject, body_text):
    host      = smtp_cfg.get('host', '')
    port      = int(smtp_cfg.get('port', 587))
    user      = smtp_cfg.get('username', '')
    password  = smtp_cfg.get('password', '')
    from_name = smtp_cfg.get('from_name', 'Action Outreach Ministry')
    tls_mode  = smtp_cfg.get('tls', 'starttls')
    if not host or not user or not password:
        raise ValueError('SMTP not configured')
    msg = MIMEMultipart()
    msg['From']    = f'{from_name} <{user}>'
    msg['To']      = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body_text, 'plain'))
    if tls_mode == 'ssl':
        with smtplib.SMTP_SSL(host, port, timeout=15) as s:
            s.login(user, password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.ehlo()
            s.starttls()
            s.login(user, password)
            s.send_message(msg)

def _send_reset_email(smtp_cfg, to_addr, token, base_url):
    link = f'{base_url}?reset_token={token}'
    body = (
        'You requested a password reset for your Action Outreach Ministry account.\n\n'
        f'Click the link below to set a new password (expires in 1 hour):\n{link}\n\n'
        'If you did not request this, you can ignore this email.'
    )
    _send_email(smtp_cfg, to_addr, 'Password Reset — Action Outreach Ministry', body)

# ── Password ──────────────────────────────────────────────────────────────────

def _hash_pw(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, h

def _verify_pw(password, salt, stored):
    _, h = _hash_pw(password, salt)
    return hmac.compare_digest(h, stored)

# ── Sessions ──────────────────────────────────────────────────────────────────

def _load_sessions():
    global SESSIONS
    SESSIONS = _load_json(SESSIONS_FILE, {})

def _save_sessions():
    with SESSIONS_LOCK:
        _save_json(SESSIONS_FILE, SESSIONS)

def _get_session(handler):
    cookie = handler.headers.get('Cookie', '')
    for part in cookie.split(';'):
        part = part.strip()
        if part.startswith('ms_session='):
            token = part[len('ms_session='):]
            with SESSIONS_LOCK:
                return SESSIONS.get(token)
    return None

def _create_session(username):
    token = secrets.token_hex(32)
    with SESSIONS_LOCK:
        SESSIONS[token] = {'username': username, 'created': int(time.time())}
    _save_sessions()
    return token

def _destroy_session(handler):
    cookie = handler.headers.get('Cookie', '')
    for part in cookie.split(';'):
        part = part.strip()
        if part.startswith('ms_session='):
            token = part[len('ms_session='):]
            with SESSIONS_LOCK:
                SESSIONS.pop(token, None)
    _save_sessions()

# ── Seed ─────────────────────────────────────────────────────────────────────

def _seed_admin():
    users = _load_users()
    if not users:
        salt, h = _hash_pw('Ministrey2025')
        users['admin'] = {
            'salt': salt, 'hash': h, 'is_admin': True,
            'contact_email': '', 'created': int(time.time())
        }
        _save_users(users)

# ── Handler ───────────────────────────────────────────────────────────────────

class AOMHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def handle_error(self, request, client_address):
        pass

    # ── Low-level response helpers ────────────────────────────────────────────

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json(self, data, status=200, cookie=None):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(body)

    def _err(self, msg, status=400):
        self._json({'error': msg}, status)

    def _body(self):
        n = int(self.headers.get('Content-Length', 0))
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except Exception:
            return {}

    def _require_admin(self):
        sess = _get_session(self)
        if not sess:
            self._err('Not authenticated', 401)
            return None
        users = _load_users()
        u = users.get(sess['username'])
        if not u or not u.get('is_admin'):
            self._err('Admin required', 403)
            return None
        return sess['username']

    # ── OPTIONS (preflight) ───────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET ───────────────────────────────────────────────────────────────────

    def do_GET(self):
        path = urlparse(self.path).path.rstrip('/') or '/'

        if path == '/api/auth/status':
            return self._api_status()
        if path == '/api/admin/users':
            return self._api_admin_users()
        if path == '/api/admin/transactions':
            return self._api_admin_txns()
        if path == '/api/admin/smtp-config':
            return self._api_get_smtp()
        if path == '/api/admin/info-requests':
            return self._api_admin_info_requests()

        # Static file
        file_path = BASE_DIR / path.lstrip('/')
        if file_path.is_dir():
            file_path = file_path / 'index.html'
        if not file_path.exists() or not file_path.is_file():
            file_path = BASE_DIR / 'index.html'

        data = file_path.read_bytes()
        mime = MIME_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ── POST ──────────────────────────────────────────────────────────────────

    def do_POST(self):
        path = urlparse(self.path).path.rstrip('/')
        routes = {
            '/api/auth/login':            self._api_login,
            '/api/auth/logout':           self._api_logout,
            '/api/auth/reset':            self._api_reset,
            '/api/auth/request-reset':    self._api_request_reset,
            '/api/auth/reset-confirm':    self._api_reset_confirm,
            '/api/admin/create-user':     self._api_create_user,
            '/api/admin/delete-user':     self._api_delete_user,
            '/api/admin/set-password':    self._api_set_password,
            '/api/admin/toggle-admin':    self._api_toggle_admin,
            '/api/admin/smtp-config':     self._api_save_smtp,
            '/api/admin/smtp-test':       self._api_test_smtp,
            '/api/donate/record':         self._api_donate_record,
            '/api/info-request':          self._api_info_request,
            '/api/contact':               self._api_contact,
        }
        fn = routes.get(path)
        if fn:
            fn()
        else:
            self._err('Not found', 404)

    # ── Auth endpoints ────────────────────────────────────────────────────────

    def _api_status(self):
        sess = _get_session(self)
        if not sess:
            return self._json({'authenticated': False})
        users = _load_users()
        u = users.get(sess['username'])
        if not u:
            return self._json({'authenticated': False})
        self._json({
            'authenticated': True,
            'username': sess['username'],
            'is_admin': u.get('is_admin', False),
            'contact_email': u.get('contact_email', '')
        })

    def _api_login(self):
        b = self._body()
        username = b.get('username', '').strip()
        password = b.get('password', '')
        if not username or not password:
            return self._err('Username and password required')
        users = _load_users()
        key = next((k for k in users if k.lower() == username.lower()), None)
        if not key or not _verify_pw(password, users[key]['salt'], users[key]['hash']):
            return self._err('Invalid credentials', 401)
        token = _create_session(key)
        cookie = f'ms_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=604800'
        self._json({'ok': True, 'username': key, 'is_admin': users[key].get('is_admin', False)}, cookie=cookie)

    def _api_logout(self):
        _destroy_session(self)
        self._json({'ok': True}, cookie='ms_session=; Path=/; Max-Age=0')

    def _api_reset(self):
        b = self._body()
        if b.get('recovery_code', '') != ADMIN_RECOVERY_CODE:
            return self._err('Invalid recovery code', 401)
        users = _load_users()
        new_user = b.get('username', '').strip()
        new_pw   = b.get('password', '')
        admin_key = next((k for k, v in users.items() if v.get('is_admin')), None)
        if not admin_key:
            if not new_user or not new_pw:
                return self._err('No admin found — provide username and password')
            salt, h = _hash_pw(new_pw)
            users[new_user] = {'salt': salt, 'hash': h, 'is_admin': True,
                               'contact_email': '', 'created': int(time.time())}
            _save_users(users)
            return self._json({'ok': True})
        if new_user and new_user != admin_key:
            users[new_user] = users.pop(admin_key)
            admin_key = new_user
        if new_pw:
            salt, h = _hash_pw(new_pw)
            users[admin_key]['salt'] = salt
            users[admin_key]['hash'] = h
        _save_users(users)
        self._json({'ok': True})

    # ── Admin endpoints ───────────────────────────────────────────────────────

    def _api_admin_users(self):
        if not self._require_admin():
            return
        users = _load_users()
        self._json([
            {'username': k, 'is_admin': v.get('is_admin', False),
             'contact_email': v.get('contact_email', ''), 'created': v.get('created', 0)}
            for k, v in users.items()
        ])

    def _api_create_user(self):
        admin = self._require_admin()
        if not admin:
            return
        b = self._body()
        username = b.get('username', '').strip()
        password = b.get('password', '')
        if not username or not password:
            return self._err('Username and password required')
        users = _load_users()
        if any(k.lower() == username.lower() for k in users):
            return self._err('Username already exists')
        salt, h = _hash_pw(password)
        users[username] = {
            'salt': salt, 'hash': h,
            'is_admin': bool(b.get('is_admin', False)),
            'contact_email': b.get('contact_email', '').strip(),
            'created': int(time.time())
        }
        _save_users(users)
        self._json({'ok': True})

    def _api_delete_user(self):
        admin = self._require_admin()
        if not admin:
            return
        username = self._body().get('username', '').strip()
        if username == admin:
            return self._err('Cannot delete your own account')
        users = _load_users()
        if username not in users:
            return self._err('User not found')
        del users[username]
        _save_users(users)
        self._json({'ok': True})

    def _api_set_password(self):
        admin = self._require_admin()
        if not admin:
            return
        b = self._body()
        username = b.get('username', '').strip()
        password = b.get('password', '')
        if not username or not password:
            return self._err('Username and password required')
        users = _load_users()
        if username not in users:
            return self._err('User not found')
        salt, h = _hash_pw(password)
        users[username]['salt'] = salt
        users[username]['hash'] = h
        _save_users(users)
        self._json({'ok': True})

    def _api_toggle_admin(self):
        admin = self._require_admin()
        if not admin:
            return
        username = self._body().get('username', '').strip()
        if username == admin:
            return self._err('Cannot change your own admin status')
        users = _load_users()
        if username not in users:
            return self._err('User not found')
        users[username]['is_admin'] = not users[username].get('is_admin', False)
        _save_users(users)
        self._json({'ok': True, 'is_admin': users[username]['is_admin']})

    def _api_admin_txns(self):
        if not self._require_admin():
            return
        self._json(_load_txns())

    # ── SMTP config ───────────────────────────────────────────────────────────

    def _api_get_smtp(self):
        if not self._require_admin():
            return
        cfg = _load_smtp()
        safe = {k: v for k, v in cfg.items() if k != 'password'}
        safe['has_password'] = bool(cfg.get('password'))
        self._json(safe)

    def _api_save_smtp(self):
        if not self._require_admin():
            return
        b = self._body()
        cfg = _load_smtp()
        for field in ('host', 'port', 'username', 'from_name', 'tls'):
            if field in b:
                cfg[field] = b[field]
        if b.get('password'):
            cfg['password'] = b['password']
        _save_smtp(cfg)
        self._json({'ok': True})

    def _api_test_smtp(self):
        admin = self._require_admin()
        if not admin:
            return
        cfg = _load_smtp()
        users = _load_users()
        to_addr = users.get(admin, {}).get('contact_email') or cfg.get('username', '')
        if not to_addr:
            return self._err('No email address on file for your account')
        try:
            _send_email(cfg, to_addr, 'SMTP Test — Action Outreach Ministry',
                        'Your SMTP settings are working correctly.')
            self._json({'ok': True, 'sent_to': to_addr})
        except Exception as e:
            self._err(str(e), 500)

    # ── Email-based password reset ────────────────────────────────────────────

    def _api_request_reset(self):
        b = self._body()
        identifier = b.get('email', '').strip()
        if not identifier:
            return self._err('Email required')
        users = _load_users()
        found_key = next(
            (k for k, u in users.items() if u.get('contact_email', '').lower() == identifier.lower()),
            None
        )
        if not found_key:
            return self._json({'ok': True})   # don't reveal whether email exists
        cfg = _load_smtp()
        token = secrets.token_urlsafe(32)
        with RESET_TOKENS_LOCK:
            RESET_TOKENS[token] = {'username': found_key, 'expires': time.time() + 3600}
        host   = self.headers.get('Host', 'actionoutreachministry.com')
        proto  = 'https' if self.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        try:
            _send_reset_email(cfg, users[found_key]['contact_email'], token, f'{proto}://{host}')
        except Exception as e:
            return self._err(f'Email could not be sent: {e}', 500)
        self._json({'ok': True})

    def _api_reset_confirm(self):
        b = self._body()
        token  = b.get('token', '').strip()
        new_pw = b.get('password', '')
        if not token or not new_pw:
            return self._err('Token and password required')
        with RESET_TOKENS_LOCK:
            entry = RESET_TOKENS.get(token)
        if not entry or time.time() > entry['expires']:
            return self._err('Reset link expired or invalid', 401)
        users    = _load_users()
        username = entry['username']
        if username not in users:
            return self._err('User not found', 404)
        salt, h = _hash_pw(new_pw)
        users[username]['salt'] = salt
        users[username]['hash'] = h
        _save_users(users)
        with RESET_TOKENS_LOCK:
            RESET_TOKENS.pop(token, None)
        self._json({'ok': True})

    def _api_contact(self):
        b = self._body()
        name    = b.get('name', '').strip()
        email   = b.get('email', '').strip()
        subject = b.get('subject', '').strip()
        message = b.get('message', '').strip()
        if not name or not email or not subject or not message:
            return self._err('All fields are required')
        entry = {'name': name, 'email': email, 'subject': subject,
                 'message': message, 'timestamp': int(time.time())}
        contacts = _load_json(BASE_DIR / 'contacts.json', [])
        contacts.append(entry)
        _save_json(BASE_DIR / 'contacts.json', contacts)
        sep = '=' * 50
        body_text = (
            f'New Contact Message — Action Outreach Ministry\n'
            f'{sep}\n\n'
            f'From:    {name} <{email}>\n'
            f'Subject: {subject}\n\n'
            f'Message:\n{message}\n\n'
            f'Sent: {time.strftime("%B %d, %Y at %I:%M %p", time.localtime())}\n'
        )
        try:
            cfg = _load_smtp()
            _send_email(cfg, KASEY_EMAIL, f'Contact: {subject} — from {name}', body_text)
        except Exception:
            pass
        self._json({'ok': True})

    def _api_info_request(self):
        b = self._body()
        first    = b.get('first', '').strip()
        last     = b.get('last', '').strip()
        street   = b.get('street', '').strip()
        city     = b.get('city', '').strip()
        state    = b.get('state', '').strip()
        zip_code = b.get('zip', '').strip()
        email    = b.get('email', '').strip()
        phone    = b.get('phone', '').strip()
        interests = b.get('interests', [])
        comments = b.get('comments', '').strip()
        if not first or not last or not street or not city or not state or not zip_code:
            return self._err('Name and mailing address are required')
        entry = {
            'id':        secrets.token_hex(6),
            'timestamp': int(time.time()),
            'name':      f'{first} {last}',
            'address':   f'{street}, {city}, {state} {zip_code}',
            'email':     email,
            'phone':     phone,
            'interests': interests,
            'comments':  comments,
        }
        reqs = _load_info_requests()
        reqs.insert(0, entry)
        _save_info_requests(reqs)
        # Email Kasey
        interest_lines = '\n  '.join(interests) if interests else '(none specified)'
        sep = '=' * 50
        body_text = (
            f'New Information Request — Action Outreach Ministry\n'
            f'{sep}\n\n'
            f'Name:    {entry["name"]}\n'
            f'Address: {entry["address"]}\n'
            f'Email:   {email or "(not provided)"}\n'
            f'Phone:   {phone or "(not provided)"}\n\n'
            f'Information Requested:\n  {interest_lines}\n\n'
            f'Comments:\n  {comments or "(none)"}\n\n'
            f'Submitted: {time.strftime("%B %d, %Y at %I:%M %p", time.localtime())}\n'
        )
        try:
            cfg = _load_smtp()
            _send_email(cfg, KASEY_EMAIL, f'Info Request: {entry["name"]} — Action Outreach Ministry', body_text)
        except Exception:
            pass  # Save succeeded; email failure is non-fatal
        self._json({'ok': True})

    def _api_admin_info_requests(self):
        if not self._require_admin():
            return
        self._json(_load_info_requests())

    def _api_donate_record(self):
        b = self._body()
        txn = {
            'id':        secrets.token_hex(8),
            'amount':    b.get('amount', 0),
            'fund':      b.get('fund', 'general'),
            'freq':      b.get('freq', 'once'),
            'processor': b.get('processor', 'paypal'),
            'timestamp': int(time.time())
        }
        txns = _load_txns()
        txns.append(txn)
        _save_txns(txns)
        self._json({'ok': True})


# ── Boot ──────────────────────────────────────────────────────────────────────

_load_sessions()
_seed_admin()

if __name__ == '__main__':
    server = ThreadedHTTPServer(('0.0.0.0', PORT), AOMHandler)
    print(f'Action Outreach Ministry server → http://0.0.0.0:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
