// ---- Settings ----
var SETTINGS = {
  paypalEmail: '',
  ministryName: 'Action Outreach Ministry',
  phone: '(850) 000-0000',
  contactEmail: 'info@actionoutreachministry.com',
};
var currentAdminUser = null;

// ---- Content Defaults ----
var CONTENT_DEFAULTS = {
  tagline: 'Reaching the World for Christ',
  location: 'Pensacola, FL',
  outreachHeroTitle: 'Reaching Hearts, Changing Lives',
  outreachHeroText: 'Action Outreach Ministry is committed to spreading the Gospel of Jesus Christ through compassionate service, community outreach, and discipleship.',
  aboutTitle: 'About Our Ministry',
  aboutText1: 'Founded on faith and fueled by love, Action Outreach Ministry has been serving the community for over two decades. We believe every person is made in the image of God and deserves to hear the Good News. Our volunteers, missionaries, and partners work tirelessly across local and international communities to bring transformation through the power of the Gospel.',
  aboutText2: 'Whether you join us in person, volunteer your time, or support us financially — you are a vital part of this mission. Together, we are the hands and feet of Jesus.',
  cards: [
    { icon: '🌍', title: 'Global Missions', text: 'We partner with missionaries worldwide to bring hope, healing, and the message of salvation to unreached communities.' },
    { icon: '🍞', title: 'Community Feeding', text: 'Our weekly food pantry serves hundreds of families, meeting physical needs while sharing the love of Christ.' },
    { icon: '📖', title: 'Bible Distribution', text: 'We distribute Bibles and discipleship materials to prisons, shelters, and underserved communities locally and abroad.' },
    { icon: '👨‍👩‍👧', title: 'Family Restoration', text: 'Through counseling, support groups, and prayer, we help families find healing and walk in God\'s purpose.' }
  ],
  testimoniesHeroTitle: 'Stories of Transformation',
  testimoniesHeroText: 'God is moving. Read how lives are being changed through prayer, outreach, and the power of the Gospel.',
  testimonies: [
    { quote: 'I was homeless and without hope. Action Outreach found me, fed me, and shared Jesus with me. Today I have a home, a family, and a faith that never wavers.', author: '— Marcus T., Pensacola FL' },
    { quote: 'Through the prayer ministry, my marriage was completely restored. We were on the verge of divorce and God showed up in a miraculous way.', author: '— Sandra & James W.' },
    { quote: 'The Bible they gave me in prison changed my life. I got out, found this ministry, and now I volunteer every week to give back what was given to me.', author: '— David R.' }
  ],
  eventsHeroTitle: 'Upcoming Events',
  eventsHeroText: 'Join us as we gather for worship, outreach, and fellowship. All are welcome.',
  events: [
    { month: 'MAY', day: '18', title: 'Community Prayer Walk', meta: '9:00 AM · Downtown Pensacola · Free', text: 'Join us as we walk through the community, praying over businesses, schools, and families. Wear comfortable shoes and bring a heart for the city.' },
    { month: 'MAY', day: '25', title: 'Food Pantry & Gospel Outreach', meta: '10:00 AM – 2:00 PM · Ministry Center · Free', text: 'Hundreds of families will receive groceries and hear the Gospel. Volunteers needed — sign up at the contact form below.' },
    { month: 'JUN', day: '7', title: 'Revival Night', meta: '6:00 PM · Main Sanctuary · Free', text: 'A night of worship, testimonies, and the Word. Come expectant — God moves powerfully when His people gather.' },
    { month: 'JUN', day: '21', title: 'Youth Summer Kickoff', meta: '11:00 AM · Ministry Grounds · Free', text: 'Games, food, and a powerful message for our youth. Bring the whole family.' }
  ],
  prayerHeroTitle: 'Urgent Prayer Requests',
  prayerHeroText: 'We believe in the power of prayer. Submit your request and our prayer team will stand in agreement with you.',
  prayers: [
    { urgent: true, text: 'Please pray for our missionary team in Haiti who are currently in a dangerous region. Pray for their safety, provision, and boldness.', meta: 'Submitted by Ministry Team · May 1, 2026' },
    { urgent: true, text: 'Pray for Brother James who is in ICU following emergency surgery. His family needs strength and God\'s healing touch.', meta: 'Submitted by Family · May 2, 2026' },
    { urgent: false, text: 'Pray for our upcoming mission trip to Guatemala — finances, visas, and spiritual preparation for the entire team.', meta: 'Submitted by Missions Dept. · Apr 28, 2026' }
  ]
};

