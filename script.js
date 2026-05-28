// ---- State ----
var CONTENT = {};
var currentAdminUser = null;
var _contentLoaded = false;

// ---- Content defaults (used until server responds) ----
var CONTENT_DEFAULTS = {
  settings: {
    ministryName: 'Action Outreach Ministry',
    tagline: 'Reaching the World for Christ',
    location: 'Pensacola, FL',
    address: '',
    phone: '(850) 000-0000',
    contactEmail: 'info@actionoutreachministry.com',
    hours: '',
    notifyEmail: '',
    paypalEmail: '',
    cashapp: '',
    venmo: '',
    zelle: '',
  },
  outreachHeroTitle: 'Reaching Hearts, Changing Lives',
  outreachHeroText: 'Action Outreach Ministry is committed to spreading the Gospel of Jesus Christ through compassionate service, community outreach, and discipleship.',
  aboutTitle: 'About Our Ministry',
  aboutText1: 'Founded on faith and fueled by love, Action Outreach Ministry has been serving the community for over two decades.',
  aboutText2: 'Whether you join us in person, volunteer your time, or support us financially — you are a vital part of this mission.',
  cards: [
    { icon: '🌍', title: 'Global Missions', text: 'We partner with missionaries worldwide to bring hope, healing, and the message of salvation to unreached communities.' },
    { icon: '🍞', title: 'Community Feeding', text: 'Our weekly food pantry serves hundreds of families, meeting physical needs while sharing the love of Christ.' },
    { icon: '📖', title: 'Bible Distribution', text: 'We distribute Bibles and discipleship materials to prisons, shelters, and underserved communities locally and abroad.' },
    { icon: '👨‍👩‍👧', title: 'Family Restoration', text: "Through counseling, support groups, and prayer, we help families find healing and walk in God's purpose." }
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
    { month: 'MAY', day: '18', title: 'Community Prayer Walk', meta: '9:00 AM · Downtown Pensacola · Free', text: 'Join us as we walk through the community, praying over businesses, schools, and families.' },
    { month: 'MAY', day: '25', title: 'Food Pantry & Gospel Outreach', meta: '10:00 AM – 2:00 PM · Ministry Center · Free', text: 'Hundreds of families will receive groceries and hear the Gospel.' },
    { month: 'JUN', day: '7',  title: 'Revival Night', meta: '6:00 PM · Main Sanctuary · Free', text: 'A night of worship, testimonies, and the Word. Come expectant — God moves powerfully when His people gather.' },
    { month: 'JUN', day: '21', title: 'Youth Summer Kickoff', meta: '11:00 AM · Ministry Grounds · Free', text: 'Games, food, and a powerful message for our youth. Bring the whole family.' }
  ],
  prayerHeroTitle: 'Urgent Prayer Requests',
  prayerHeroText: 'We believe in the power of prayer. Submit your request and our prayer team will stand in agreement with you.',
  prayers: [
    { urgent: true,  text: 'Please pray for our missionary team in Haiti who are currently in a dangerous region. Pray for their safety, provision, and boldness.', meta: 'Submitted by Ministry Team · May 1, 2026' },
    { urgent: true,  text: "Pray for Brother James who is in ICU following emergency surgery. His family needs strength and God's healing touch.", meta: 'Submitted by Family · May 2, 2026' },
    { urgent: false, text: 'Pray for our upcoming mission trip to Guatemala — finances, visas, and spiritual preparation for the entire team.', meta: 'Submitted by Missions Dept. · Apr 28, 2026' }
  ]
};

// ---- Init ----
(function init() {
  // Apply defaults immediately so page renders without flash
  CONTENT = JSON.parse(JSON.stringify(CONTENT_DEFAULTS));
  applyContent();

  // Load live content from server
  fetch('/api/content')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      CONTENT = d;
      _contentLoaded = true;
      applyContent();
    })
    .catch(function() { _contentLoaded = true; });

  // Check auth
  fetch('/api/auth/status')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.authenticated && d.is_admin) {
        currentAdminUser = { username: d.username, is_admin: d.is_admin };
        _applyNewsletterNavVisibility();
      }
    })
    .catch(function() {});

  // Password reset link
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
  setTimeout(function() { el.style.display = 'none'; }, 2500);
}

function s(key) {
  return (CONTENT.settings || CONTENT_DEFAULTS.settings)[key] || CONTENT_DEFAULTS.settings[key] || '';
}

// ---- Render Content ----
function applyContent() {
  var name = s('ministryName') || 'Action Outreach Ministry';
  setEl('site-name-header', name);
  setEl('site-tagline', s('tagline'));
  var fn = document.getElementById('site-name-footer');
  if (fn) fn.innerHTML = '&#10011; ' + escHtml(name);
  var loc = s('location');
  var addr = s('address');
  setEl('footer-location', '📍 ' + (addr || loc));
  setEl('footer-phone', '📞 ' + s('phone'));
  setEl('footer-email', '✉ ' + s('contactEmail'));
  var hoursEl = document.getElementById('footer-hours');
  if (hoursEl) {
    if (s('hours')) { hoursEl.textContent = '🕐 ' + s('hours'); hoursEl.style.display = ''; }
    else { hoursEl.style.display = 'none'; }
  }

  setEl('outreach-hero-title', CONTENT.outreachHeroTitle || '');
  setEl('outreach-hero-text', CONTENT.outreachHeroText || '');
  setEl('about-title', CONTENT.aboutTitle || '');
  setEl('about-text-1', CONTENT.aboutText1 || '');
  setEl('about-text-2', CONTENT.aboutText2 || '');
  renderCards();
  setEl('testimonies-hero-title', CONTENT.testimoniesHeroTitle || '');
  setEl('testimonies-hero-text', CONTENT.testimoniesHeroText || '');
  renderTestimonies();
  setEl('events-hero-title', CONTENT.eventsHeroTitle || '');
  setEl('events-hero-text', CONTENT.eventsHeroText || '');
  renderEvents();
  setEl('prayer-hero-title', CONTENT.prayerHeroTitle || '');
  setEl('prayer-hero-text', CONTENT.prayerHeroText || '');
  renderPrayers();

  // Update page title
  document.title = name;
  _applyNewsletterNavVisibility();
}

