#!/usr/bin/env python3
"""Action Outreach Ministry — standalone web server. No pip dependencies."""

import hashlib, hmac, json, os, secrets, smtplib, socket, threading, time
import urllib.error, urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Force IPv4 — VPS has no IPv6 routing
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_ipv4(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else results
socket.getaddrinfo = _getaddrinfo_ipv4

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
from pathlib import Path
from urllib.parse import urlparse

PORT      = 8000
BASE_DIR  = Path(__file__).parent

USERS_FILE         = BASE_DIR / 'ministry_users.json'
SESSIONS_FILE      = BASE_DIR / 'ministry_sessions.json'
TXNS_FILE          = BASE_DIR / 'ministry_transactions.json'
DONATIONS_FILE     = BASE_DIR / 'confirmed_donations.json'
SMTP_FILE          = BASE_DIR / 'smtp_config.json'
INFO_REQUESTS_FILE = BASE_DIR / 'info_requests.json'
CONTENT_FILE       = BASE_DIR / 'ministry_content.json'
PENDING_FILE       = BASE_DIR / 'ministry_pending.json'
CONTACTS_FILE      = BASE_DIR / 'contacts.json'

ADMIN_RECOVERY_CODE = 'outreach2024reset'

SESSIONS      = {}
SESSIONS_LOCK = threading.Lock()

RESET_TOKENS      = {}
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

CONTENT_DEFAULTS = {
    'settings': {
        'ministryName': 'Action Outreach Ministry',
        'tagline': 'Reaching the World for Christ',
        'location': 'Pensacola, FL',
        'address': '',
        'phone': '(850) 000-0000',
        'contactEmail': 'info@actionoutreachministry.com',
        'hours': '',
        'notifyEmail': '',
        'ntfyTopic': 'aom-5b0888c03c48',
        'paypalEmail': '',
        'cashapp': '',
        'venmo': '',
        'zelle': '',
    },
    'outreachHeroTitle': 'Reaching Hearts, Changing Lives',
    'outreachHeroText': 'Action Outreach Ministry is committed to spreading the Gospel of Jesus Christ through compassionate service, community outreach, and discipleship.',
    'aboutTitle': 'About Our Ministry',
    'aboutText1': 'Founded on faith and fueled by love, Action Outreach Ministry has been serving the community for over two decades. We believe every person is made in the image of God and deserves to hear the Good News. Our volunteers, missionaries, and partners work tirelessly across local and international communities to bring transformation through the power of the Gospel.',
    'aboutText2': 'Whether you join us in person, volunteer your time, or support us financially — you are a vital part of this mission. Together, we are the hands and feet of Jesus.',
    'cards': [
        {'icon': '🌍', 'title': 'Global Missions', 'text': 'We partner with missionaries worldwide to bring hope, healing, and the message of salvation to unreached communities.'},
        {'icon': '🍞', 'title': 'Community Feeding', 'text': 'Our weekly food pantry serves hundreds of families, meeting physical needs while sharing the love of Christ.'},
        {'icon': '📖', 'title': 'Bible Distribution', 'text': 'We distribute Bibles and discipleship materials to prisons, shelters, and underserved communities locally and abroad.'},
        {'icon': '👨‍👩‍👧', 'title': 'Family Restoration', 'text': "Through counseling, support groups, and prayer, we help families find healing and walk in God's purpose."},
    ],
    'testimoniesHeroTitle': 'Stories of Transformation',
    'testimoniesHeroText': 'God is moving. Read how lives are being changed through prayer, outreach, and the power of the Gospel.',
    'testimonies': [
        {'quote': 'I was homeless and without hope. Action Outreach found me, fed me, and shared Jesus with me. Today I have a home, a family, and a faith that never wavers.', 'author': '— Marcus T., Pensacola FL'},
        {'quote': 'Through the prayer ministry, my marriage was completely restored. We were on the verge of divorce and God showed up in a miraculous way.', 'author': '— Sandra & James W.'},
        {'quote': 'The Bible they gave me in prison changed my life. I got out, found this ministry, and now I volunteer every week to give back what was given to me.', 'author': '— David R.'},
    ],
    'eventsHeroTitle': 'Upcoming Events',
    'eventsHeroText': 'Join us as we gather for worship, outreach, and fellowship. All are welcome.',
    'events': [
        {'month': 'MAY', 'day': '18', 'title': 'Community Prayer Walk', 'meta': '9:00 AM · Downtown Pensacola · Free', 'text': 'Join us as we walk through the community, praying over businesses, schools, and families. Wear comfortable shoes and bring a heart for the city.'},
        {'month': 'MAY', 'day': '25', 'title': 'Food Pantry & Gospel Outreach', 'meta': '10:00 AM – 2:00 PM · Ministry Center · Free', 'text': 'Hundreds of families will receive groceries and hear the Gospel. Volunteers needed — sign up at the contact form below.'},
        {'month': 'JUN', 'day': '7', 'title': 'Revival Night', 'meta': '6:00 PM · Main Sanctuary · Free', 'text': 'A night of worship, testimonies, and the Word. Come expectant — God moves powerfully when His people gather.'},
        {'month': 'JUN', 'day': '21', 'title': 'Youth Summer Kickoff', 'meta': '11:00 AM · Ministry Grounds · Free', 'text': 'Games, food, and a powerful message for our youth. Bring the whole family.'},
    ],
    'newsletter': {
        'title':   'Ministry Newsletter',
        'issue':   'Spring 2026',
        'date':    'May 2026',
        'visible': False,
        'body':    '<p>Welcome to the Action Outreach Ministry newsletter. Edit this content in the Admin panel under the <strong>Newsletter</strong> tab.</p>',
    },
    'prayerHeroTitle': 'Urgent Prayer Requests',
    'prayerHeroText': 'We believe in the power of prayer. Submit your request and our prayer team will stand in agreement with you.',
    'prayers': [
        {'urgent': True,  'text': 'Please pray for our missionary team in Haiti who are currently in a dangerous region. Pray for their safety, provision, and boldness.', 'meta': 'Submitted by Ministry Team · May 1, 2026'},
        {'urgent': True,  'text': "Pray for Brother James who is in ICU following emergency surgery. His family needs strength and God's healing touch.", 'meta': 'Submitted by Family · May 2, 2026'},
        {'urgent': False, 'text': 'Pray for our upcoming mission trip to Guatemala — finances, visas, and spiritual preparation for the entire team.', 'meta': 'Submitted by Missions Dept. · Apr 28, 2026'},
    ],
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

def _load_users():          return _load_json(USERS_FILE, {})
def _save_users(u):         _save_json(USERS_FILE, u)
def _load_txns():               return _load_json(TXNS_FILE, [])
def _save_txns(t):              _save_json(TXNS_FILE, t)
def _load_donations():          return _load_json(DONATIONS_FILE, [])
def _save_donations(d):         _save_json(DONATIONS_FILE, d)
def _load_smtp():           return _load_json(SMTP_FILE, {})
def _save_smtp(cfg):        _save_json(SMTP_FILE, cfg)
def _load_info_requests():  return _load_json(INFO_REQUESTS_FILE, [])
def _save_info_requests(r): _save_json(INFO_REQUESTS_FILE, r)
def _load_pending():        return _load_json(PENDING_FILE, {'testimonies': [], 'prayers': []})
def _save_pending(p):       _save_json(PENDING_FILE, p)
def _load_contacts():       return _load_json(CONTACTS_FILE, [])
def _save_contacts(c):      _save_json(CONTACTS_FILE, c)

def _load_content():
    content = _load_json(CONTENT_FILE, None)
    if content is None:
        return dict(CONTENT_DEFAULTS)
    # Ensure settings key exists
    if 'settings' not in content:
        content['settings'] = dict(CONTENT_DEFAULTS['settings'])
    else:
        for k, v in CONTENT_DEFAULTS['settings'].items():
            content['settings'].setdefault(k, v)
    return content

def _notify_email():
    content = _load_json(CONTENT_FILE, {})
    email = content.get('settings', {}).get('notifyEmail', '')
    if not email:
        email = _load_smtp().get('username', '')
    return email

def _ntfy_topic():
    content = _load_json(CONTENT_FILE, {})
    return content.get('settings', {}).get('ntfyTopic', '')

def _push(title, message, tags='bell'):
    topic = _ntfy_topic()
    if not topic:
        return
    try:
        req = urllib.request.Request(
            f'https://ntfy.sh/{topic}',
            data=message.encode(),
            headers={'Title': title, 'Tags': tags, 'Priority': 'default'},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass

def _seed_content():
    if not CONTENT_FILE.exists():
        _save_json(CONTENT_FILE, CONTENT_DEFAULTS)

# ── Email ─────────────────────────────────────────────────────────────────────

def _send_email_gmail_api(smtp_cfg, to_addr, subject, body_text):
    import base64
    from email.mime.text import MIMEText as _MIMEText
    client_id     = smtp_cfg.get('gmail_client_id', '')
    client_secret = smtp_cfg.get('gmail_client_secret', '')
    refresh_token = smtp_cfg.get('gmail_refresh_token', '')
    send_as       = smtp_cfg.get('gmail_send_as', '')
    if not (client_id and client_secret and refresh_token):
        raise ValueError('Gmail API credentials not configured')
    # Refresh access token
    payload = json.dumps({
        'client_id': client_id, 'client_secret': client_secret,
        'refresh_token': refresh_token, 'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token',
        data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=10) as r:
        access_token = json.load(r)['access_token']
    # Build message
    from_name = smtp_cfg.get('from_name', 'Action Outreach Ministry')
    msg = MIMEMultipart()
    msg['From']    = f'{from_name} <{send_as}>' if send_as else send_as
    msg['To']      = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body_text, 'plain'))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    send_req = urllib.request.Request(
        'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
        data=json.dumps({'raw': raw}).encode(),
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(send_req, timeout=15) as r:
            pass
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Gmail API error {e.code}: {e.reason}')

def _send_email(smtp_cfg, to_addr, subject, body_text):
    if smtp_cfg.get('gmail_refresh_token'):
        _send_email_gmail_api(smtp_cfg, to_addr, subject, body_text)
        return
    from_name  = smtp_cfg.get('from_name', 'Action Outreach Ministry')
    from_email = smtp_cfg.get('username', '')
    brevo_key  = smtp_cfg.get('brevo_api_key', '')
    if brevo_key:
        payload = json.dumps({
            'sender': {'name': from_name, 'email': from_email or 'actionoutreachministry@gmail.com'},
            'to': [{'email': to_addr}],
            'subject': subject,
            'textContent': body_text,
        }).encode()
        req = urllib.request.Request(
            'https://api.brevo.com/v3/smtp/email',
            data=payload,
            headers={'Content-Type': 'application/json', 'api-key': brevo_key},
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                pass
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'Brevo error {e.code}: {e.reason}')
        return
    host     = smtp_cfg.get('host', '')
    port     = int(smtp_cfg.get('port', 587))
    user     = smtp_cfg.get('username', '')
    password = smtp_cfg.get('password', '')
    tls_mode = smtp_cfg.get('tls', 'starttls')
    if not host or not user or not password:
        raise ValueError('Email not configured')
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
        if path == '/api/content':
            return self._api_get_content()
        if path == '/api/admin/users':
            return self._api_admin_users()
        if path == '/api/admin/transactions':
            return self._api_admin_txns()
        if path == '/api/admin/smtp-config':
            return self._api_get_smtp()
        if path == '/api/admin/info-requests':
            return self._api_admin_info_requests()
        if path == '/api/admin/contacts':
            return self._api_admin_contacts()
        if path == '/api/admin/pending':
            return self._api_admin_pending()
        if path == '/api/admin/donations':
            return self._api_admin_donations()

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
            '/api/auth/login':                self._api_login,
            '/api/auth/logout':               self._api_logout,
            '/api/auth/reset':                self._api_reset,
            '/api/auth/request-reset':        self._api_request_reset,
            '/api/auth/reset-confirm':        self._api_reset_confirm,
            '/api/admin/content':             self._api_save_content,
            '/api/admin/create-user':         self._api_create_user,
            '/api/admin/delete-user':         self._api_delete_user,
            '/api/admin/set-password':        self._api_set_password,
            '/api/admin/toggle-admin':        self._api_toggle_admin,
            '/api/admin/smtp-config':         self._api_save_smtp,
            '/api/admin/smtp-test':           self._api_test_smtp,
            '/api/admin/testimony/approve':   self._api_approve_testimony,
            '/api/admin/testimony/reject':    self._api_reject_testimony,
            '/api/admin/prayer/approve':      self._api_approve_prayer,
            '/api/admin/prayer/reject':       self._api_reject_prayer,
            '/api/testimony':                 self._api_submit_testimony,
            '/api/prayer':                    self._api_submit_prayer,
            '/api/donate/record':             self._api_donate_record,
            '/api/paypal/ipn':                self._api_paypal_ipn,
            '/api/info-request':              self._api_info_request,
            '/api/contact':                   self._api_contact,
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

    # ── Content endpoints ─────────────────────────────────────────────────────

    def _api_get_content(self):
        self._json(_load_content())

    def _api_save_content(self):
        if not self._require_admin():
            return
        b = self._body()
        content = _load_content()
        # Merge settings sub-object cleanly
        if 'settings' in b and isinstance(b['settings'], dict):
            content.setdefault('settings', {}).update(b['settings'])
            del b['settings']
        content.update(b)
        _save_json(CONTENT_FILE, content)
        self._json({'ok': True})

    # ── Testimony / Prayer submissions (public) ───────────────────────────────

    def _api_submit_testimony(self):
        b = self._body()
        name  = b.get('name', '').strip() or 'Anonymous'
        email = b.get('email', '').strip()
        quote = b.get('quote', '').strip()
        if not quote:
            return self._err('Testimony text required')
        entry = {
            'id':        secrets.token_hex(6),
            'timestamp': int(time.time()),
            'name':      name,
            'email':     email,
            'quote':     quote,
        }
        pending = _load_pending()
        pending['testimonies'].insert(0, entry)
        _save_pending(pending)
        _push(f'New Testimony — {name}', quote[:200], tags='scroll')
        try:
            cfg    = _load_smtp()
            notify = _notify_email()
            if notify:
                _send_email(cfg, notify, f'New Testimony Submission — {name}',
                    f'Name:  {name}\nEmail: {email or "(not provided)"}\n\nTestimony:\n{quote}')
        except Exception:
            pass
        self._json({'ok': True})

    def _api_submit_prayer(self):
        b = self._body()
        name   = b.get('name', '').strip() or 'Anonymous'
        email  = b.get('email', '').strip()
        text   = b.get('text', '').strip()
        urgent = bool(b.get('urgent', False))
        if not text:
            return self._err('Prayer request text required')
        entry = {
            'id':        secrets.token_hex(6),
            'timestamp': int(time.time()),
            'name':      name,
            'email':     email,
            'text':      text,
            'urgent':    urgent,
        }
        pending = _load_pending()
        pending['prayers'].insert(0, entry)
        _save_pending(pending)
        urgency = 'urgent' if urgent else 'pray'
        _push(f'{"URGENT " if urgent else ""}Prayer Request — {name}', text[:200], tags=urgency)
        try:
            cfg    = _load_smtp()
            notify = _notify_email()
            if notify:
                _send_email(cfg, notify, f'New Prayer Request — {name}',
                    f'Name:   {name}\nUrgent: {"YES" if urgent else "No"}\nEmail:  {email or "(not provided)"}\n\nRequest:\n{text}')
        except Exception:
            pass
        self._json({'ok': True})

    # ── Pending approval (admin) ──────────────────────────────────────────────

    def _api_admin_pending(self):
        if not self._require_admin():
            return
        self._json(_load_pending())

    def _api_approve_testimony(self):
        if not self._require_admin():
            return
        tid     = self._body().get('id', '')
        pending = _load_pending()
        entry   = next((e for e in pending['testimonies'] if e['id'] == tid), None)
        if not entry:
            return self._err('Not found', 404)
        pending['testimonies'] = [e for e in pending['testimonies'] if e['id'] != tid]
        _save_pending(pending)
        content = _load_content()
        content.setdefault('testimonies', []).insert(0, {
            'quote':  entry['quote'],
            'author': f'— {entry["name"]}',
        })
        _save_json(CONTENT_FILE, content)
        self._json({'ok': True})

    def _api_reject_testimony(self):
        if not self._require_admin():
            return
        tid     = self._body().get('id', '')
        pending = _load_pending()
        pending['testimonies'] = [e for e in pending['testimonies'] if e['id'] != tid]
        _save_pending(pending)
        self._json({'ok': True})

    def _api_approve_prayer(self):
        if not self._require_admin():
            return
        pid     = self._body().get('id', '')
        pending = _load_pending()
        entry   = next((e for e in pending['prayers'] if e['id'] == pid), None)
        if not entry:
            return self._err('Not found', 404)
        pending['prayers'] = [e for e in pending['prayers'] if e['id'] != pid]
        _save_pending(pending)
        content  = _load_content()
        date_str = time.strftime('%b %d, %Y', time.localtime(entry['timestamp']))
        content.setdefault('prayers', []).insert(0, {
            'text':   entry['text'],
            'meta':   f'Submitted by {entry["name"]} · {date_str}',
            'urgent': entry.get('urgent', False),
        })
        _save_json(CONTENT_FILE, content)
        self._json({'ok': True})

    def _api_reject_prayer(self):
        if not self._require_admin():
            return
        pid     = self._body().get('id', '')
        pending = _load_pending()
        pending['prayers'] = [e for e in pending['prayers'] if e['id'] != pid]
        _save_pending(pending)
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

    def _api_admin_contacts(self):
        if not self._require_admin():
            return
        self._json(_load_contacts())

    # ── SMTP config ───────────────────────────────────────────────────────────

    def _api_get_smtp(self):
        if not self._require_admin():
            return
        cfg = _load_smtp()
        safe = {k: v for k, v in cfg.items() if k not in ('password', 'brevo_api_key')}
        safe['has_password'] = bool(cfg.get('password'))
        safe['has_brevo_key'] = bool(cfg.get('brevo_api_key'))
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
        if b.get('brevo_api_key'):
            cfg['brevo_api_key'] = b['brevo_api_key']
        _save_smtp(cfg)
        self._json({'ok': True})

    def _api_test_smtp(self):
        admin = self._require_admin()
        if not admin:
            return
        cfg     = _load_smtp()
        to_addr = _notify_email()
        if not to_addr:
            return self._err('No notification email configured — set it in Settings first')
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
            return self._json({'ok': True})
        cfg   = _load_smtp()
        token = secrets.token_urlsafe(32)
        with RESET_TOKENS_LOCK:
            RESET_TOKENS[token] = {'username': found_key, 'expires': time.time() + 3600}
        host  = self.headers.get('Host', 'actionoutreachministry.com')
        proto = 'https' if self.headers.get('X-Forwarded-Proto') == 'https' else 'http'
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

    # ── Contact / Info Request ────────────────────────────────────────────────

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
        contacts = _load_contacts()
        contacts.insert(0, entry)
        _save_contacts(contacts)
        sep = '=' * 50
        body_text = (
            f'New Contact Message — Action Outreach Ministry\n{sep}\n\n'
            f'From:    {name} <{email}>\nSubject: {subject}\n\n'
            f'Message:\n{message}\n\n'
            f'Sent: {time.strftime("%B %d, %Y at %I:%M %p", time.localtime())}\n'
        )
        _push(f'Contact: {subject}', f'From {name} <{email}>\n{message[:150]}', tags='email')
        try:
            notify = _notify_email()
            if notify:
                _send_email(_load_smtp(), notify, f'Contact: {subject} — from {name}', body_text)
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
        interest_lines = '\n  '.join(interests) if interests else '(none specified)'
        sep = '=' * 50
        body_text = (
            f'New Information Request — Action Outreach Ministry\n{sep}\n\n'
            f'Name:    {entry["name"]}\nAddress: {entry["address"]}\n'
            f'Email:   {email or "(not provided)"}\nPhone:   {phone or "(not provided)"}\n\n'
            f'Information Requested:\n  {interest_lines}\n\n'
            f'Comments:\n  {comments or "(none)"}\n\n'
            f'Submitted: {time.strftime("%B %d, %Y at %I:%M %p", time.localtime())}\n'
        )
        _push(f'Info Request — {entry["name"]}', f'{entry["address"]}\n{", ".join(interests) if interests else "General info"}', tags='mailbox')
        try:
            notify = _notify_email()
            if notify:
                _send_email(_load_smtp(), notify,
                    f'Info Request: {entry["name"]} — Action Outreach Ministry', body_text)
        except Exception:
            pass
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

    def _api_admin_donations(self):
        if not self._require_admin():
            return
        self._json(_load_donations())

    def _api_paypal_ipn(self):
        # Read raw IPN body
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)

        # Send verification back to PayPal
        verify_url = 'https://ipnpb.paypal.com/cgi-bin/webscr'
        verify_body = b'cmd=_notify-validate&' + raw
        try:
            req = urllib.request.Request(
                verify_url,
                data=verify_body,
                headers={'Content-Type': 'application/x-www-form-urlencoded',
                         'User-Agent': 'AOM-IPN/1.0'}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read().decode()
        except Exception:
            self.send_response(200)
            self.end_headers()
            return

        if result != 'VERIFIED':
            self.send_response(200)
            self.end_headers()
            return

        # Parse IPN fields
        from urllib.parse import parse_qs
        fields = {k: v[0] for k, v in parse_qs(raw.decode()).items()}

        payment_status = fields.get('payment_status', '')
        txn_type       = fields.get('txn_type', '')
        # Accept completed one-time and subscription payments
        valid_types    = {'web_accept', 'subscr_payment', 'express_checkout', 'cart', ''}
        if payment_status != 'Completed' or txn_type not in valid_types:
            self.send_response(200)
            self.end_headers()
            return

        amount      = float(fields.get('mc_gross', 0))
        currency    = fields.get('mc_currency', 'USD')
        donor_name  = fields.get('first_name', '') + ' ' + fields.get('last_name', '')
        donor_email = fields.get('payer_email', '')
        txn_id      = fields.get('txn_id', secrets.token_hex(8))
        item_name   = fields.get('item_name', 'General Fund')
        freq        = 'monthly' if txn_type == 'subscr_payment' else 'once'

        donation = {
            'id':          txn_id,
            'amount':      amount,
            'currency':    currency,
            'donor_name':  donor_name.strip(),
            'donor_email': donor_email,
            'fund':        item_name,
            'freq':        freq,
            'timestamp':   int(time.time()),
            'source':      'paypal_ipn',
        }
        donations = _load_donations()
        # Deduplicate by txn_id
        if not any(d.get('id') == txn_id for d in donations):
            donations.append(donation)
            _save_donations(donations)
            freq_label = ' (monthly)' if freq == 'monthly' else ''
            msg = f'${amount:.2f}{freq_label} from {donor_name.strip() or donor_email} — {item_name}'
            _push('💰 New Donation!', msg, ['money_with_wings'])
            _send_email(
                _load_smtp(),
                _notify_email(),
                'New Donation — Action Outreach Ministry',
                f'A donation was confirmed by PayPal.\n\n'
                f'Amount: ${amount:.2f} {currency}{freq_label}\n'
                f'Donor: {donor_name.strip() or "Anonymous"}\n'
                f'Email: {donor_email or "not provided"}\n'
                f'Fund: {item_name}\n'
                f'PayPal Txn: {txn_id}\n'
            )

        self.send_response(200)
        self.end_headers()


# ── Boot ──────────────────────────────────────────────────────────────────────

_load_sessions()
_seed_admin()
_seed_content()

if __name__ == '__main__':
    server = ThreadedHTTPServer(('0.0.0.0', PORT), AOMHandler)
    print(f'Action Outreach Ministry server → http://0.0.0.0:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