var CONTENT = JSON.parse(JSON.stringify(CONTENT_DEFAULTS));

(function init() {
  var saved = localStorage.getItem('aom_settings');
  if (saved) { try { Object.assign(SETTINGS, JSON.parse(saved)); } catch(e) {} }
  var savedContent = localStorage.getItem('aom_content');
  if (savedContent) { try { Object.assign(CONTENT, JSON.parse(savedContent)); } catch(e) {} }
  fetch('/api/auth/status').then(function(r) { return r.json(); }).then(function(d) {
    if (d.authenticated && d.is_admin) {
      currentAdminUser = {username: d.username, is_admin: d.is_admin};
    }
  }).catch(function() {});

  var resetToken = new URLSearchParams(window.location.search).get('reset_token');
  if (resetToken) { showResetConfirmModal(resetToken); }
})();

// ---- Helpers ----
function setEl(id, text) {
  var el = document.getElementById(id);
  if (el) el.textContent = text;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showSaveOk(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.style.display = 'block';
  setTimeout(function() { el.style.display = 'none'; }, 2000);
}

// ---- Render Content ----
function applyContent() {
  setEl('site-name-header', SETTINGS.ministryName);
  setEl('site-tagline', CONTENT.tagline);
  var fn = document.getElementById('site-name-footer');
  if (fn) fn.innerHTML = '&#10011; ' + escHtml(SETTINGS.ministryName);
  setEl('footer-location', '📍 ' + CONTENT.location);
  setEl('footer-phone', '📞 ' + SETTINGS.phone);
  setEl('footer-email', '✉ ' + SETTINGS.contactEmail);
  setEl('outreach-hero-title', CONTENT.outreachHeroTitle);
  setEl('outreach-hero-text', CONTENT.outreachHeroText);
  setEl('about-title', CONTENT.aboutTitle);
  setEl('about-text-1', CONTENT.aboutText1);
  setEl('about-text-2', CONTENT.aboutText2);
  renderCards();
  setEl('testimonies-hero-title', CONTENT.testimoniesHeroTitle);
  setEl('testimonies-hero-text', CONTENT.testimoniesHeroText);
  renderTestimonies();
  setEl('events-hero-title', CONTENT.eventsHeroTitle);
  setEl('events-hero-text', CONTENT.eventsHeroText);
  renderEvents();
  setEl('prayer-hero-title', CONTENT.prayerHeroTitle);
  setEl('prayer-hero-text', CONTENT.prayerHeroText);
  renderPrayers();
}

function renderCards() {
  var grid = document.getElementById('cards-grid');
  if (!grid) return;
  grid.innerHTML = CONTENT.cards.map(function(c) {
    return '<div class="info-card"><div class="card-icon">' + c.icon + '</div><h3>' + escHtml(c.title) + '</h3><p>' + escHtml(c.text) + '</p></div>';
  }).join('');
}

function renderTestimonies() {
  var list = document.getElementById('testimony-list');
  if (!list) return;
  list.innerHTML = CONTENT.testimonies.map(function(t) {
    return '<div class="testimony-card"><div class="testimony-quote">"' + escHtml(t.quote) + '"</div><div class="testimony-author">' + escHtml(t.author) + '</div></div>';
  }).join('');
}

function renderEvents() {
  var list = document.getElementById('events-list');
  if (!list) return;
  list.innerHTML = CONTENT.events.map(function(e) {
    return '<div class="event-card">' +
      '<div class="event-date-box"><span class="event-month">' + escHtml(e.month) + '</span><span class="event-day">' + escHtml(e.day) + '</span></div>' +
      '<div class="event-info"><h3>' + escHtml(e.title) + '</h3><p class="event-meta">' + escHtml(e.meta) + '</p><p>' + escHtml(e.text) + '</p></div>' +
      '</div>';
  }).join('');
}

function renderPrayers() {
  var list = document.getElementById('prayer-list');
  if (!list) return;
  list.innerHTML = CONTENT.prayers.map(function(p) {
    return '<div class="prayer-card' + (p.urgent ? ' urgent' : '') + '">' +
      (p.urgent ? '<div class="prayer-badge">URGENT</div>' : '') +
      '<div class="prayer-text">' + escHtml(p.text) + '</div>' +
      '<div class="prayer-meta">' + escHtml(p.meta) + '</div>' +
      '<button class="pray-btn" onclick="markPrayed(this)">🙏 I\'m Praying</button>' +
      '</div>';
  }).join('');
}

// ---- Tab Navigation ----
function switchTab(id) {
  document.querySelectorAll('.nav-tab').forEach(function(t) {
    t.classList.toggle('active', t.dataset.tab === id);
  });
  document.querySelectorAll('.tab-section').forEach(function(s) {
    s.classList.toggle('active', s.id === 'tab-' + id);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.querySelectorAll('.nav-tab').forEach(function(btn) {
  btn.addEventListener('click', function() { switchTab(btn.dataset.tab); });
});

// ---- Donation Modal ----
var selectedAmount = 100;
var donationFreq = 'once';

function openDonation() {
  document.getElementById('donation-overlay').style.display = 'flex';
  document.getElementById('donation-error').style.display = 'none';
  updateGiveBtn();
}
function closeDonation() {
  document.getElementById('donation-overlay').style.display = 'none';
}
document.getElementById('donation-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeDonation();
});

document.querySelectorAll('.amount-btn').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('.amount-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    var customWrap = document.getElementById('custom-input-wrap');
    if (btn.id === 'custom-btn') {
      customWrap.style.display = 'block';
      document.getElementById('custom-amount').focus();
      selectedAmount = 0;
    } else {
      customWrap.style.display = 'none';
      selectedAmount = parseInt(btn.dataset.amount);
    }
    updateGiveBtn();
  });
});