function renderCards() {
  var grid = document.getElementById('cards-grid');
  if (!grid) return;
  var cards = CONTENT.cards || [];
  grid.innerHTML = cards.map(function(c) {
    return '<div class="info-card"><div class="card-icon">' + c.icon + '</div><h3>' + escHtml(c.title) + '</h3><p>' + escHtml(c.text) + '</p></div>';
  }).join('');
}

function renderTestimonies() {
  var list = document.getElementById('testimony-list');
  if (!list) return;
  var testimonies = CONTENT.testimonies || [];
  list.innerHTML = testimonies.map(function(t) {
    return '<div class="testimony-card"><div class="testimony-quote">"' + escHtml(t.quote) + '"</div><div class="testimony-author">' + escHtml(t.author) + '</div></div>';
  }).join('');
}

function renderEvents() {
  var list = document.getElementById('events-list');
  if (!list) return;
  var events = CONTENT.events || [];
  list.innerHTML = events.map(function(e) {
    return '<div class="event-card">' +
      '<div class="event-date-box"><span class="event-month">' + escHtml(e.month) + '</span><span class="event-day">' + escHtml(e.day) + '</span></div>' +
      '<div class="event-info"><h3>' + escHtml(e.title) + '</h3><p class="event-meta">' + escHtml(e.meta) + '</p><p>' + escHtml(e.text) + '</p></div>' +
      '</div>';
  }).join('');
}

function renderPrayers() {
  var list = document.getElementById('prayer-list');
  if (!list) return;
  var prayers = CONTENT.prayers || [];
  list.innerHTML = prayers.map(function(p) {
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

// ---- Newsletter Modal ----
function openNewsletter() {
  var nl = CONTENT.newsletter || {};
  setEl('nl-title', nl.title || 'Ministry Newsletter');
  var issueEl = document.getElementById('nl-issue');
  var dateEl  = document.getElementById('nl-date');
  if (issueEl) issueEl.textContent = nl.issue || '';
  if (dateEl)  dateEl.textContent  = nl.date  || '';
  var bodyEl = document.getElementById('nl-body');
  if (bodyEl) bodyEl.innerHTML = nl.body || '<p>Newsletter content coming soon.</p>';
  document.getElementById('newsletter-overlay').style.display = 'flex';
}
function closeNewsletter() {
  document.getElementById('newsletter-overlay').style.display = 'none';
}
document.getElementById('newsletter-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeNewsletter();
});

function _applyNewsletterNavVisibility() {
  var btn = document.getElementById('nav-newsletter');
  if (btn) btn.style.display = '';
}

// ---- Contact Info Modal ----
function openContactInfo() {
  var name = s('ministryName') || 'Action Outreach Ministry';
  var addr = s('address') || s('location');
  setEl('ci-ministry-name', name);
  setEl('ci-tagline', s('tagline'));
  setEl('ci-address', addr);
  setEl('ci-phone', s('phone'));
  setEl('ci-contact-email', s('contactEmail'));
  var hoursRow = document.getElementById('ci-hours-row');
  if (s('hours')) {
    setEl('ci-hours', s('hours'));
    if (hoursRow) hoursRow.style.display = '';
  } else {
    if (hoursRow) hoursRow.style.display = 'none';
  }
  document.getElementById('contact-info-overlay').style.display = 'flex';
}
function closeContactInfo() {
  document.getElementById('contact-info-overlay').style.display = 'none';
}
document.getElementById('contact-info-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeContactInfo();
});

// ---- Donation Modal ----
var selectedAmount = 100;
var donationFreq = 'once';
var currentPayMethod = 'paypal';

function openDonation() {
  document.getElementById('donation-overlay').style.display = 'flex';
  document.getElementById('donation-error').style.display = 'none';
  updateGiveBtn();
  renderAllQRs();
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

function renderAllQRs() {
  var methods = [
    { key: 'cashapp', label: 'Cash App', color: '#00d632' },
    { key: 'venmo',   label: 'Venmo',    color: '#3d95ce' },
    { key: 'zelle',   label: 'Zelle',    color: '#6d1ed4' },
    { key: 'paypal',  label: 'PayPal',   color: '#009cde' },
  ];
  var grid = document.getElementById('qr-grid-all');
  if (!grid) return;
  grid.innerHTML = methods.map(function(m) {
    var handle = m.key === 'paypal' ? s('paypalEmail') : s(m.key);
    if (!handle) {
      return '<div class="qr-cell qr-cell-empty"><div class="qr-cell-label" style="color:' + m.color + '">' + m.label + '</div><p class="qr-not-set">Not configured</p></div>';
    }
    var qrUrl = _qrUrl(m.key, handle);
    var display = _qrHandle(m.key, handle);
    return '<div class="qr-cell">' +
      '<div class="qr-cell-label" style="color:' + m.color + '">' + m.label + '</div>' +
      '<img src="https://api.qrserver.com/v1/create-qr-code/?size=130x130&margin=6&data=' + encodeURIComponent(qrUrl) + '" class="qr-cell-img" alt="' + m.label + ' QR">' +
      '<div class="qr-cell-handle">' + escHtml(display) + '</div>' +
      '</div>';
  }).join('');
}

function _qrUrl(method, handle) {
  if (method === 'cashapp') return 'https://cash.app/' + (handle.startsWith('$') ? handle : '$' + handle);
  if (method === 'venmo')   return 'https://venmo.com/' + (handle.startsWith('@') ? handle.slice(1) : handle);
  if (method === 'paypal')  return 'https://www.paypal.com/donate?business=' + encodeURIComponent(handle);
  return handle;
}

function _qrHandle(method, handle) {
  if (method === 'cashapp') return handle.startsWith('$') ? handle : '$' + handle;
  if (method === 'venmo')   return handle.startsWith('@') ? handle : '@' + handle;
  return handle;
}

function processDonation() {
  var errEl = document.getElementById('donation-error');
  errEl.style.display = 'none';
  if (!selectedAmount || selectedAmount < 1) {
    errEl.textContent = 'Please select or enter a donation amount.';
    errEl.style.display = 'block';
    return;
  }
  var paypalEmail = s('paypalEmail');
  if (!paypalEmail) {
    errEl.textContent = 'Donation processing is being set up. Please contact us directly to give.';
    errEl.style.display = 'block';
    return;
  }
  var fund = document.getElementById('fund-select').value;
  var fundLabels = { general:'General Fund', missions:'Global Missions', food:'Community Feeding Program', bibles:'Bible Distribution', youth:'Youth Ministry' };
  var ministryName = s('ministryName') || 'Action Outreach Ministry';
  var params = new URLSearchParams({
    cmd:           donationFreq === 'monthly' ? '_xclick-subscriptions' : '_donations',
    business:      paypalEmail,
    item_name:     ministryName + ' — ' + (fundLabels[fund] || 'General Fund'),
    amount:        selectedAmount.toFixed(2),
    currency_code: 'USD',
    no_note:       '0',
    return:        window.location.href,
    cancel_return: window.location.href,
  });
  if (donationFreq === 'monthly') {
    params.set('a3', selectedAmount.toFixed(2));
    params.set('p3', '1');
    params.set('t3', 'M');
    params.set('src', '1');
  }
  // Record the donation intent
  fetch('/api/donate/record', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ amount: selectedAmount, fund: fund, freq: donationFreq, processor: 'paypal' })
  }).catch(function() {});
  window.open('https://www.paypal.com/donate?' + params.toString(), '_blank');
  closeDonation();
}

