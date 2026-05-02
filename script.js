// ---- Settings (loaded from localStorage) ----
var SETTINGS = {
  paypalEmail: '',
  ministryName: 'Action Outreach Ministry',
  phone: '(850) 000-0000',
  contactEmail: 'info@actionoutreachministry.com',
  adminPassword: 'ministry2024'
};

(function loadSettings() {
  var saved = localStorage.getItem('aom_settings');
  if (saved) {
    try { Object.assign(SETTINGS, JSON.parse(saved)); } catch(e) {}
  }
})();

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
  var fundLabels = {
    general: 'General Fund',
    missions: 'Global Missions',
    food: 'Community Feeding Program',
    bibles: 'Bible Distribution',
    youth: 'Youth Ministry'
  };

  // Build PayPal donation URL
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
  // In production, POST to a form backend (Formspree, Netlify Forms, etc.)
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
  document.getElementById('admin-pw').value = '';
  document.getElementById('admin-pw-err').style.display = 'none';
}

function closeAdmin() {
  document.getElementById('admin-overlay').style.display = 'none';
}

document.getElementById('admin-overlay').addEventListener('click', function(e) {
  if (e.target === this) closeAdmin();
});

function checkAdminPw() {
  var pw = document.getElementById('admin-pw').value;
  if (pw === SETTINGS.adminPassword) {
    document.getElementById('admin-login-wrap').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'block';
    // Populate fields
    document.getElementById('admin-paypal-email').value = SETTINGS.paypalEmail || '';
    document.getElementById('admin-ministry-name').value = SETTINGS.ministryName || '';
    document.getElementById('admin-phone').value = SETTINGS.phone || '';
    document.getElementById('admin-contact-email').value = SETTINGS.contactEmail || '';
  } else {
    document.getElementById('admin-pw-err').style.display = 'block';
  }
}

document.getElementById('admin-pw').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') checkAdminPw();
});

function saveAdminSettings() {
  var newPw = document.getElementById('admin-new-pw').value;
  SETTINGS.paypalEmail = document.getElementById('admin-paypal-email').value.trim();
  SETTINGS.ministryName = document.getElementById('admin-ministry-name').value.trim() || 'Action Outreach Ministry';
  SETTINGS.phone = document.getElementById('admin-phone').value.trim();
  SETTINGS.contactEmail = document.getElementById('admin-contact-email').value.trim();
  if (newPw) SETTINGS.adminPassword = newPw;

  localStorage.setItem('aom_settings', JSON.stringify(SETTINGS));
  document.getElementById('admin-save-ok').style.display = 'block';
  setTimeout(function() { document.getElementById('admin-save-ok').style.display = 'none'; }, 2000);
}

// Keyboard close
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeDonation(); closeAdmin(); }
});