document.getElementById('custom-amount').addEventListener('input', function() {
  selectedAmount = parseFloat(this.value) || 0;
  updateGiveBtn();
});

function setFreq(f) {
  donationFreq = f;
  document.getElementById('freq-once').classList.toggle('active', f === 'once');
  document.getElementById('freq-monthly').classList.toggle('active', f === 'monthly');
  updateGiveBtn();
}

function updateGiveBtn() {
  var btn = document.getElementById('give-btn');
  var amt = selectedAmount > 0 ? '$' + selectedAmount : 'Amount';
  var freq = donationFreq === 'monthly' ? '/mo' : '';
  btn.textContent = 'Give ' + amt + freq + ' Now';
}

function processDonation() {
  var errEl = document.getElementById('donation-error');
  errEl.style.display = 'none';
  if (!selectedAmount || selectedAmount < 1) {
    errEl.textContent = 'Please select or enter a donation amount.';
    errEl.style.display = 'block';
    return;
  }
  var paypalEmail = SETTINGS.paypalEmail;
  if (!paypalEmail) {
    errEl.textContent = 'Donation processing is being set up. Please contact us directly to give.';
    errEl.style.display = 'block';
    return;
  }
  var fund = document.getElementById('fund-select').value;
  var fundLabels = { general:'General Fund', missions:'Global Missions', food:'Community Feeding Program', bibles:'Bible Distribution', youth:'Youth Ministry' };
  var params = new URLSearchParams({
    cmd: donationFreq === 'monthly' ? '_xclick-subscriptions' : '_donations',
    business: paypalEmail,
    item_name: SETTINGS.ministryName + ' — ' + (fundLabels[fund] || 'General Fund'),
    amount: selectedAmount.toFixed(2),
    currency_code: 'USD',
    no_note: '0',
    return: window.location.href,
    cancel_return: window.location.href,
  });
  if (donationFreq === 'monthly') {
    params.set('a3', selectedAmount.toFixed(2));
    params.set('p3', '1');
    params.set('t3', 'M');
    params.set('src', '1');
  }
  window.open('https://www.paypal.com/donate?' + params.toString(), '_blank');
  closeDonation();
}

// ---- Prayer "I'm Praying" ----
function markPrayed(btn) {
  btn.classList.add('prayed');
  btn.textContent = '🙏 Praying for this';
  btn.disabled = true;
}

// ---- Forms ----
document.getElementById('testimony-form').addEventListener('submit', function(e) {
  e.preventDefault();
  document.getElementById('testimony-form').style.display = 'none';
  document.getElementById('testimony-thanks').style.display = 'block';
});
document.getElementById('prayer-form').addEventListener('submit', function(e) {
  e.preventDefault();
  document.getElementById('prayer-form').style.display = 'none';
  document.getElementById('prayer-thanks').style.display = 'block';
});