// ---- Prayer "I'm Praying" ----
function markPrayed(btn) {
  btn.classList.add('prayed');
  btn.textContent = '🙏 Praying for this';
  btn.disabled = true;
}

// ---- Testimony Form ----
document.getElementById('testimony-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var errEl = document.getElementById('testimony-err');
  errEl.style.display = 'none';
  var payload = {
    name:  document.getElementById('t-name').value.trim() || 'Anonymous',
    email: document.getElementById('t-email').value.trim(),
    quote: document.getElementById('t-body').value.trim(),
  };
  if (!payload.quote) {
    errEl.textContent = 'Please enter your testimony.';
    errEl.style.display = 'block';
    return;
  }
  fetch('/api/testimony', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('testimony-form').style.display = 'none';
      document.getElementById('testimony-thanks').style.display = 'block';
    } else {
      errEl.textContent = d.error || 'Submission failed. Please try again.';
      errEl.style.display = 'block';
    }
  }).catch(function() {
    errEl.textContent = 'Network error. Please try again.';
    errEl.style.display = 'block';
  });
});

// ---- Prayer Form ----
document.getElementById('prayer-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var errEl = document.getElementById('prayer-err');
  errEl.style.display = 'none';
  var payload = {
    name:   document.getElementById('p-name').value.trim() || 'Anonymous',
    email:  document.getElementById('p-email').value.trim(),
    text:   document.getElementById('p-body').value.trim(),
    urgent: document.getElementById('p-urgent').checked,
  };
  if (!payload.text) {
    errEl.textContent = 'Please enter your prayer request.';
    errEl.style.display = 'block';
    return;
  }
  fetch('/api/prayer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('prayer-form').style.display = 'none';
      document.getElementById('prayer-thanks').style.display = 'block';
    } else {
      errEl.textContent = d.error || 'Submission failed. Please try again.';
      errEl.style.display = 'block';
    }
  }).catch(function() {
    errEl.textContent = 'Network error. Please try again.';
    errEl.style.display = 'block';
  });
});

// ---- Contact Form ----
document.getElementById('contact-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var errEl = document.getElementById('contact-err');
  errEl.style.display = 'none';
  var payload = {
    name:    document.getElementById('cf-name').value.trim(),
    email:   document.getElementById('cf-email').value.trim(),
    subject: document.getElementById('cf-subject').value.trim(),
    message: document.getElementById('cf-message').value.trim(),
  };
  fetch('/api/contact', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('contact-form').style.display = 'none';
      document.getElementById('contact-thanks').style.display = 'block';
    } else {
      errEl.textContent = d.error || 'Could not send message. Please try again.';
      errEl.style.display = 'block';
    }
  }).catch(function() {
    errEl.textContent = 'Network error. Please check your connection and try again.';
    errEl.style.display = 'block';
  });
});

// ---- Info Request Form ----
document.getElementById('info-request-form').addEventListener('submit', function(e) {
  e.preventDefault();
  var errEl = document.getElementById('info-request-err');
  errEl.style.display = 'none';
  var interests = [];
  if (document.getElementById('ir-c1').checked) interests.push('General Ministry Overview');
  if (document.getElementById('ir-c2').checked) interests.push('Volunteer Opportunities');
  if (document.getElementById('ir-c3').checked) interests.push('Mission Trips');
  if (document.getElementById('ir-c4').checked) interests.push('Prayer Newsletter');
  if (document.getElementById('ir-c5').checked) interests.push('How to Give / Support the Mission');
  if (document.getElementById('ir-c6').checked) interests.push('Community Events');
  var payload = {
    first:     document.getElementById('ir-first').value.trim(),
    last:      document.getElementById('ir-last').value.trim(),
    street:    document.getElementById('ir-street').value.trim(),
    city:      document.getElementById('ir-city').value.trim(),
    state:     document.getElementById('ir-state').value.trim(),
    zip:       document.getElementById('ir-zip').value.trim(),
    email:     document.getElementById('ir-email').value.trim(),
    phone:     document.getElementById('ir-phone').value.trim(),
    interests: interests,
    comments:  document.getElementById('ir-comments').value.trim(),
  };
  fetch('/api/info-request', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      document.getElementById('info-request-form').style.display = 'none';
      document.getElementById('info-request-thanks').style.display = 'block';
    } else {
      errEl.textContent = d.error || 'Submission failed. Please try again.';
      errEl.style.display = 'block';
    }
  }).catch(function() {
    errEl.textContent = 'Network error. Please check your connection and try again.';
    errEl.style.display = 'block';
  });
});

// ---- Admin Modal ----
function openAdmin() {
  document.getElementById('admin-overlay').style.display = 'flex';
  if (currentAdminUser) {
    document.getElementById('admin-login-wrap').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'block';
    var bar = document.getElementById('admin-logged-in-bar');
    if (bar) bar.textContent = '✓ Logged in as ' + currentAdminUser.username;
    adminTab('settings');
  } else {
    document.getElementById('admin-login-wrap').style.display = 'block';
    document.getElementById('admin-panel').style.display = 'none';
    document.getElementById('admin-user').value = '';
    document.getElementById('admin-pw').value = '';
    document.getElementById('admin-pw-err').style.display = 'none';
    document.getElementById('admin-reset-wrap').style.display = 'none';
    document.getElementById('admin-reset-err').style.display = 'none';
    document.getElementById('admin-reset-ok').style.display = 'none';
  }
}
function closeAdmin() {
  document.getElementById('admin-overlay').style.display = 'none';
}
document.getElementById('admin-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeAdmin();
});

