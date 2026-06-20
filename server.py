#!/usr/bin/env python3
"""Action Outreach Ministry — standalone web server. No pip dependencies."""

import cgi, hashlib, hmac, json, os, re, secrets, smtplib, socket, threading, time
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
INCOME_FILE        = BASE_DIR / 'ministry_income.json'      # manually-recorded deposits (CashApp/Venmo/Zelle/cash/check)
EXPENSES_FILE      = BASE_DIR / 'ministry_expenses.json'    # overhead / expenses paid out
PAYPAL_FILE        = BASE_DIR / 'paypal_config.json'        # PayPal REST creds for Webhooks (replaces deprecated IPN)
SMTP_FILE          = BASE_DIR / 'smtp_config.json'
INFO_REQUESTS_FILE = BASE_DIR / 'info_requests.json'
CONTENT_FILE       = BASE_DIR / 'ministry_content.json'
PENDING_FILE       = BASE_DIR / 'ministry_pending.json'
CONTACTS_FILE      = BASE_DIR / 'contacts.json'
UPLOADS_DIR        = BASE_DIR / 'uploads'

ALLOWED_UPLOAD_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.mp3', '.pdf', '.doc', '.docx'}
MAX_UPLOAD_BYTES    = 20 * 1024 * 1024   # 20 MB

# Emergency admin reset code — read from env, NOT hardcoded. Unset ⇒ the /api/auth/reset
# endpoint is disabled (no source-code backdoor). Set AOM_RECOVERY_CODE only when needed.
ADMIN_RECOVERY_CODE = os.environ.get('AOM_RECOVERY_CODE', '')

SESSION_TTL       = 7 * 24 * 3600    # server-side session lifetime (seconds)
PBKDF2_ITERATIONS = 200_000          # password KDF work factor

LOGIN_FAILS       = {}               # ip -> [timestamps] of recent failed logins
LOGIN_FAILS_LOCK  = threading.Lock()
LOGIN_MAX_FAILS   = 8                 # lock the IP after this many failures…
LOGIN_WINDOW      = 900               # …within this many seconds (15 min)

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
    '.gif':  'image/gif',
    '.ico':  'image/x-icon',
    '.svg':  'image/svg+xml',
    '.txt':  'text/plain',
    '.mp3':  'audio/mpeg',
    '.pdf':  'application/pdf',
    '.doc':  'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

def _safe_filename(name):
    name = Path(name).name
    name = re.sub(r'[^\w.\-]', '_', name)
    return name[:120] or 'upload'

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
def _load_income():             return _load_json(INCOME_FILE, [])
def _save_income(i):            _save_json(INCOME_FILE, i)
def _load_expenses():           return _load_json(EXPENSES_FILE, [])
def _save_expenses(e):          _save_json(EXPENSES_FILE, e)
def _load_paypal():             return _load_json(PAYPAL_FILE, {})
def _save_paypal(c):            _save_json(PAYPAL_FILE, c)
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

def _send_email_gmail_api(smtp_cfg, to_addr, subject, body_text, reply_to=''):
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
    if reply_to:
        msg['Reply-To'] = reply_to
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

def _send_email(smtp_cfg, to_addr, subject, body_text, reply_to=''):
    if smtp_cfg.get('gmail_refresh_token'):
        _send_email_gmail_api(smtp_cfg, to_addr, subject, body_text, reply_to)
        return
    from_name  = smtp_cfg.get('from_name', 'Action Outreach Ministry')
    from_email = smtp_cfg.get('username', '')
    brevo_key  = smtp_cfg.get('brevo_api_key', '')
    if brevo_key:
        msg_obj = {
            'sender': {'name': from_name, 'email': from_email or 'actionoutreachministry@gmail.com'},
            'to': [{'email': to_addr}],
            'subject': subject,
            'textContent': body_text,
        }
        if reply_to:
            msg_obj['replyTo'] = {'email': reply_to}
        payload = json.dumps(msg_obj).encode()
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
    from email.header import Header
    from email.utils import formataddr
    msg = MIMEMultipart()
    msg['From']    = formataddr((str(Header(from_name, 'utf-8')), user))
    msg['To']      = to_addr
    msg['Subject'] = str(Header(subject, 'utf-8'))
    if reply_to:
        msg['Reply-To'] = reply_to
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
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


def _notify_admin(subject, body_text, reply_to='', push_title='', push_body='', tags='bell'):
    """Single intake forwarder used by every website form.

    The submission is already saved to its folder/JSON by the caller (the durable
    record). This pings a push alert and forwards a copy to the ONE inbox
    (Settings > Notification Email), with Reply-To set to the submitter so a reply
    from that inbox goes straight back to the person who reached out.
    """
    if push_title:
        try:
            _push(push_title, push_body or body_text[:200], tags=tags)
        except Exception:
            pass
    try:
        to = _notify_email()
        if to:
            _send_email(_load_smtp(), to, subject, body_text, reply_to=reply_to)
    except Exception:
        pass


# Free SMS via carrier email-to-SMS gateways (no paid provider; reuses the working email system).
# Best-effort: requires the recipient's carrier, and carriers are slowly deprecating these.
SMS_GATEWAYS = {
    'verizon':    'vtext.com',
    'att':        'txt.att.net',
    'tmobile':    'tmomail.net',
    'sprint':     'messaging.sprintpcs.com',
    'boost':      'sms.myboostmobile.com',
    'cricket':    'sms.cricketwireless.net',
    'uscellular': 'email.uscc.net',
    'metro':      'mymetropcs.com',
    'googlefi':   'msg.fi.google.com',
    'xfinity':    'vtext.com',
}