// ---- Admin Modal ----
function openAdmin() {
  document.getElementById('admin-overlay').style.display = 'flex';
  document.getElementById('admin-login-wrap').style.display = 'block';
  document.getElementById('admin-panel').style.display = 'none';
  document.getElementById('admin-user').value = '';
  document.getElementById('admin-pw').value = '';
  document.getElementById('admin-pw-err').style.display = 'none';
  document.getElementById('admin-reset-wrap').style.display = 'none';
  document.getElementById('admin-reset-err').style.display = 'none';
  document.getElementById('admin-reset-ok').style.display = 'none';
}
function closeAdmin() {
  document.getElementById('admin-overlay').style.display = 'none';
}
document.getElementById('admin-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeAdmin();
});
function checkAdminPw() {
  var user = document.getElementById('admin-user').value.trim();
  var pw = document.getElementById('admin-pw').value;
  fetch('/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: user, password: pw})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      currentAdminUser = {username: d.username, is_admin: d.is_admin};
      document.getElementById('admin-login-wrap').style.display = 'none';
      document.getElementById('admin-panel').style.display = 'block';
      var bar = document.getElementById('admin-logged-in-bar');
      if (bar) bar.textContent = '✓ Logged in as ' + d.username;
      adminTab('settings');
    } else {
      document.getElementById('admin-pw-err').style.display = 'block';
    }
  }).catch(function() {
    // No backend (static hosting) — fall back to hardcoded credentials
    if (user === 'admin' && pw === 'Ministrey2025') {
      currentAdminUser = {username: 'admin', is_admin: true};
      document.getElementById('admin-login-wrap').style.display = 'none';
      document.getElementById('admin-panel').style.display = 'block';
      var bar = document.getElementById('admin-logged-in-bar');
      if (bar) bar.textContent = '✓ Logged in as admin';
      adminTab('settings');
    } else {
      document.getElementById('admin-pw-err').style.display = 'block';
    }
  });
}
document.getElementById('admin-pw').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') checkAdminPw();
});
document.getElementById('admin-user').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') document.getElementById('admin-pw').focus();
});
function toggleResetSection() {
  var wrap = document.getElementById('admin-reset-wrap');
  wrap.style.display = wrap.style.display === 'none' ? 'block' : 'none';
}
function doResetCredentials() {
  var code  = document.getElementById('admin-recovery-code').value.trim();
  var user  = document.getElementById('admin-reset-user').value.trim();
  var pw    = document.getElementById('admin-reset-pw').value;
  document.getElementById('admin-reset-err').style.display = 'none';
  document.getElementById('admin-reset-ok').style.display  = 'none';
  fetch('/api/auth/reset', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({recovery_code: code, username: user, password: pw})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('admin-reset-ok').style.display = 'block';
      document.getElementById('admin-recovery-code').value = '';
      document.getElementById('admin-reset-user').value = '';
      document.getElementById('admin-reset-pw').value = '';
    } else {
      document.getElementById('admin-reset-err').textContent = d.error || 'Reset failed.';
      document.getElementById('admin-reset-err').style.display = 'block';
    }
  }).catch(function() {
    document.getElementById('admin-reset-err').style.display = 'block';
  });
}

// ---- Password Reset Confirm (from email link) ----
var _pendingResetToken = null;
function showResetConfirmModal(token) {
  _pendingResetToken = token;
  document.getElementById('reset-confirm-overlay').style.display = 'flex';
  history.replaceState({}, '', window.location.pathname);
}
function submitResetConfirm() {
  var pw  = document.getElementById('reset-new-pw').value;
  var pw2 = document.getElementById('reset-new-pw2').value;
  var errEl = document.getElementById('reset-confirm-err');
  errEl.style.display = 'none';
  if (!pw) { errEl.textContent = 'Enter a new password.'; errEl.style.display = 'block'; return; }
  if (pw !== pw2) { errEl.textContent = 'Passwords do not match.'; errEl.style.display = 'block'; return; }
  fetch('/api/auth/reset-confirm', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({token: _pendingResetToken, password: pw})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('reset-confirm-ok').style.display = 'block';
      document.getElementById('reset-new-pw').value = '';
      document.getElementById('reset-new-pw2').value = '';
    } else {
      errEl.textContent = d.error || 'Reset failed. Link may have expired.';
      errEl.style.display = 'block';
    }
  });
}