function checkAdminPw() {
  var user = document.getElementById('admin-user').value.trim();
  var pw   = document.getElementById('admin-pw').value;
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
    document.getElementById('admin-pw-err').style.display = 'block';
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
  var code = document.getElementById('admin-recovery-code').value.trim();
  var user = document.getElementById('admin-reset-user').value.trim();
  var pw   = document.getElementById('admin-reset-pw').value;
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
    if (d.has_brevo_key) document.getElementById('smtp-brevo-key').placeholder = '(saved)';
  }).catch(function() {});
}
function saveSmtpConfig() {
  var body = {
    host:          document.getElementById('smtp-host').value.trim(),
    port:          document.getElementById('smtp-port').value || '587',
    username:      document.getElementById('smtp-user').value.trim(),
    from_name:     document.getElementById('smtp-from-name').value.trim(),
    tls:           document.getElementById('smtp-tls').value,
    password:      document.getElementById('smtp-pass').value,
    brevo_api_key: document.getElementById('smtp-brevo-key').value.trim()
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
  msgEl.style.display = 'block';
  msgEl.style.color = '#f0c040';
  msgEl.textContent = 'Sending…';
  fetch('/api/admin/smtp-test', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}' })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) {
        msgEl.style.color = '#86efac';
        msgEl.textContent = 'Test email sent to ' + d.sent_to;
      } else {
        msgEl.style.color = '#f87171';
        msgEl.textContent = d.error || 'Failed to send test email.';
      }
    })
    .catch(function(e) {
      msgEl.style.color = '#f87171';
      msgEl.textContent = 'Request failed: ' + e.message;
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
  if (name === 'settings')    { populateSettingsTab(); loadSmtpConfig(); loadUserCount(); }
  if (name === 'content')     { populateContentTab(); }
  if (name === 'testimonies') { renderAdminTestimonies(); loadAdminPendingTestimonies(); }
  if (name === 'events')      { renderAdminEvents(); }
  if (name === 'prayer')      { renderAdminPrayers(); loadAdminPendingPrayers(); }
  if (name === 'newsletter')  { populateNewsletterTab(); }
  if (name === 'contacts')    { renderAdminContacts(); }
  if (name === 'donations')   { renderAdminDonations(); populateDonationsSetup(); }
  if (name === 'users')       { renderAdminUsers(); }
  if (name === 'inforequests'){ renderAdminInfoRequests(); }
}

function loadUserCount() {
  fetch('/api/admin/users').then(function(r) { return r.json(); }).then(function(users) {
    var el = document.getElementById('settings-user-count');
    if (el) el.textContent = users.length + ' user' + (users.length === 1 ? '' : 's') + ' registered';
  }).catch(function() {});
}

// ---- Settings Tab ----
function populateSettingsTab() {
  var st = CONTENT.settings || {};
  document.getElementById('admin-ministry-name').value = st.ministryName || '';
  document.getElementById('admin-tagline').value       = st.tagline || '';
  document.getElementById('admin-location').value      = st.location || '';
  document.getElementById('admin-address').value       = st.address || '';
  document.getElementById('admin-phone').value         = st.phone || '';
  document.getElementById('admin-contact-email').value = st.contactEmail || '';
  document.getElementById('admin-hours').value         = st.hours || '';
  document.getElementById('admin-notify-email').value  = st.notifyEmail || '';
  document.getElementById('admin-paypal-email').value  = st.paypalEmail || '';
  document.getElementById('admin-cashapp').value       = st.cashapp || '';
  document.getElementById('admin-venmo').value         = st.venmo || '';
  document.getElementById('admin-zelle').value         = st.zelle || '';
  document.getElementById('admin-new-pw').value  = '';
  document.getElementById('admin-new-pw2').value = '';
}

function saveAdminSettings() {
  var settings = {
    ministryName: document.getElementById('admin-ministry-name').value.trim() || 'Action Outreach Ministry',
    tagline:      document.getElementById('admin-tagline').value.trim(),
    location:     document.getElementById('admin-location').value.trim(),
    address:      document.getElementById('admin-address').value.trim(),
    phone:        document.getElementById('admin-phone').value.trim(),
    contactEmail: document.getElementById('admin-contact-email').value.trim(),
    hours:        document.getElementById('admin-hours').value.trim(),
    notifyEmail:  document.getElementById('admin-notify-email').value.trim(),
    paypalEmail:  document.getElementById('admin-paypal-email').value.trim(),
    cashapp:      document.getElementById('admin-cashapp').value.trim(),
    venmo:        document.getElementById('admin-venmo').value.trim(),
    zelle:        document.getElementById('admin-zelle').value.trim(),
  };
  fetch('/api/admin/content', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({settings: settings})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      if (!CONTENT.settings) CONTENT.settings = {};
      Object.assign(CONTENT.settings, settings);
      applyContent();
      showSaveOk('admin-save-ok');
    }
  }).catch(function() {});
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
      document.getElementById('admin-new-pw').value  = '';
      document.getElementById('admin-new-pw2').value = '';
      showSaveOk('admin-creds-ok');
    }
  });
}

// ---- Content Tab ----
function populateContentTab() {
  document.getElementById('ct-outreach-title').value = CONTENT.outreachHeroTitle || '';
  document.getElementById('ct-outreach-text').value  = CONTENT.outreachHeroText  || '';
  document.getElementById('ct-about-title').value    = CONTENT.aboutTitle  || '';
  document.getElementById('ct-about-1').value        = CONTENT.aboutText1  || '';
  document.getElementById('ct-about-2').value        = CONTENT.aboutText2  || '';
  document.getElementById('ct-test-title').value     = CONTENT.testimoniesHeroTitle || '';
  document.getElementById('ct-test-text').value      = CONTENT.testimoniesHeroText  || '';
  document.getElementById('ct-events-title').value   = CONTENT.eventsHeroTitle || '';
  document.getElementById('ct-events-text').value    = CONTENT.eventsHeroText  || '';
  document.getElementById('ct-prayer-title').value   = CONTENT.prayerHeroTitle || '';
  document.getElementById('ct-prayer-text').value    = CONTENT.prayerHeroText  || '';
  (CONTENT.cards || []).forEach(function(c, i) {
    if (document.getElementById('ct-card-icon-' + i)) {
      document.getElementById('ct-card-icon-' + i).value  = c.icon  || '';
      document.getElementById('ct-card-title-' + i).value = c.title || '';
      document.getElementById('ct-card-text-' + i).value  = c.text  || '';
    }
  });
}