def _send_reset_sms(smtp_cfg, phone, carrier, token, base_url):
    gateway = SMS_GATEWAYS.get((carrier or '').lower())
    if not gateway:
        raise ValueError('Unsupported carrier')
    digits = re.sub(r'\D', '', phone or '')
    if len(digits) < 10:
        raise ValueError('Invalid phone number')
    to_addr = f'{digits[-10:]}@{gateway}'
    body = f'AOM password reset (expires 1hr): {base_url}?reset_token={token}'
    _send_email(smtp_cfg, to_addr, 'Password Reset', body)


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
    """PBKDF2-HMAC-SHA256. The hash string self-describes its algo/iterations so verify can tell
    new hashes from legacy ones and migrate transparently."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return salt, f'pbkdf2_sha256${PBKDF2_ITERATIONS}${dk.hex()}'

def _verify_pw(password, salt, stored):
    if stored.startswith('pbkdf2_sha256$'):
        try:
            _, iters, hexhash = stored.split('$', 2)
            dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iters))
            return hmac.compare_digest(dk.hex(), hexhash)
        except Exception:
            return False
    # legacy single-round SHA-256 — still verifiable, auto-upgraded to PBKDF2 on next login
    legacy = hashlib.sha256((salt + password).encode()).hexdigest()
    return hmac.compare_digest(legacy, stored)

def _needs_rehash(stored):
    """True for legacy hashes that should be upgraded to PBKDF2."""
    return not stored.startswith('pbkdf2_sha256$')

# ── Roles & permissions (RBAC) ──────────────────────────────────────────────────
ROLES = ['owner', 'admin', 'editor', 'moderator', 'viewer']
ROLE_LABELS = {'owner': 'Owner', 'admin': 'Admin', 'editor': 'Editor',
               'moderator': 'Moderator', 'viewer': 'Viewer'}
ROLE_DESC = {
    'owner':     'Full control, including users, settings & finances. Cannot be removed by others.',
    'admin':     'Manage everything except owner accounts.',
    'editor':    'Edit site content (cards, events, newsletter). No users, settings, or finances.',
    'moderator': 'Approve/reject testimonies & prayers; view submissions.',
    'viewer':    'Read-only access to submissions and donation totals.',
}
_ALL = {'panel_access','manage_users','manage_settings','edit_content','moderate',
        'view_submissions','manage_finances','view_donations'}
ROLE_PERMS = {
    'owner':     set(_ALL),
    'admin':     set(_ALL),
    'editor':    {'panel_access','edit_content','view_submissions'},
    'moderator': {'panel_access','moderate','view_submissions','view_donations'},
    'viewer':    {'panel_access','view_submissions','view_donations'},
}

EXPENSE_CATEGORIES = ['Facilities/Rent', 'Utilities', 'Salaries/Stipends', 'Outreach', 'Missions',
                      'Events', 'Supplies', 'Office/Admin', 'Insurance', 'Benevolence', 'Other']
INCOME_SOURCES     = ['cashapp', 'venmo', 'zelle', 'cash', 'check', 'paypal', 'other']

def _role_of(u):
    r = (u or {}).get('role')
    return r if r in ROLE_PERMS else ('owner' if (u or {}).get('is_admin') else 'editor')

def _perms_of(u):
    return ROLE_PERMS.get(_role_of(u), set())

def _ensure_roles():
    """One-time migration: give every user an explicit role; guarantee at least one owner."""
    users = _load_users()
    if not users:
        return
    changed = False
    for u in users.values():
        if u.get('role') not in ROLE_PERMS:
            u['role'] = 'owner' if u.get('is_admin') else 'editor'; changed = True
        admin_flag = u['role'] in ('owner', 'admin')
        if u.get('is_admin') != admin_flag:
            u['is_admin'] = admin_flag; changed = True
    if not any(_role_of(u) == 'owner' for u in users.values()):
        first = min(users.items(), key=lambda kv: kv[1].get('created', 0))[0]
        users[first]['role'] = 'owner'; users[first]['is_admin'] = True; changed = True
    if changed:
        _save_users(users)

# ── PayPal Webhooks (replaces deprecated IPN) ───────────────────────────────────
def _paypal_api_base(cfg):
    return 'https://api-m.paypal.com' if cfg.get('mode', 'live') == 'live' else 'https://api-m.sandbox.paypal.com'

def _paypal_token(cfg):
    import base64
    cid, sec = cfg.get('client_id', ''), cfg.get('client_secret', '')
    if not cid or not sec:
        return None
    auth = base64.b64encode(f'{cid}:{sec}'.encode()).decode()
    req = urllib.request.Request(
        _paypal_api_base(cfg) + '/v1/oauth2/token', data=b'grant_type=client_credentials',
        headers={'Authorization': 'Basic ' + auth, 'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get('access_token')

def _paypal_api(cfg, method, endpoint, payload=None):
    """Authenticated PayPal REST call. Returns (parsed_json_or_None, error_or_None)."""
    token = _paypal_token(cfg)
    if not token:
        return None, 'no_token'
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        _paypal_api_base(cfg) + endpoint, data=data, method=method,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r), None
    except Exception as e:
        body = None
        if hasattr(e, 'read'):
            try:
                body = json.loads(e.read().decode())
            except Exception:
                body = None
        return body, 'http_error'


def _paypal_verify_webhook(cfg, headers, raw_event):
    """Verify a webhook via PayPal's verify-webhook-signature REST API. Returns True only on SUCCESS."""
    token = _paypal_token(cfg)
    if not token or not cfg.get('webhook_id'):
        return False
    payload = {
        'auth_algo':         headers.get('Paypal-Auth-Algo', ''),
        'cert_url':          headers.get('Paypal-Cert-Url', ''),
        'transmission_id':   headers.get('Paypal-Transmission-Id', ''),
        'transmission_sig':  headers.get('Paypal-Transmission-Sig', ''),
        'transmission_time': headers.get('Paypal-Transmission-Time', ''),
        'webhook_id':        cfg.get('webhook_id'),
        'webhook_event':     json.loads(raw_event),
    }
    req = urllib.request.Request(
        _paypal_api_base(cfg) + '/v1/notifications/verify-webhook-signature',
        data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get('verification_status') == 'SUCCESS'

def _record_donation(donation):
    """Dedupe (by id) + save a confirmed donation, then notify. Shared by IPN and Webhook paths."""
    donations = _load_donations()
    if any(d.get('id') == donation['id'] for d in donations):
        return False
    donations.append(donation)
    _save_donations(donations)
    amount = float(donation.get('amount', 0) or 0)
    name   = donation.get('donor_name') or donation.get('donor_email') or 'Anonymous'
    flabel = ' (monthly)' if donation.get('freq') == 'monthly' else ''
    _push('💰 New Donation!', f'${amount:.2f}{flabel} from {name} — {donation.get("fund", "General")}', ['money_with_wings'])
    try:
        _send_email(_load_smtp(), _notify_email(), 'New Donation — Action Outreach Ministry',
                    f'A donation was confirmed by PayPal.\n\n'
                    f'Amount: ${amount:.2f} {donation.get("currency", "USD")}{flabel}\n'
                    f'Donor: {donation.get("donor_name") or "Anonymous"}\n'
                    f'Email: {donation.get("donor_email") or "not provided"}\n'
                    f'Fund: {donation.get("fund", "General")}')
    except Exception:
        pass
    # Donor tax-receipt / thank-you — only when PayPal gave us the donor's email.
    try:
        _send_donor_receipt(donation)
    except Exception:
        pass


_FUND_LABELS = {'general': 'General Fund', 'missions': 'Global Missions',
                'food': 'Community Feeding Program', 'bibles': 'Bible Distribution',
                'youth': 'Youth Ministry'}


def _send_donor_receipt(donation):
    """Email the donor a thank-you + tax receipt (no-op if no donor email was provided)."""
    email = (donation.get('donor_email') or '').strip()
    if not email:
        return
    settings = _load_content().get('settings', {}) or {}
    ministry = settings.get('ministryName') or 'Action Outreach Ministry'
    ein      = settings.get('ein') or settings.get('taxId') or ''
    amount   = float(donation.get('amount', 0) or 0)
    fund     = donation.get('fund', 'General Fund')
    fund     = _FUND_LABELS.get(fund, fund)
    monthly  = donation.get('freq') == 'monthly'
    when     = time.strftime('%B %d, %Y', time.localtime(donation.get('timestamp') or time.time()))
    donor    = donation.get('donor_name') or 'Friend'
    lines = [
        f'Dear {donor},', '',
        f'Thank you for your generous {"recurring " if monthly else ""}gift to {ministry}. '
        'Your support directly fuels our mission and the work of the Gospel.', '',
        f'  Amount:     ${amount:.2f} {donation.get("currency", "USD")}{" / month" if monthly else ""}',
        f'  Designation: {fund}',
        f'  Date:       {when}',
        f'  Receipt #:  {donation.get("id", "")}', '',
        f'{ministry} is a nonprofit organization. This letter may serve as your receipt for tax '
        'purposes. No goods or services were provided in exchange for this contribution.',
    ]
    if ein:
        lines.append(f'Tax ID (EIN): {ein}')
    lines += ['', 'With gratitude,', ministry]
    _send_email(_load_smtp(), email, f'Your gift to {ministry} — thank you!', '\n'.join(lines))
    return True

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
                sess = SESSIONS.get(token)
                if not sess:
                    return None
                # server-side expiry: a leaked token can't live forever
                if int(time.time()) - sess.get('created', 0) > SESSION_TTL:
                    SESSIONS.pop(token, None)
                    return None
                return sess
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
    """Seed the first owner ONLY if no users exist. Password comes from AOM_INITIAL_PASSWORD, or a
    random one printed to the log — never a known default baked into source."""
    users = _load_users()
    if not users:
        pw = os.environ.get('AOM_INITIAL_PASSWORD') or secrets.token_urlsafe(12)
        salt, h = _hash_pw(pw)
        users['admin'] = {
            'salt': salt, 'hash': h, 'role': 'owner', 'is_admin': True,
            'contact_email': '', 'contact_phone': '', 'carrier': '', 'created': int(time.time())
        }
        _save_users(users)
        print(f'[AOM] Seeded initial owner → username: admin  password: {pw}  (change it immediately)')

# ── Handler ───────────────────────────────────────────────────────────────────

class AOMHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def handle_error(self, request, client_address):
        pass

    # ── Low-level response helpers ────────────────────────────────────────────

    def _cors(self):
        origin = self.headers.get('Origin', '')
        allowed = origin if origin in ('https://actionoutreachministry.com',
                                       'http://localhost:8000', 'http://127.0.0.1:8000') else ''
        self.send_header('Access-Control-Allow-Origin', allowed or 'https://actionoutreachministry.com')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _security_headers(self):
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy',
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.paypal.com https://www.paypalobjects.com; "
            "frame-src https://www.paypal.com; "
            "img-src 'self' data: https://api.qrserver.com https://www.paypalobjects.com; "
            "connect-src 'self' https://www.paypal.com; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:;")

    def _json(self, data, status=200, cookie=None):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        self._security_headers()
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

    # ── Login rate-limiting (brute-force protection) ──────────────────────────
    def _client_ip(self):
        # Only trust X-Forwarded-For from the local nginx proxy
        peer = self.client_address[0]
        if peer in ('127.0.0.1', '::1'):
            xff = self.headers.get('X-Forwarded-For', '')
            if xff:
                return xff.split(',')[0].strip()
        return peer

    def _login_locked(self, ip):
        now = time.time()
        with LOGIN_FAILS_LOCK:
            fails = [t for t in LOGIN_FAILS.get(ip, []) if now - t < LOGIN_WINDOW]
            LOGIN_FAILS[ip] = fails
            return len(fails) >= LOGIN_MAX_FAILS

    def _login_fail(self, ip):
        with LOGIN_FAILS_LOCK:
            LOGIN_FAILS.setdefault(ip, []).append(time.time())

    def _login_ok(self, ip):
        with LOGIN_FAILS_LOCK:
            LOGIN_FAILS.pop(ip, None)

    def _require_perm(self, perm):
        """Gate an endpoint on a specific capability. Returns the acting username or None."""
        sess = _get_session(self)
        if not sess:
            self._err('Not authenticated', 401)
            return None
        u = _load_users().get(sess['username'])
        if not u or perm not in _perms_of(u):
            self._err('Permission denied', 403)
            return None
        return sess['username']

    def _require_admin(self):
        """Any role with admin-panel access (views). Writes use _require_perm with a finer perm."""
        return self._require_perm('panel_access')

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
        if path == '/api/admin/income':
            return self._api_admin_income()
        if path == '/api/admin/expenses':
            return self._api_admin_expenses()
        if path == '/api/admin/finance-summary':
            return self._api_finance_summary()
        if path == '/api/admin/paypal-config':
            return self._api_get_paypal_config()
        if path == '/api/paypal/public':
            return self._api_paypal_public()
        if path in ('/give', '/donate'):
            self.send_response(302)
            self.send_header('Location', '/#donate')
            self.end_headers()
            return

        # Static file
        file_path = (BASE_DIR / path.lstrip('/')).resolve()
        # Prevent path traversal outside BASE_DIR
        try:
            file_path.relative_to(BASE_DIR.resolve())
        except ValueError:
            file_path = BASE_DIR / 'index.html'
        if file_path.is_dir():
            file_path = file_path / 'index.html'
        if not file_path.exists() or not file_path.is_file():
            file_path = BASE_DIR / 'index.html'

        data = file_path.read_bytes()
        mime = MIME_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self._security_headers()
        # No caching for HTML/JS/CSS — always serve fresh
        if file_path.suffix.lower() in ('.html', '.js', '.css'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
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
            '/api/auth/change-password':      self._api_change_password,
            '/api/auth/update-contact':       self._api_update_contact,
            '/api/admin/content':             self._api_save_content,
            '/api/admin/upload-card-file':       self._api_upload_card_file,
            '/api/admin/delete-card-file':       self._api_delete_card_file,
            '/api/admin/upload-newsletter-file': self._api_upload_newsletter_file,
            '/api/admin/delete-newsletter-file': self._api_delete_newsletter_file,
            '/api/admin/create-user':         self._api_create_user,
            '/api/admin/delete-user':         self._api_delete_user,
            '/api/admin/set-password':        self._api_set_password,
            '/api/admin/set-role':            self._api_set_role,
            '/api/admin/income/add':          self._api_income_add,
            '/api/admin/income/delete':       self._api_income_delete,
            '/api/admin/expense/add':         self._api_expense_add,
            '/api/admin/expense/delete':      self._api_expense_delete,
            '/api/admin/smtp-config':         self._api_save_smtp,
            '/api/admin/smtp-test':           self._api_test_smtp,
            '/api/admin/testimony/approve':   self._api_approve_testimony,
            '/api/admin/testimony/reject':    self._api_reject_testimony,
            '/api/admin/prayer/approve':      self._api_approve_prayer,
            '/api/admin/prayer/reject':       self._api_reject_prayer,
            '/api/testimony':                 self._api_submit_testimony,
            '/api/prayer':                    self._api_submit_prayer,
            '/api/donate/record':             self._api_donate_record,
            '/api/paypal/create-order':       self._api_paypal_create_order,
            '/api/paypal/capture-order':      self._api_paypal_capture_order,
            '/api/paypal/ipn':                self._api_paypal_ipn,
            '/api/paypal/webhook':            self._api_paypal_webhook,
            '/api/admin/paypal-config':       self._api_save_paypal_config,
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
            'role': _role_of(u),
            'perms': sorted(_perms_of(u)),
            'contact_email': u.get('contact_email', ''),
            'contact_phone': u.get('contact_phone', ''),
            'carrier': u.get('carrier', '')
        })

    def _api_login(self):
        ip = self._client_ip()
        if self._login_locked(ip):
            return self._err('Too many failed attempts — try again in 15 minutes', 429)
        b = self._body()
        username = b.get('username', '').strip()
        password = b.get('password', '')
        if not username or not password:
            return self._err('Username and password required')
        users = _load_users()
        key = next((k for k in users if k.lower() == username.lower()), None)
        if not key or not _verify_pw(password, users[key]['salt'], users[key]['hash']):
            self._login_fail(ip)
            return self._err('Invalid credentials', 401)
        self._login_ok(ip)
        # transparent migration: upgrade legacy SHA-256 hashes to PBKDF2 on successful login
        if _needs_rehash(users[key]['hash']):
            salt, h = _hash_pw(password)
            users[key]['salt'], users[key]['hash'] = salt, h
            _save_users(users)
        token = _create_session(key)
        secure = '; Secure' if self.headers.get('X-Forwarded-Proto') == 'https' else ''
        cookie = f'ms_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}{secure}'
        self._json({'ok': True, 'username': key, 'is_admin': users[key].get('is_admin', False)}, cookie=cookie)

    def _api_logout(self):
        _destroy_session(self)
        self._json({'ok': True}, cookie='ms_session=; Path=/; Max-Age=0')

    def _api_reset(self):
        b = self._body()
        # Disabled unless an out-of-band recovery code is set via the AOM_RECOVERY_CODE env var.
        if not ADMIN_RECOVERY_CODE or not hmac.compare_digest(b.get('recovery_code', ''), ADMIN_RECOVERY_CODE):
            return self._err('Recovery is disabled or the code is invalid', 401)
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
        if not self._require_perm('edit_content'):
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

    # ── Card file upload / delete ─────────────────────────────────────────────

    def _api_upload_card_file(self):
        if not self._require_perm('edit_content'):
            return
        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in ct:
            return self._err('Expected multipart/form-data', 400)
        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_UPLOAD_BYTES:
            return self._err('File too large (max 20 MB)', 400)
        env = {'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': ct, 'CONTENT_LENGTH': str(length)}
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=env)
        card_idx = form.getvalue('card_index', '').strip()
        if not card_idx.isdigit():
            return self._err('Invalid card_index', 400)
        if 'file' not in form:
            return self._err('No file in request', 400)
        fld = form['file']
        ext = Path(fld.filename or '').suffix.lower()
        if ext not in ALLOWED_UPLOAD_EXTS:
            return self._err('File type not allowed. Accepted: jpg, png, gif, mp3, pdf, doc, docx', 400)
        safe = _safe_filename(fld.filename)
        upload_dir = UPLOADS_DIR / 'cards' / card_idx
        upload_dir.mkdir(parents=True, exist_ok=True)
        data = fld.file.read()
        (upload_dir / safe).write_bytes(data)
        url = '/uploads/cards/{}/{}'.format(card_idx, safe)
        content = _load_content()
        cards = content.get('cards', [])
        idx = int(card_idx)
        if 0 <= idx < len(cards):
            cards[idx].setdefault('files', [])
            # replace if same name already exists
            cards[idx]['files'] = [f for f in cards[idx]['files'] if f['name'] != safe]
            cards[idx]['files'].append({'name': safe, 'url': url,
                                        'type': ext.lstrip('.'), 'size': len(data)})
            content['cards'] = cards
            _save_json(CONTENT_FILE, content)
        self._json({'ok': True, 'url': url, 'name': safe, 'type': ext.lstrip('.'), 'size': len(data)})

    def _api_upload_newsletter_file(self):
        if not self._require_perm('edit_content'):
            return
        ct = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in ct:
            return self._err('Expected multipart/form-data', 400)
        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_UPLOAD_BYTES:
            return self._err('File too large (max 20 MB)', 400)
        env = {'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': ct, 'CONTENT_LENGTH': str(length)}
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=env)
        if 'file' not in form:
            return self._err('No file in request', 400)
        fld = form['file']
        ext = Path(fld.filename or '').suffix.lower()
        if ext not in ALLOWED_UPLOAD_EXTS:
            return self._err('File type not allowed. Accepted: jpg, png, gif, mp3, pdf, doc, docx', 400)
        safe = _safe_filename(fld.filename)
        upload_dir = UPLOADS_DIR / 'newsletter'
        upload_dir.mkdir(parents=True, exist_ok=True)
        data = fld.file.read()
        (upload_dir / safe).write_bytes(data)
        url = '/uploads/newsletter/' + safe
        content = _load_content()
        nl = content.setdefault('newsletter', {})
        nl.setdefault('files', [])
        nl['files'] = [f for f in nl['files'] if f['name'] != safe]
        nl['files'].append({'name': safe, 'url': url, 'type': ext.lstrip('.'), 'size': len(data)})
        _save_json(CONTENT_FILE, content)
        self._json({'ok': True, 'url': url, 'name': safe, 'type': ext.lstrip('.'), 'size': len(data)})

    def _api_delete_newsletter_file(self):
        if not self._require_perm('edit_content'):
            return
        b = self._body()
        filename = str(b.get('filename', '')).strip()
        if not filename:
            return self._err('Missing filename', 400)
        safe = _safe_filename(filename)
        if safe != filename:
            return self._err('Invalid filename', 400)
        fp = UPLOADS_DIR / 'newsletter' / safe
        if fp.exists() and fp.is_file():
            fp.unlink()
        content = _load_content()
        nl = content.setdefault('newsletter', {})
        nl['files'] = [f for f in nl.get('files', []) if f['name'] != safe]
        _save_json(CONTENT_FILE, content)
        self._json({'ok': True})

    def _api_delete_card_file(self):
        if not self._require_perm('edit_content'):
            return
        b = self._body()
        card_idx = str(b.get('card_index', '')).strip()
        filename = str(b.get('filename', '')).strip()
        if not card_idx.isdigit() or not filename:
            return self._err('Invalid parameters', 400)
        safe = _safe_filename(filename)
        if safe != filename:
            return self._err('Invalid filename', 400)
        fp = UPLOADS_DIR / 'cards' / card_idx / safe
        if fp.exists() and fp.is_file():
            fp.unlink()
        content = _load_content()
        cards = content.get('cards', [])
        idx = int(card_idx)
        if 0 <= idx < len(cards):
            cards[idx]['files'] = [f for f in cards[idx].get('files', []) if f['name'] != safe]
            content['cards'] = cards
            _save_json(CONTENT_FILE, content)
        self._json({'ok': True})

    # ── Testimony / Prayer submissions (public) ───────────────────────────────

    def _api_submit_testimony(self):
        b = self._body()
        name  = b.get('name', '').strip()[:100] or 'Anonymous'
        email = b.get('email', '').strip()[:200]
        quote = b.get('quote', '').strip()[:5000]
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
        host  = self.headers.get('Host', 'actionoutreachministry.com')
        proto = 'https' if self.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        review_link = f'{proto}://{host}/#rt-{entry["id"]}'
        _notify_admin(
            f'New Testimony Submission — {name}',
            f'Name:  {name}\nEmail: {email or "(not provided)"}\n\nTestimony:\n{quote}\n\n'
            f'──────────────────────────────\n'
            f'Review, edit & publish this testimony (opens the admin tools):\n{review_link}\n',
            reply_to=email,
            push_title=f'New Testimony — {name}', push_body=quote[:200], tags='scroll')
        self._json({'ok': True})

    def _api_submit_prayer(self):
        b = self._body()
        name   = b.get('name', '').strip()[:100] or 'Anonymous'
        email  = b.get('email', '').strip()[:200]
        text   = b.get('text', '').strip()[:2000]
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
        _notify_admin(
            f'New Prayer Request — {name}',
            f'Name:   {name}\nUrgent: {"YES" if urgent else "No"}\nEmail:  {email or "(not provided)"}\n\nRequest:\n{text}',
            reply_to=email,
            push_title=f'{"URGENT " if urgent else ""}Prayer Request — {name}',
            push_body=text[:200], tags=urgency)
        self._json({'ok': True})

    # ── Pending approval (admin) ──────────────────────────────────────────────

    def _api_admin_pending(self):
        if not self._require_perm('moderate'):
            return
        self._json(_load_pending())

    def _api_approve_testimony(self):
        if not self._require_perm('moderate'):
            return
        b       = self._body()
        tid     = b.get('id', '')
        pending = _load_pending()
        entry   = next((e for e in pending['testimonies'] if e['id'] == tid), None)
        if not entry:
            return self._err('Not found', 404)
        # The admin may EDIT the name/quote before publishing — use the edited values if sent.
        name  = str(b.get('name',  entry.get('name', ''))).strip() or 'Anonymous'
        quote = str(b.get('quote', entry.get('quote', ''))).strip()
        if not quote:
            return self._err('Testimony text cannot be empty')
        pending['testimonies'] = [e for e in pending['testimonies'] if e['id'] != tid]
        _save_pending(pending)
        content = _load_content()
        content.setdefault('testimonies', []).insert(0, {
            'quote':  quote,
            'author': f'— {name}',
        })
        _save_json(CONTENT_FILE, content)
        self._json({'ok': True})

    def _api_reject_testimony(self):
        if not self._require_perm('moderate'):
            return
        tid     = self._body().get('id', '')
        pending = _load_pending()
        pending['testimonies'] = [e for e in pending['testimonies'] if e['id'] != tid]
        _save_pending(pending)
        self._json({'ok': True})

    def _api_approve_prayer(self):
        if not self._require_perm('moderate'):
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
        if not self._require_perm('moderate'):
            return
        pid     = self._body().get('id', '')
        pending = _load_pending()
        pending['prayers'] = [e for e in pending['prayers'] if e['id'] != pid]
        _save_pending(pending)
        self._json({'ok': True})

    # ── Admin endpoints ───────────────────────────────────────────────────────

    def _api_admin_users(self):
        if not self._require_perm('manage_users'):
            return
        users = _load_users()
        self._json([
            {'username': k, 'is_admin': v.get('is_admin', False), 'role': _role_of(v),
             'contact_email': v.get('contact_email', ''),
             'contact_phone': v.get('contact_phone', ''), 'created': v.get('created', 0)}
            for k, v in users.items()
        ])

    def _api_create_user(self):
        actor = self._require_perm('manage_users')
        if not actor:
            return
        b = self._body()
        username = b.get('username', '').strip()
        password = b.get('password', '')
        role     = b.get('role', 'viewer').strip()
        if role not in ROLE_PERMS:
            role = 'viewer'
        if not username or not password:
            return self._err('Username and password required')
        if len(password) < 8:
            return self._err('Password must be at least 8 characters')
        users = _load_users()
        if any(k.lower() == username.lower() for k in users):
            return self._err('Username already exists')
        if role == 'owner' and _role_of(users.get(actor, {})) != 'owner':
            return self._err('Only an owner can create owner accounts', 403)
        salt, h = _hash_pw(password)
        users[username] = {
            'salt': salt, 'hash': h, 'role': role,
            'is_admin': role in ('owner', 'admin'),
            'contact_email': b.get('contact_email', '').strip(),
            'contact_phone': b.get('contact_phone', '').strip(),
            'carrier': b.get('carrier', '').strip(),
            'created': int(time.time())
        }
        _save_users(users)
        self._json({'ok': True})

    def _api_delete_user(self):
        actor = self._require_perm('manage_users')
        if not actor:
            return
        username = self._body().get('username', '').strip()
        if username == actor:
            return self._err('Cannot delete your own account')
        users = _load_users()
        if username not in users:
            return self._err('User not found')
        if _role_of(users[username]) == 'owner':
            if _role_of(users[actor]) != 'owner':
                return self._err('Only an owner can remove an owner', 403)
            if len([k for k, u in users.items() if _role_of(u) == 'owner']) <= 1:
                return self._err('Cannot delete the last owner')
        del users[username]
        _save_users(users)
        self._json({'ok': True})

    def _api_set_password(self):
        actor = self._require_perm('manage_users')
        if not actor:
            return
        b = self._body()
        username = b.get('username', '').strip()
        password = b.get('password', '')
        if not username or not password:
            return self._err('Username and password required')
        if len(password) < 8:
            return self._err('Password must be at least 8 characters')
        users = _load_users()
        if username not in users:
            return self._err('User not found')
        if _role_of(users[username]) == 'owner' and _role_of(users[actor]) != 'owner':
            return self._err('Only an owner can reset an owner password', 403)
        salt, h = _hash_pw(password)
        users[username]['salt'] = salt
        users[username]['hash'] = h
        _save_users(users)
        self._json({'ok': True})

    def _api_set_role(self):
        actor = self._require_perm('manage_users')
        if not actor:
            return
        b = self._body()
        username = b.get('username', '').strip()
        new_role = b.get('role', '').strip()
        if new_role not in ROLE_PERMS:
            return self._err('Invalid role')
        if username == actor:
            return self._err('You cannot change your own role')
        users = _load_users()
        if username not in users:
            return self._err('User not found')
        actor_role  = _role_of(users[actor])
        target_role = _role_of(users[username])
        # Only an owner may grant owner, or modify an existing owner.
        if (new_role == 'owner' or target_role == 'owner') and actor_role != 'owner':
            return self._err('Only an owner can manage owner accounts', 403)
        # Never demote the last owner.
        if target_role == 'owner' and new_role != 'owner':
            if len([k for k, u in users.items() if _role_of(u) == 'owner']) <= 1:
                return self._err('Cannot demote the last owner')
        users[username]['role'] = new_role
        users[username]['is_admin'] = new_role in ('owner', 'admin')
        _save_users(users)
        self._json({'ok': True, 'role': new_role})

    def _api_admin_txns(self):
        if not self._require_perm('view_donations'):
            return
        self._json(_load_txns())

    def _api_admin_contacts(self):
        if not self._require_admin():
            return
        self._json(_load_contacts())

    # ── SMTP config ───────────────────────────────────────────────────────────

    def _api_get_smtp(self):
        if not self._require_perm('manage_settings'):
            return
        cfg = _load_smtp()
        safe = {k: v for k, v in cfg.items()
                if k not in ('password', 'brevo_api_key', 'gmail_client_secret', 'gmail_refresh_token')}
        safe['has_password']  = bool(cfg.get('password'))
        safe['has_brevo_key'] = bool(cfg.get('brevo_api_key'))
        # Which delivery method is actually in effect (priority: Gmail API → Brevo → SMTP)
        if cfg.get('gmail_refresh_token'):
            safe['active_method'] = 'gmail_api'
        elif cfg.get('brevo_api_key'):
            safe['active_method'] = 'brevo'
        elif cfg.get('host') and cfg.get('username') and cfg.get('password'):
            safe['active_method'] = 'smtp'
        else:
            safe['active_method'] = 'none'
        safe['notify_email'] = _notify_email()
        self._json(safe)

    def _api_save_smtp(self):
        if not self._require_perm('manage_settings'):
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
        admin = self._require_perm('manage_settings')
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
        method  = b.get('method', 'email')          # 'email' | 'sms'
        email   = b.get('email', '').strip()
        phone   = b.get('phone', '').strip()
        carrier = b.get('carrier', '').strip()
        users   = _load_users()
        if method == 'sms':
            digits = re.sub(r'\D', '', phone)
            found_key = next((k for k, u in users.items()
                              if re.sub(r'\D', '', u.get('contact_phone', '')) == digits and digits), None)
        else:
            found_key = next((k for k, u in users.items()
                              if u.get('contact_email', '').lower() == email.lower() and email), None)
        # Always return ok (don't leak which accounts exist)
        if not found_key:
            return self._json({'ok': True})
        cfg   = _load_smtp()
        token = secrets.token_urlsafe(32)
        with RESET_TOKENS_LOCK:
            RESET_TOKENS[token] = {'username': found_key, 'expires': time.time() + 3600}
        host  = self.headers.get('Host', 'actionoutreachministry.com')
        proto = 'https' if self.headers.get('X-Forwarded-Proto') == 'https' else 'http'
        base  = f'{proto}://{host}'
        try:
            if method == 'sms':
                _send_reset_sms(cfg, users[found_key].get('contact_phone', ''),
                                users[found_key].get('carrier', carrier), token, base)
            else:
                _send_reset_email(cfg, users[found_key]['contact_email'], token, base)
        except Exception as e:
            return self._err(f'Could not send reset: {e}', 500)
        self._json({'ok': True})

    def _api_change_password(self):
        """Self-service: a logged-in user changes their own password (old → new)."""
        sess = _get_session(self)
        if not sess:
            return self._err('Not authenticated', 401)
        b = self._body()
        old_pw = b.get('old_password', '')
        new_pw = b.get('new_password', '')
        if len(new_pw) < 8:
            return self._err('New password must be at least 8 characters')
        users = _load_users()
        u = users.get(sess['username'])
        if not u or not _verify_pw(old_pw, u['salt'], u['hash']):
            return self._err('Current password is incorrect', 401)
        salt, h = _hash_pw(new_pw)
        u['salt'], u['hash'] = salt, h
        _save_users(users)
        self._json({'ok': True})

    def _api_update_contact(self):
        """Self-service: a logged-in user sets their own recovery contact (email / phone / carrier)
        — required for password reset to reach them."""
        sess = _get_session(self)
        if not sess:
            return self._err('Not authenticated', 401)
        b = self._body()
        users = _load_users()
        u = users.get(sess['username'])
        if not u:
            return self._err('User not found', 404)
        u['contact_email'] = b.get('contact_email', u.get('contact_email', '')).strip()
        u['contact_phone'] = b.get('contact_phone', u.get('contact_phone', '')).strip()
        u['carrier']       = b.get('carrier', u.get('carrier', '')).strip()
        _save_users(users)
        self._json({'ok': True, 'contact_email': u['contact_email'],
                    'contact_phone': u['contact_phone'], 'carrier': u['carrier']})

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
        name    = b.get('name', '').strip()[:100]
        email   = b.get('email', '').strip()[:200]
        subject = b.get('subject', '').strip()[:200]
        message = b.get('message', '').strip()[:5000]
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
        _notify_admin(
            f'Contact: {subject} — from {name}', body_text,
            reply_to=email,
            push_title=f'Contact: {subject}',
            push_body=f'From {name} <{email}>\n{message[:150]}', tags='email')
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
        _notify_admin(
            f'Info Request: {entry["name"]} — Action Outreach Ministry', body_text,
            reply_to=email,
            push_title=f'Info Request — {entry["name"]}',
            push_body=f'{entry["address"]}\n{", ".join(interests) if interests else "General info"}', tags='mailbox')
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
        if not self._require_perm('view_donations'):
            return
        self._json(_load_donations())

    # ── Finances: recorded income (deposits) + expenses + accounting summary ───
    def _period_start(self):
        from urllib.parse import parse_qs
        period = (parse_qs(urlparse(self.path).query).get('period', ['all'])[0]).lower()
        import datetime as _dt
        now = _dt.datetime.now()
        if period == 'month':
            return period, _dt.datetime(now.year, now.month, 1).timestamp()
        if period == 'year':
            return period, _dt.datetime(now.year, 1, 1).timestamp()
        return period, 0

    def _api_admin_income(self):
        if not self._require_perm('manage_finances'):
            return
        self._json(_load_income())

    def _api_admin_expenses(self):
        if not self._require_perm('manage_finances'):
            return
        self._json(_load_expenses())

    def _api_income_add(self):
        actor = self._require_perm('manage_finances')
        if not actor:
            return
        b = self._body()
        try:
            amount = round(float(b.get('amount', 0)), 2)
        except Exception:
            amount = 0
        if amount <= 0:
            return self._err('Amount must be greater than 0')
        rec = {'id': secrets.token_hex(8),
               'date': b.get('date', '').strip() or time.strftime('%Y-%m-%d'),
               'source': b.get('source', 'cashapp').strip() or 'other',
               'amount': amount, 'fund': b.get('fund', 'General').strip() or 'General',
               'donor': b.get('donor', '').strip(), 'notes': b.get('notes', '').strip(),
               'recorded_by': actor, 'ts': int(time.time())}
        income = _load_income(); income.append(rec); _save_income(income)
        self._json({'ok': True, 'id': rec['id']})

    def _api_income_delete(self):
        if not self._require_perm('manage_finances'):
            return
        rid = self._body().get('id', '')
        _save_income([r for r in _load_income() if r.get('id') != rid])
        self._json({'ok': True})

    def _api_expense_add(self):
        actor = self._require_perm('manage_finances')
        if not actor:
            return
        b = self._body()
        try:
            amount = round(float(b.get('amount', 0)), 2)
        except Exception:
            amount = 0
        if amount <= 0:
            return self._err('Amount must be greater than 0')
        if not b.get('payee', '').strip():
            return self._err('Payee is required')
        rec = {'id': secrets.token_hex(8),
               'date': b.get('date', '').strip() or time.strftime('%Y-%m-%d'),
               'payee': b.get('payee', '').strip(),
               'category': b.get('category', 'Other').strip() or 'Other',
               'amount': amount, 'method': b.get('method', '').strip(),
               'fund': b.get('fund', 'General').strip() or 'General',
               'notes': b.get('notes', '').strip(),
               'recorded_by': actor, 'ts': int(time.time())}
        exp = _load_expenses(); exp.append(rec); _save_expenses(exp)
        self._json({'ok': True, 'id': rec['id']})

    def _api_expense_delete(self):
        if not self._require_perm('manage_finances'):
            return
        eid = self._body().get('id', '')
        _save_expenses([e for e in _load_expenses() if e.get('id') != eid])
        self._json({'ok': True})

    def _api_finance_summary(self):
        if not self._require_perm('manage_finances'):
            return
        period, start = self._period_start()
        # Income = PayPal-confirmed donations + manually recorded deposits (NOT click-intents).
        income_items = []
        for d in _load_donations():
            if d.get('timestamp', 0) >= start:
                income_items.append({'amount': float(d.get('amount', 0) or 0),
                                     'fund': d.get('fund', 'General') or 'General', 'source': 'paypal'})
        for r in _load_income():
            if r.get('ts', 0) >= start:
                income_items.append({'amount': float(r.get('amount', 0) or 0),
                                     'fund': r.get('fund', 'General') or 'General',
                                     'source': r.get('source', 'other') or 'other'})
        expenses = [e for e in _load_expenses() if e.get('ts', 0) >= start]

        def _by(items, field):
            out = {}
            for i in items:
                k = i.get(field, 'Other') or 'Other'
                out[k] = round(out.get(k, 0) + float(i.get('amount', 0) or 0), 2)
            return out

        income_total  = round(sum(i['amount'] for i in income_items), 2)
        expense_total = round(sum(float(e.get('amount', 0) or 0) for e in expenses), 2)
        self._json({
            'period': period,
            'income_total': income_total, 'expense_total': expense_total,
            'net': round(income_total - expense_total, 2),
            'income_by_source': _by(income_items, 'source'),
            'income_by_fund':   _by(income_items, 'fund'),
            'expense_by_category': _by(expenses, 'category'),
            'expense_by_fund':     _by(expenses, 'fund'),
            'income_count': len(income_items), 'expense_count': len(expenses),
            'categories': EXPENSE_CATEGORIES, 'sources': INCOME_SOURCES,
        })

    def _api_paypal_webhook(self):
        """PayPal Webhook listener (the supported replacement for IPN). Verifies the signature via
        PayPal's REST API, then records confirmed payments. Always returns 200 to PayPal."""
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        cfg = _load_paypal()
        try:
            if _paypal_verify_webhook(cfg, self.headers, raw):
                evt   = json.loads(raw)
                etype = evt.get('event_type', '')
                res   = evt.get('resource', {}) or {}
                if etype in ('PAYMENT.CAPTURE.COMPLETED', 'PAYMENT.SALE.COMPLETED'):
                    amt      = res.get('amount', {}) or {}
                    amount   = float(amt.get('value') or amt.get('total') or 0)
                    currency = amt.get('currency_code') or amt.get('currency') or 'USD'
                    payer    = res.get('payer', {}) or {}
                    pn       = payer.get('name', {}) or {}
                    donor    = (str(pn.get('given_name', '')) + ' ' + str(pn.get('surname', ''))).strip()
                    email    = payer.get('email_address', '')
                    fund     = res.get('custom_id') or res.get('invoice_id') or 'General Fund'
                    freq     = 'monthly' if res.get('billing_agreement_id') else 'once'
                    tid      = res.get('id') or evt.get('id') or secrets.token_hex(8)
                    _record_donation({'id': tid, 'amount': amount, 'currency': currency,
                                      'donor_name': donor, 'donor_email': email, 'fund': fund,
                                      'freq': freq, 'timestamp': int(time.time()), 'source': 'paypal_webhook'})
        except Exception:
            pass
        self.send_response(200)
        self.end_headers()

    def _api_get_paypal_config(self):
        if not self._require_perm('manage_settings'):
            return
        cfg = _load_paypal()
        self._json({'client_id': cfg.get('client_id', ''), 'webhook_id': cfg.get('webhook_id', ''),
                    'mode': cfg.get('mode', 'live'), 'has_secret': bool(cfg.get('client_secret'))})

    def _api_save_paypal_config(self):
        if not self._require_perm('manage_settings'):
            return
        b = self._body()
        cfg = _load_paypal()
        cfg['client_id']  = b.get('client_id', '').strip()
        cfg['webhook_id'] = b.get('webhook_id', '').strip()
        cfg['mode']       = b.get('mode', 'live').strip() or 'live'
        # only overwrite the secret if a new one was provided (UI sends blank to keep existing)
        if b.get('client_secret', '').strip():
            cfg['client_secret'] = b.get('client_secret', '').strip()
        _save_paypal(cfg)
        self._json({'ok': True})

    # ── Smart Buttons (in-page checkout via Orders v2) ────────────────────────
    _FUND_LABELS = {'general': 'General Fund', 'missions': 'Global Missions',
                    'food': 'Community Feeding Program', 'bibles': 'Bible Distribution',
                    'youth': 'Youth Ministry'}

    def _api_paypal_public(self):
        """Public, no-auth: the client_id the browser SDK needs (client_id is safe to expose;
        the secret never leaves the server). `enabled` gates the in-page flow on the frontend."""
        cfg = _load_paypal()
        self._json({'client_id': cfg.get('client_id', ''), 'mode': cfg.get('mode', 'live'),
                    'enabled': bool(cfg.get('client_id') and cfg.get('client_secret'))})

    def _api_paypal_create_order(self):
        b = self._body()
        try:
            amount = round(float(b.get('amount', 0)), 2)
        except Exception:
            amount = 0.0
        if amount < 1:
            return self._err('Invalid amount')
        fund = str(b.get('fund', 'general'))[:50]
        cfg = _load_paypal()
        name = (_load_content().get('settings', {}) or {}).get('ministryName') or 'Action Outreach Ministry'
        payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {'currency_code': 'USD', 'value': '%.2f' % amount},
                'custom_id': fund,        # carried into the capture + webhook so the fund is known
                'description': ('%s — %s' % (name, self._FUND_LABELS.get(fund, 'General Fund')))[:127],
            }],
            'application_context': {'shipping_preference': 'NO_SHIPPING',
                                    'brand_name': name[:127], 'user_action': 'PAY_NOW'},
        }
        res, err = _paypal_api(cfg, 'POST', '/v2/checkout/orders', payload)
        if not res or not res.get('id'):
            return self._err('Could not create PayPal order', 502)
        self._json({'id': res['id']})

    def _api_paypal_capture_order(self):
        b = self._body()
        oid = str(b.get('orderID', '')).strip()
        if not oid or not oid.isalnum():
            return self._err('Missing or invalid orderID')
        cfg = _load_paypal()
        res, err = _paypal_api(cfg, 'POST', '/v2/checkout/orders/%s/capture' % oid, {})
        if not res:
            return self._err('Capture failed', 502)
        status = res.get('status')
        if status == 'COMPLETED':
            try:
                pu    = (res.get('purchase_units') or [{}])[0]
                cap   = ((pu.get('payments') or {}).get('captures') or [{}])[0]
                amt   = cap.get('amount') or {}
                payer = res.get('payer') or {}
                pn    = payer.get('name') or {}
                donor = (str(pn.get('given_name', '')) + ' ' + str(pn.get('surname', ''))).strip()
                # _record_donation dedupes by id, so the webhook firing for the same capture is a no-op
                _record_donation({'id': cap.get('id') or oid, 'amount': float(amt.get('value') or 0),
                                  'currency': amt.get('currency_code', 'USD'), 'donor_name': donor,
                                  'donor_email': payer.get('email_address', ''),
                                  'fund': pu.get('custom_id') or 'General Fund', 'freq': 'once',
                                  'timestamp': int(time.time()), 'source': 'paypal_smart_button'})
            except Exception:
                pass
        self._json({'ok': status == 'COMPLETED', 'status': status})

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
    _ensure_roles()   # migrate existing users to explicit roles; guarantee an owner
    server = ThreadedHTTPServer(('0.0.0.0', PORT), AOMHandler)
    print(f'Action Outreach Ministry server → http://0.0.0.0:{PORT}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