// ---- SMTP Config ----
function loadSmtpConfig() {
  fetch('/api/admin/smtp-config').then(function(r) { return r.json(); }).then(function(d) {
    if (d.error) return;
    document.getElementById('smtp-host').value      = d.host || '';
    document.getElementById('smtp-port').value      = d.port || '587';
    document.getElementById('smtp-user').value      = d.username || '';
    document.getElementById('smtp-from-name').value = d.from_name || '';
    document.getElementById('smtp-tls').value       = d.tls || 'starttls';
    if (d.has_password) document.getElementById('smtp-pass').placeholder = '(saved)';
  }).catch(function() {});
}
function saveSmtpConfig() {
  var body = {
    host:      document.getElementById('smtp-host').value.trim(),
    port:      document.getElementById('smtp-port').value || '587',
    username:  document.getElementById('smtp-user').value.trim(),
    from_name: document.getElementById('smtp-from-name').value.trim(),
    tls:       document.getElementById('smtp-tls').value,
    password:  document.getElementById('smtp-pass').value
  };
  fetch('/api/admin/smtp-config', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('smtp-pass').value = '';
      document.getElementById('smtp-pass').placeholder = '(saved)';
      showSaveOk('smtp-save-ok');
    }
  });
}
function testSmtpEmail() {
  var msgEl = document.getElementById('smtp-msg');
  msgEl.style.display = 'none';
  fetch('/api/admin/smtp-test', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}' })
    .then(function(r) { return r.json(); }).then(function(d) {
      msgEl.style.display = 'block';
      if (d.ok) {
        msgEl.style.color = '#86efac';
        msgEl.textContent = 'Test email sent to ' + d.sent_to;
      } else {
        msgEl.style.color = '#f87171';
        msgEl.textContent = d.error || 'Failed to send test email.';
      }
    });
}

// ---- Admin Tabs ----
function adminTab(name) {
  document.querySelectorAll('.admin-tab').forEach(function(t) {
    t.classList.toggle('active', t.dataset.tab === name);
  });
  document.querySelectorAll('.admin-tab-body').forEach(function(b) {
    b.style.display = b.id === 'admin-tab-' + name ? 'block' : 'none';
  });
  if (name === 'settings') { populateSettingsTab(); loadSmtpConfig(); loadUserCount(); }
  if (name === 'content') populateContentTab();
  if (name === 'testimonies') renderAdminTestimonies();
  if (name === 'events') renderAdminEvents();
  if (name === 'prayer') renderAdminPrayers();
  if (name === 'users') renderAdminUsers();
}

function loadUserCount() {
  fetch('/api/admin/users').then(function(r) { return r.json(); }).then(function(users) {
    var el = document.getElementById('settings-user-count');
    if (el) el.textContent = users.length + ' user' + (users.length === 1 ? '' : 's') + ' registered';
  }).catch(function() {});
}

// ---- Settings Tab ----
function populateSettingsTab() {
  document.getElementById('admin-paypal-email').value = SETTINGS.paypalEmail || '';
  document.getElementById('admin-ministry-name').value = SETTINGS.ministryName || '';
  document.getElementById('admin-phone').value = SETTINGS.phone || '';
  document.getElementById('admin-contact-email').value = SETTINGS.contactEmail || '';
  document.getElementById('admin-tagline').value = CONTENT.tagline || '';
  document.getElementById('admin-location').value = CONTENT.location || '';
  document.getElementById('admin-new-pw').value = '';
  document.getElementById('admin-new-pw2').value = '';
}
function saveAdminSettings() {
  SETTINGS.paypalEmail = document.getElementById('admin-paypal-email').value.trim();
  SETTINGS.ministryName = document.getElementById('admin-ministry-name').value.trim() || 'Action Outreach Ministry';
  SETTINGS.phone = document.getElementById('admin-phone').value.trim();
  SETTINGS.contactEmail = document.getElementById('admin-contact-email').value.trim();
  CONTENT.tagline = document.getElementById('admin-tagline').value.trim();
  CONTENT.location = document.getElementById('admin-location').value.trim();
  localStorage.setItem('aom_settings', JSON.stringify(SETTINGS));
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  applyContent();
  showSaveOk('admin-save-ok');
}
function changeMyPassword() {
  var newPw  = document.getElementById('admin-new-pw').value;
  var newPw2 = document.getElementById('admin-new-pw2').value;
  document.getElementById('admin-creds-err').style.display = 'none';
  if (!newPw) return;
  if (newPw !== newPw2) { document.getElementById('admin-creds-err').style.display = 'block'; return; }
  fetch('/api/admin/set-password', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: currentAdminUser.username, password: newPw})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('admin-new-pw').value = '';
      document.getElementById('admin-new-pw2').value = '';
      showSaveOk('admin-creds-ok');
    }
  });
}