function saveContentTab() {
  var cards = (CONTENT.cards || []).map(function(c, i) {
    return {
      icon:  document.getElementById('ct-card-icon-' + i)  ? document.getElementById('ct-card-icon-' + i).value.trim()  : c.icon,
      title: document.getElementById('ct-card-title-' + i) ? document.getElementById('ct-card-title-' + i).value.trim() : c.title,
      text:  document.getElementById('ct-card-text-' + i)  ? document.getElementById('ct-card-text-' + i).value.trim()  : c.text,
    };
  });
  var update = {
    outreachHeroTitle:    document.getElementById('ct-outreach-title').value.trim(),
    outreachHeroText:     document.getElementById('ct-outreach-text').value.trim(),
    aboutTitle:           document.getElementById('ct-about-title').value.trim(),
    aboutText1:           document.getElementById('ct-about-1').value.trim(),
    aboutText2:           document.getElementById('ct-about-2').value.trim(),
    testimoniesHeroTitle: document.getElementById('ct-test-title').value.trim(),
    testimoniesHeroText:  document.getElementById('ct-test-text').value.trim(),
    eventsHeroTitle:      document.getElementById('ct-events-title').value.trim(),
    eventsHeroText:       document.getElementById('ct-events-text').value.trim(),
    prayerHeroTitle:      document.getElementById('ct-prayer-title').value.trim(),
    prayerHeroText:       document.getElementById('ct-prayer-text').value.trim(),
    cards:                cards,
  };
  fetch('/api/admin/content', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(update)
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      Object.assign(CONTENT, update);
      applyContent();
      showSaveOk('ct-save-ok');
    }
  }).catch(function() {});
}

// ---- Pending Testimonies (admin) ----
function loadAdminPendingTestimonies() {
  var wrap = document.getElementById('admin-pending-testimonies');
  if (!wrap) return;
  fetch('/api/admin/pending').then(function(r) { return r.json(); }).then(function(d) {
    var items = (d.testimonies || []);
    if (!items.length) {
      wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;margin-bottom:8px;">No pending submissions.</p>';
      return;
    }
    wrap.innerHTML = items.map(function(item) {
      var date = new Date(item.timestamp * 1000).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
      return '<div class="admin-pending-item">' +
        '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">' +
          '<strong style="font-size:13px;color:#fff;">' + escHtml(item.name) + '</strong>' +
          '<span style="font-size:11px;color:#94a3b8;">' + date + '</span>' +
        '</div>' +
        '<div style="font-size:13px;color:rgba(255,255,255,0.7);margin-bottom:8px;font-style:italic;">"' + escHtml(item.quote.substring(0,120)) + (item.quote.length > 120 ? '…' : '') + '"</div>' +
        (item.email ? '<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">✉ ' + escHtml(item.email) + '</div>' : '') +
        '<div style="display:flex;gap:6px;">' +
          '<button class="admin-item-btn" style="background:rgba(134,239,172,0.15);border-color:rgba(134,239,172,0.4);color:#86efac;" onclick="approveTestimony(\'' + item.id + '\')">✓ Approve & Publish</button>' +
          '<button class="admin-item-btn del" onclick="rejectTestimony(\'' + item.id + '\')">✕ Reject</button>' +
        '</div></div>';
    }).join('');
  }).catch(function() {
    wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load.</p>';
  });
}

function approveTestimony(id) {
  fetch('/api/admin/testimony/approve', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      // Refresh live content and admin list
      fetch('/api/content').then(function(r) { return r.json(); }).then(function(c) {
        CONTENT = c; applyContent();
      });
      loadAdminPendingTestimonies();
      renderAdminTestimonies();
    }
  });
}

function rejectTestimony(id) {
  if (!confirm('Reject and delete this testimony submission?')) return;
  fetch('/api/admin/testimony/reject', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) loadAdminPendingTestimonies();
  });
}

// ---- Pending Prayers (admin) ----
function loadAdminPendingPrayers() {
  var wrap = document.getElementById('admin-pending-prayers');
  if (!wrap) return;
  fetch('/api/admin/pending').then(function(r) { return r.json(); }).then(function(d) {
    var items = (d.prayers || []);
    if (!items.length) {
      wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;margin-bottom:8px;">No pending submissions.</p>';
      return;
    }
    wrap.innerHTML = items.map(function(item) {
      var date = new Date(item.timestamp * 1000).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
      return '<div class="admin-pending-item">' +
        '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">' +
          '<strong style="font-size:13px;color:#fff;">' + escHtml(item.name) + (item.urgent ? ' <span style="background:#dc2626;color:#fff;font-size:10px;padding:1px 5px;border-radius:3px;margin-left:4px;">URGENT</span>' : '') + '</strong>' +
          '<span style="font-size:11px;color:#94a3b8;">' + date + '</span>' +
        '</div>' +
        '<div style="font-size:13px;color:rgba(255,255,255,0.7);margin-bottom:8px;">' + escHtml(item.text.substring(0,120)) + (item.text.length > 120 ? '…' : '') + '</div>' +
        (item.email ? '<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">✉ ' + escHtml(item.email) + '</div>' : '') +
        '<div style="display:flex;gap:6px;">' +
          '<button class="admin-item-btn" style="background:rgba(134,239,172,0.15);border-color:rgba(134,239,172,0.4);color:#86efac;" onclick="approvePrayer(\'' + item.id + '\')">✓ Approve & Publish</button>' +
          '<button class="admin-item-btn del" onclick="rejectPrayer(\'' + item.id + '\')">✕ Reject</button>' +
        '</div></div>';
    }).join('');
  }).catch(function() {
    wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load.</p>';
  });
}