// ---- Content Tab ----
function populateContentTab() {
  document.getElementById('ct-outreach-title').value = CONTENT.outreachHeroTitle;
  document.getElementById('ct-outreach-text').value = CONTENT.outreachHeroText;
  document.getElementById('ct-about-title').value = CONTENT.aboutTitle;
  document.getElementById('ct-about-1').value = CONTENT.aboutText1;
  document.getElementById('ct-about-2').value = CONTENT.aboutText2;
  document.getElementById('ct-test-title').value = CONTENT.testimoniesHeroTitle;
  document.getElementById('ct-test-text').value = CONTENT.testimoniesHeroText;
  document.getElementById('ct-events-title').value = CONTENT.eventsHeroTitle;
  document.getElementById('ct-events-text').value = CONTENT.eventsHeroText;
  document.getElementById('ct-prayer-title').value = CONTENT.prayerHeroTitle;
  document.getElementById('ct-prayer-text').value = CONTENT.prayerHeroText;
  CONTENT.cards.forEach(function(c, i) {
    document.getElementById('ct-card-icon-' + i).value = c.icon;
    document.getElementById('ct-card-title-' + i).value = c.title;
    document.getElementById('ct-card-text-' + i).value = c.text;
  });
}
function saveContentTab() {
  CONTENT.outreachHeroTitle = document.getElementById('ct-outreach-title').value.trim();
  CONTENT.outreachHeroText = document.getElementById('ct-outreach-text').value.trim();
  CONTENT.aboutTitle = document.getElementById('ct-about-title').value.trim();
  CONTENT.aboutText1 = document.getElementById('ct-about-1').value.trim();
  CONTENT.aboutText2 = document.getElementById('ct-about-2').value.trim();
  CONTENT.testimoniesHeroTitle = document.getElementById('ct-test-title').value.trim();
  CONTENT.testimoniesHeroText = document.getElementById('ct-test-text').value.trim();
  CONTENT.eventsHeroTitle = document.getElementById('ct-events-title').value.trim();
  CONTENT.eventsHeroText = document.getElementById('ct-events-text').value.trim();
  CONTENT.prayerHeroTitle = document.getElementById('ct-prayer-title').value.trim();
  CONTENT.prayerHeroText = document.getElementById('ct-prayer-text').value.trim();
  CONTENT.cards.forEach(function(c, i) {
    c.icon = document.getElementById('ct-card-icon-' + i).value.trim();
    c.title = document.getElementById('ct-card-title-' + i).value.trim();
    c.text = document.getElementById('ct-card-text-' + i).value.trim();
  });
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  applyContent();
  showSaveOk('ct-save-ok');
}