function approvePrayer(id) {
  fetch('/api/admin/prayer/approve', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      fetch('/api/content').then(function(r) { return r.json(); }).then(function(c) {
        CONTENT = c; applyContent();
      });
      loadAdminPendingPrayers();
      renderAdminPrayers();
    }
  });
}

function rejectPrayer(id) {
  if (!confirm('Reject and delete this prayer request submission?')) return;
  fetch('/api/admin/prayer/reject', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) loadAdminPendingPrayers();
  });
}

// ---- Testimonies CRUD ----
function renderAdminTestimonies() {
  var wrap = document.getElementById('admin-testimonies-list');
  var testimonies = CONTENT.testimonies || [];
  if (!testimonies.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No testimonies published yet.</p>'; return; }
  wrap.innerHTML = testimonies.map(function(t, i) {
    return '<div class="admin-item">' +
      '<div class="admin-item-preview">"' + escHtml(t.quote.substring(0, 55)) + '…"</div>' +
      '<div class="admin-item-actions">' +
      '<button class="admin-item-btn" onclick="editTestimony(' + i + ')">Edit</button>' +
      '<button class="admin-item-btn del" onclick="deleteTestimony(' + i + ')">Delete</button>' +
      '</div></div>';
  }).join('');
}

function editTestimony(idx) {
  var t = (CONTENT.testimonies || [])[idx];
  if (!t) return;
  document.getElementById('t-edit-idx').value   = idx;
  document.getElementById('t-edit-quote').value  = t.quote;
  document.getElementById('t-edit-author').value = t.author;
  document.getElementById('admin-testimony-edit').style.display = 'block';
}
function newTestimony() {
  document.getElementById('t-edit-idx').value   = -1;
  document.getElementById('t-edit-quote').value  = '';
  document.getElementById('t-edit-author').value = '';
  document.getElementById('admin-testimony-edit').style.display = 'block';
}
function saveTestimony() {
  var idx    = parseInt(document.getElementById('t-edit-idx').value);
  var quote  = document.getElementById('t-edit-quote').value.trim();
  var author = document.getElementById('t-edit-author').value.trim();
  if (!quote) return;
  var testimonies = (CONTENT.testimonies || []).slice();
  if (idx === -1) { testimonies.push({quote: quote, author: author}); }
  else { testimonies[idx] = {quote: quote, author: author}; }
  fetch('/api/admin/content', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({testimonies: testimonies})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      CONTENT.testimonies = testimonies;
      renderTestimonies();
      renderAdminTestimonies();
      document.getElementById('admin-testimony-edit').style.display = 'none';
    }
  });
}
function deleteTestimony(idx) {
  if (!confirm('Delete this testimony?')) return;
  var testimonies = (CONTENT.testimonies || []).slice();
  testimonies.splice(idx, 1);
  fetch('/api/admin/content', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({testimonies: testimonies})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      CONTENT.testimonies = testimonies;
      renderTestimonies();
      renderAdminTestimonies();
    }
  });
}

// ---- Events CRUD ----
function renderAdminEvents() {
  var wrap = document.getElementById('admin-events-list');
  var events = CONTENT.events || [];
  if (!events.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No events yet.</p>'; return; }
  wrap.innerHTML = events.map(function(e, i) {
    return '<div class="admin-item">' +
      '<div class="admin-item-preview"><strong>' + escHtml(e.month) + ' ' + escHtml(e.day) + '</strong> — ' + escHtml(e.title) + '</div>' +
      '<div class="admin-item-actions">' +
      '<button class="admin-item-btn" onclick="editEvent(' + i + ')">Edit</button>' +
      '<button class="admin-item-btn del" onclick="deleteEvent(' + i + ')">Delete</button>' +
      '</div></div>';
  }).join('');
}
function editEvent(idx) {
  var e = (CONTENT.events || [])[idx];
  if (!e) return;
  document.getElementById('ev-edit-idx').value   = idx;
  document.getElementById('ev-edit-month').value = e.month;
  document.getElementById('ev-edit-day').value   = e.day;
  document.getElementById('ev-edit-title').value = e.title;
  document.getElementById('ev-edit-meta').value  = e.meta;
  document.getElementById('ev-edit-text').value  = e.text;
  document.getElementById('admin-event-edit').style.display = 'block';
}
function newEvent() {
  document.getElementById('ev-edit-idx').value = -1;
  ['ev-edit-month','ev-edit-day','ev-edit-title','ev-edit-meta','ev-edit-text'].forEach(function(id) { document.getElementById(id).value = ''; });
  document.getElementById('admin-event-edit').style.display = 'block';
}
function saveEvent() {
  var idx  = parseInt(document.getElementById('ev-edit-idx').value);
  var item = {
    month: document.getElementById('ev-edit-month').value.trim().toUpperCase(),
    day:   document.getElementById('ev-edit-day').value.trim(),
    title: document.getElementById('ev-edit-title').value.trim(),
    meta:  document.getElementById('ev-edit-meta').value.trim(),
    text:  document.getElementById('ev-edit-text').value.trim()
  };
  if (!item.title) return;
  var events = (CONTENT.events || []).slice();
  if (idx === -1) { events.push(item); }
  else { events[idx] = item; }
  fetch('/api/admin/content', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({events: events})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      CONTENT.events = events;
      renderEvents();
      renderAdminEvents();
      document.getElementById('admin-event-edit').style.display = 'none';
    }
  });
}
function deleteEvent(idx) {
  if (!confirm('Delete this event?')) return;
  var events = (CONTENT.events || []).slice();
  events.splice(idx, 1);
  fetch('/api/admin/content', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({events: events})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) { CONTENT.events = events; renderEvents(); renderAdminEvents(); }
  });
}