// ---- Testimonies CRUD ----
function renderAdminTestimonies() {
  var wrap = document.getElementById('admin-testimonies-list');
  if (!CONTENT.testimonies.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No testimonies yet.</p>'; return; }
  wrap.innerHTML = CONTENT.testimonies.map(function(t, i) {
    return '<div class="admin-item">' +
      '<div class="admin-item-preview">"' + escHtml(t.quote.substring(0, 55)) + '…"</div>' +
      '<div class="admin-item-actions">' +
      '<button class="admin-item-btn" onclick="editTestimony(' + i + ')">Edit</button>' +
      '<button class="admin-item-btn del" onclick="deleteTestimony(' + i + ')">Delete</button>' +
      '</div></div>';
  }).join('');
}
function editTestimony(idx) {
  var t = CONTENT.testimonies[idx];
  document.getElementById('t-edit-idx').value = idx;
  document.getElementById('t-edit-quote').value = t.quote;
  document.getElementById('t-edit-author').value = t.author;
  document.getElementById('admin-testimony-edit').style.display = 'block';
}
function newTestimony() {
  document.getElementById('t-edit-idx').value = -1;
  document.getElementById('t-edit-quote').value = '';
  document.getElementById('t-edit-author').value = '';
  document.getElementById('admin-testimony-edit').style.display = 'block';
}
function saveTestimony() {
  var idx = parseInt(document.getElementById('t-edit-idx').value);
  var quote = document.getElementById('t-edit-quote').value.trim();
  var author = document.getElementById('t-edit-author').value.trim();
  if (!quote) return;
  if (idx === -1) { CONTENT.testimonies.push({ quote: quote, author: author }); }
  else { CONTENT.testimonies[idx] = { quote: quote, author: author }; }
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  renderTestimonies();
  renderAdminTestimonies();
  document.getElementById('admin-testimony-edit').style.display = 'none';
}
function deleteTestimony(idx) {
  if (!confirm('Delete this testimony?')) return;
  CONTENT.testimonies.splice(idx, 1);
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  renderTestimonies();
  renderAdminTestimonies();
}

// ---- Events CRUD ----
function renderAdminEvents() {
  var wrap = document.getElementById('admin-events-list');
  if (!CONTENT.events.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No events yet.</p>'; return; }
  wrap.innerHTML = CONTENT.events.map(function(e, i) {
    return '<div class="admin-item">' +
      '<div class="admin-item-preview"><strong>' + escHtml(e.month) + ' ' + escHtml(e.day) + '</strong> — ' + escHtml(e.title) + '</div>' +
      '<div class="admin-item-actions">' +
      '<button class="admin-item-btn" onclick="editEvent(' + i + ')">Edit</button>' +
      '<button class="admin-item-btn del" onclick="deleteEvent(' + i + ')">Delete</button>' +
      '</div></div>';
  }).join('');
}
function editEvent(idx) {
  var e = CONTENT.events[idx];
  document.getElementById('ev-edit-idx').value = idx;
  document.getElementById('ev-edit-month').value = e.month;
  document.getElementById('ev-edit-day').value = e.day;
  document.getElementById('ev-edit-title').value = e.title;
  document.getElementById('ev-edit-meta').value = e.meta;
  document.getElementById('ev-edit-text').value = e.text;
  document.getElementById('admin-event-edit').style.display = 'block';
}
function newEvent() {
  document.getElementById('ev-edit-idx').value = -1;
  ['ev-edit-month','ev-edit-day','ev-edit-title','ev-edit-meta','ev-edit-text'].forEach(function(id) { document.getElementById(id).value = ''; });
  document.getElementById('admin-event-edit').style.display = 'block';
}
function saveEvent() {
  var idx = parseInt(document.getElementById('ev-edit-idx').value);
  var item = {
    month: document.getElementById('ev-edit-month').value.trim().toUpperCase(),
    day: document.getElementById('ev-edit-day').value.trim(),
    title: document.getElementById('ev-edit-title').value.trim(),
    meta: document.getElementById('ev-edit-meta').value.trim(),
    text: document.getElementById('ev-edit-text').value.trim()
  };
  if (!item.title) return;
  if (idx === -1) { CONTENT.events.push(item); }
  else { CONTENT.events[idx] = item; }
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  renderEvents();
  renderAdminEvents();
  document.getElementById('admin-event-edit').style.display = 'none';
}
function deleteEvent(idx) {
  if (!confirm('Delete this event?')) return;
  CONTENT.events.splice(idx, 1);
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  renderEvents();
  renderAdminEvents();
}

// ---- Prayer CRUD ----
function renderAdminPrayers() {
  var wrap = document.getElementById('admin-prayers-list');
  if (!CONTENT.prayers.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No prayer requests yet.</p>'; return; }
  wrap.innerHTML = CONTENT.prayers.map(function(p, i) {
    return '<div class="admin-item">' +
      '<div class="admin-item-preview">' + (p.urgent ? '<span class="admin-urgent-badge">URGENT</span> ' : '') + escHtml(p.text.substring(0, 55)) + '…</div>' +
      '<div class="admin-item-actions">' +
      '<button class="admin-item-btn" onclick="editPrayer(' + i + ')">Edit</button>' +
      '<button class="admin-item-btn del" onclick="deletePrayer(' + i + ')">Delete</button>' +
      '</div></div>';
  }).join('');
}
function editPrayer(idx) {
  var p = CONTENT.prayers[idx];
  document.getElementById('pr-edit-idx').value = idx;
  document.getElementById('pr-edit-text').value = p.text;
  document.getElementById('pr-edit-meta').value = p.meta;
  document.getElementById('pr-edit-urgent').checked = p.urgent;
  document.getElementById('admin-prayer-edit').style.display = 'block';
}
function newPrayer() {
  document.getElementById('pr-edit-idx').value = -1;
  document.getElementById('pr-edit-text').value = '';
  document.getElementById('pr-edit-meta').value = '';
  document.getElementById('pr-edit-urgent').checked = false;
  document.getElementById('admin-prayer-edit').style.display = 'block';
}
function savePrayer() {
  var idx = parseInt(document.getElementById('pr-edit-idx').value);
  var item = {
    text: document.getElementById('pr-edit-text').value.trim(),
    meta: document.getElementById('pr-edit-meta').value.trim(),
    urgent: document.getElementById('pr-edit-urgent').checked
  };
  if (!item.text) return;
  if (idx === -1) { CONTENT.prayers.push(item); }
  else { CONTENT.prayers[idx] = item; }
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  renderPrayers();
  renderAdminPrayers();
  document.getElementById('admin-prayer-edit').style.display = 'none';
}
function deletePrayer(idx) {
  if (!confirm('Delete this prayer request?')) return;
  CONTENT.prayers.splice(idx, 1);
  localStorage.setItem('aom_content', JSON.stringify(CONTENT));
  renderPrayers();
  renderAdminPrayers();
}

// ---- User Management ----
function renderAdminUsers() {
  var wrap = document.getElementById('admin-users-list');
  wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;">Loading…</p>';
  fetch('/api/admin/users').then(function(r) { return r.json(); }).then(function(users) {
    if (!users.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No users yet.</p>'; return; }
    wrap.innerHTML = users.map(function(u) {
      var isSelf = currentAdminUser && u.username === currentAdminUser.username;
      var slug = u.username.replace(/[^a-z0-9]/gi, '_');
      return '<div class="admin-item">' +
        '<div class="admin-item-preview"><strong>' + escHtml(u.username) + '</strong>' +
        (u.is_admin ? ' <span style="color:#fbbf24;font-size:11px;margin-left:4px;">ADMIN</span>' : '') +
        (isSelf ? ' <span style="color:#94a3b8;font-size:11px;margin-left:4px;">(you)</span>' : '') +
        (u.contact_email ? '&nbsp;&nbsp;·&nbsp;&nbsp;<span style="color:#94a3b8;font-size:12px;">' + escHtml(u.contact_email) + '</span>' : '') +
        '</div>' +
        '<div class="admin-item-actions">' +
        '<button class="admin-item-btn" onclick="promptSetUserPw(\'' + escHtml(u.username) + '\')">Set Password</button>' +
        (!isSelf ? '<button class="admin-item-btn" onclick="toggleAomAdmin(\'' + escHtml(u.username) + '\')">' + (u.is_admin ? 'Revoke Admin' : 'Make Admin') + '</button>' : '') +
        (!isSelf ? '<button class="admin-item-btn del" onclick="deleteAomUser(\'' + escHtml(u.username) + '\')">Delete</button>' : '') +
        '</div>' +
        '<div id="user-pw-row-' + slug + '" style="display:none;margin-top:8px;">' +
        '<input type="password" id="user-pw-input-' + slug + '" data-username="' + escHtml(u.username) + '" class="custom-input" placeholder="New password" style="width:calc(100% - 80px);display:inline-block;vertical-align:middle;">' +
        '<button class="admin-item-btn" style="margin-left:6px;vertical-align:middle;" onclick="saveUserPw(\'' + escHtml(u.username) + '\')">Set</button>' +
        '</div>' +
        '</div>';
    }).join('');
  }).catch(function() { wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load users.</p>'; });
}

function promptSetUserPw(username) {
  var slug = username.replace(/[^a-z0-9]/gi, '_');
  var row = document.getElementById('user-pw-row-' + slug);
  if (row) row.style.display = row.style.display === 'none' ? 'block' : 'none';
}

function saveUserPw(username) {
  var slug = username.replace(/[^a-z0-9]/gi, '_');
  var pw = document.getElementById('user-pw-input-' + slug).value;
  if (!pw) return;
  fetch('/api/admin/set-password', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: username, password: pw})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) renderAdminUsers();
  });
}

function toggleAomAdmin(username) {
  fetch('/api/admin/toggle-admin', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: username})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok !== undefined) renderAdminUsers();
  });
}

function deleteAomUser(username) {
  if (!confirm('Delete user "' + username + '"?')) return;
  fetch('/api/admin/delete-user', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: username})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) renderAdminUsers();
  });
}

function createAomUser() {
  var username = document.getElementById('new-user-name').value.trim();
  var email    = document.getElementById('new-user-email').value.trim();
  var pw       = document.getElementById('new-user-pw').value;
  var isAdmin  = document.getElementById('new-user-admin').checked;
  var errEl    = document.getElementById('new-user-err');
  errEl.style.display = 'none';
  if (!username || !pw) { errEl.textContent = 'Username and password are required.'; errEl.style.display = 'block'; return; }
  fetch('/api/admin/create-user', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: username, password: pw, contact_email: email, is_admin: isAdmin})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('new-user-name').value = '';
      document.getElementById('new-user-email').value = '';
      document.getElementById('new-user-pw').value = '';
      document.getElementById('new-user-admin').checked = false;
      renderAdminUsers();
      showSaveOk('new-user-ok');
    } else {
      errEl.textContent = d.error || 'Failed to create user.';
      errEl.style.display = 'block';
    }
  });
}

// ---- Keyboard ----
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeDonation(); closeAdmin(); }
});

// ---- Init ----
applyContent();