// ---- Prayer CRUD ----
function renderAdminPrayers() {
  var wrap = document.getElementById('admin-prayers-list');
  var prayers = CONTENT.prayers || [];
  if (!prayers.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No prayer requests published yet.</p>'; return; }
  wrap.innerHTML = prayers.map(function(p, i) {
    return '<div class="admin-item">' +
      '<div class="admin-item-preview">' + (p.urgent ? '<span class="admin-urgent-badge">URGENT</span> ' : '') + escHtml(p.text.substring(0, 55)) + '…</div>' +
      '<div class="admin-item-actions">' +
      '<button class="admin-item-btn" onclick="editPrayer(' + i + ')">Edit</button>' +
      '<button class="admin-item-btn del" onclick="deletePrayer(' + i + ')">Delete</button>' +
      '</div></div>';
  }).join('');
}
function editPrayer(idx) {
  var p = (CONTENT.prayers || [])[idx];
  if (!p) return;
  document.getElementById('pr-edit-idx').value    = idx;
  document.getElementById('pr-edit-text').value   = p.text;
  document.getElementById('pr-edit-meta').value   = p.meta;
  document.getElementById('pr-edit-urgent').checked = p.urgent;
  document.getElementById('admin-prayer-edit').style.display = 'block';
}
function newPrayer() {
  document.getElementById('pr-edit-idx').value      = -1;
  document.getElementById('pr-edit-text').value      = '';
  document.getElementById('pr-edit-meta').value      = '';
  document.getElementById('pr-edit-urgent').checked  = false;
  document.getElementById('admin-prayer-edit').style.display = 'block';
}
function savePrayer() {
  var idx  = parseInt(document.getElementById('pr-edit-idx').value);
  var item = {
    text:   document.getElementById('pr-edit-text').value.trim(),
    meta:   document.getElementById('pr-edit-meta').value.trim(),
    urgent: document.getElementById('pr-edit-urgent').checked
  };
  if (!item.text) return;
  var prayers = (CONTENT.prayers || []).slice();
  if (idx === -1) { prayers.push(item); }
  else { prayers[idx] = item; }
  fetch('/api/admin/content', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prayers: prayers})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      CONTENT.prayers = prayers;
      renderPrayers();
      renderAdminPrayers();
      document.getElementById('admin-prayer-edit').style.display = 'none';
    }
  });
}
function deletePrayer(idx) {
  if (!confirm('Delete this prayer request?')) return;
  var prayers = (CONTENT.prayers || []).slice();
  prayers.splice(idx, 1);
  fetch('/api/admin/content', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prayers: prayers})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) { CONTENT.prayers = prayers; renderPrayers(); renderAdminPrayers(); }
  });
}

// ---- Contacts Admin ----
function renderAdminContacts() {
  var wrap = document.getElementById('admin-contacts-list');
  wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;">Loading…</p>';
  fetch('/api/admin/contacts').then(function(r) { return r.json(); }).then(function(items) {
    if (!Array.isArray(items) || !items.length) {
      wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No contact messages yet.</p>';
      return;
    }
    wrap.innerHTML = items.map(function(c) {
      var date = new Date(c.timestamp * 1000).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric', hour:'2-digit', minute:'2-digit'});
      return '<div class="admin-item" style="flex-direction:column;align-items:flex-start;gap:4px;">' +
        '<div style="display:flex;justify-content:space-between;width:100%;">' +
          '<strong style="font-size:13px;">' + escHtml(c.name) + '</strong>' +
          '<span style="font-size:11px;color:#94a3b8;">' + date + '</span>' +
        '</div>' +
        '<div style="font-size:12px;color:#86b4f0;">✉ ' + escHtml(c.email) + '</div>' +
        '<div style="font-size:13px;color:#f0c040;font-weight:600;">' + escHtml(c.subject) + '</div>' +
        '<div style="font-size:13px;color:rgba(255,255,255,0.7);">' + escHtml(c.message) + '</div>' +
        '</div>';
    }).join('');
  }).catch(function() {
    wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load contacts.</p>';
  });
}

// ---- Donations Admin ----
function renderAdminDonations() {
  var wrap = document.getElementById('admin-donations-list');
  wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;">Loading…</p>';
  Promise.all([
    fetch('/api/admin/donations').then(function(r) { return r.json(); }),
    fetch('/api/admin/transactions').then(function(r) { return r.json(); })
  ]).then(function(results) {
    var confirmed = Array.isArray(results[0]) ? results[0] : [];
    var intents   = Array.isArray(results[1]) ? results[1] : [];
    var html = '';

    // Confirmed (PayPal IPN verified)
    var total = confirmed.reduce(function(s, d) { return s + (d.amount || 0); }, 0);
    html += '<div style="font-size:12px;font-weight:700;color:#86efac;letter-spacing:.5px;text-transform:uppercase;margin-bottom:8px;">✓ Confirmed via PayPal</div>';
    if (confirmed.length) {
      html += '<div style="background:rgba(134,239,172,0.1);border:1px solid rgba(134,239,172,0.25);border-radius:8px;padding:10px 14px;margin-bottom:10px;font-size:14px;color:#86efac;font-weight:600;">$' + total.toFixed(2) + ' confirmed across ' + confirmed.length + ' payment' + (confirmed.length===1?'':'s') + '</div>';
      html += confirmed.slice().reverse().map(function(d) {
        var date = new Date(d.timestamp * 1000).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
        return '<div class="admin-item">' +
          '<div class="admin-item-preview"><strong>$' + (d.amount||0).toFixed(2) + (d.freq==='monthly'?'/mo':'') + '</strong>' +
          (d.donor_name ? ' · ' + escHtml(d.donor_name) : '') +
          (d.donor_email ? ' &lt;' + escHtml(d.donor_email) + '&gt;' : '') +
          ' · ' + escHtml(d.fund||'General Fund') + '</div>' +
          '<div style="font-size:11px;color:#94a3b8;flex-shrink:0;">' + date + '</div></div>';
      }).join('');
    } else {
      html += '<p style="font-size:13px;color:rgba(255,255,255,0.35);margin-bottom:14px;">No confirmed PayPal donations yet. Configure IPN in your PayPal account to enable this.</p>';
    }

    // Intents (user clicked Give button)
    if (intents.length) {
      html += '<div style="font-size:12px;font-weight:700;color:#94a3b8;letter-spacing:.5px;text-transform:uppercase;margin:16px 0 8px;">Donation intents (clicked Give)</div>';
      html += intents.slice().reverse().map(function(t) {
        var date = new Date(t.timestamp * 1000).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
        return '<div class="admin-item" style="opacity:.7">' +
          '<div class="admin-item-preview">$' + (t.amount||0).toFixed(2) + (t.freq==='monthly'?'/mo':'') + ' · ' + escHtml(t.fund||'general') + '</div>' +
          '<div style="font-size:11px;color:#94a3b8;flex-shrink:0;">' + date + '</div></div>';
      }).join('');
    }

    wrap.innerHTML = html || '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No records yet.</p>';
  }).catch(function() {
    wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load donations.</p>';
  });
}

// ---- Info Requests Admin ----
function renderAdminInfoRequests() {
  var wrap = document.getElementById('admin-inforeq-list');
  wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;">Loading…</p>';
  fetch('/api/admin/info-requests').then(function(r) { return r.json(); }).then(function(reqs) {
    if (!Array.isArray(reqs) || !reqs.length) {
      wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No requests yet.</p>';
      return;
    }
    wrap.innerHTML = reqs.map(function(r) {
      var date = new Date(r.timestamp * 1000).toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
      var interests = (r.interests && r.interests.length) ? r.interests.join(', ') : '—';
      return '<div class="admin-item" style="flex-direction:column;align-items:flex-start;gap:4px;">' +
        '<div style="display:flex;justify-content:space-between;width:100%;align-items:center;">' +
          '<div class="admin-item-preview" style="font-weight:700;">' + escHtml(r.name) + '</div>' +
          '<div style="font-size:11px;color:#94a3b8;">' + date + '</div>' +
        '</div>' +
        '<div style="font-size:12px;color:#cbd5e1;">📍 ' + escHtml(r.address) + '</div>' +
        (r.email ? '<div style="font-size:12px;color:#94a3b8;">✉ ' + escHtml(r.email) + '</div>' : '') +
        (r.phone ? '<div style="font-size:12px;color:#94a3b8;">📞 ' + escHtml(r.phone) + '</div>' : '') +
        '<div style="font-size:12px;color:#f0c040;margin-top:2px;">Interested in: ' + escHtml(interests) + '</div>' +
        (r.comments ? '<div style="font-size:12px;color:#94a3b8;margin-top:2px;font-style:italic;">"' + escHtml(r.comments) + '"</div>' : '') +
        '</div>';
    }).join('');
  }).catch(function() {
    wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load requests.</p>';
  });
}

// ---- User Management ----
function renderAdminUsers() {
  var wrap = document.getElementById('admin-users-list');
  wrap.innerHTML = '<p style="color:#94a3b8;font-size:13px;">Loading…</p>';
  fetch('/api/admin/users').then(function(r) { return r.json(); }).then(function(users) {
    if (!users.length) { wrap.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:13px;">No users yet.</p>'; return; }
    wrap.innerHTML = users.map(function(u) {
      var isSelf = currentAdminUser && u.username === currentAdminUser.username;
      var slug   = u.username.replace(/[^a-z0-9]/gi, '_');
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
        '<input type="password" id="user-pw-input-' + slug + '" class="custom-input" placeholder="New password" style="width:calc(100% - 80px);display:inline-block;vertical-align:middle;">' +
        '<button class="admin-item-btn" style="margin-left:6px;vertical-align:middle;" onclick="saveUserPw(\'' + escHtml(u.username) + '\')">Set</button>' +
        '</div>' +
        '</div>';
    }).join('');
  }).catch(function() { wrap.innerHTML = '<p style="color:#f87171;font-size:13px;">Failed to load users.</p>'; });
}

function promptSetUserPw(username) {
  var slug = username.replace(/[^a-z0-9]/gi, '_');
  var row  = document.getElementById('user-pw-row-' + slug);
  if (row) row.style.display = row.style.display === 'none' ? 'block' : 'none';
}

function saveUserPw(username) {
  var slug = username.replace(/[^a-z0-9]/gi, '_');
  var pw   = document.getElementById('user-pw-input-' + slug).value;
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
      document.getElementById('new-user-name').value  = '';
      document.getElementById('new-user-email').value = '';
      document.getElementById('new-user-pw').value    = '';
      document.getElementById('new-user-admin').checked = false;
      renderAdminUsers();
      showSaveOk('new-user-ok');
    } else {
      errEl.textContent = d.error || 'Failed to create user.';
      errEl.style.display = 'block';
    }
  });
}

// ---- Donations Setup ----
function populateDonationsSetup() {
  var el = document.getElementById('ipn-url-display');
  if (el) el.textContent = window.location.origin + '/api/paypal/ipn';
}

function copyIpnUrl() {
  var url = window.location.origin + '/api/paypal/ipn';
  navigator.clipboard.writeText(url).then(function() {
    var btn = document.querySelector('.paypal-copy-btn');
    if (btn) { btn.textContent = 'Copied!'; setTimeout(function() { btn.textContent = 'Copy'; }, 2000); }
  });
}

// ---- Newsletter Admin Tab ----
function populateNewsletterTab() {
  var nl = CONTENT.newsletter || {};
  var vis = document.getElementById('nl-admin-visible');
  var tit = document.getElementById('nl-admin-title');
  var iss = document.getElementById('nl-admin-issue');
  var dat = document.getElementById('nl-admin-date');
  var bod = document.getElementById('nl-admin-body');
  if (vis) vis.checked = !!nl.visible;
  if (tit) tit.value   = nl.title || '';
  if (iss) iss.value   = nl.issue || '';
  if (dat) dat.value   = nl.date  || '';
  if (bod) bod.value   = nl.body  || '';
}

function saveNewsletter() {
  var nl = {
    visible: document.getElementById('nl-admin-visible').checked,
    title:   document.getElementById('nl-admin-title').value.trim(),
    issue:   document.getElementById('nl-admin-issue').value.trim(),
    date:    document.getElementById('nl-admin-date').value.trim(),
    body:    document.getElementById('nl-admin-body').value,
  };
  fetch('/api/admin/content', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({newsletter: nl})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) {
      CONTENT.newsletter = nl;
      _applyNewsletterNavVisibility();
      showSaveOk('nl-save-ok');
    }
  }).catch(function() {});
}

function previewNewsletter() {
  var nl = {
    visible: true,
    title:   document.getElementById('nl-admin-title').value.trim() || 'Ministry Newsletter',
    issue:   document.getElementById('nl-admin-issue').value.trim(),
    date:    document.getElementById('nl-admin-date').value.trim(),
    body:    document.getElementById('nl-admin-body').value,
  };
  var saved = CONTENT.newsletter;
  CONTENT.newsletter = nl;
  openNewsletter();
  CONTENT.newsletter = saved;
}

// ---- Keyboard ----
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeDonation(); closeAdmin(); closeContactInfo(); closeNewsletter(); }
});
