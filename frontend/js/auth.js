var supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// --- Screen management ---

function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(function(s) {
    s.classList.remove('active');
  });
  document.getElementById(screenId).classList.add('active');
}

// --- State ---

var currentPhone = '';
var resendTimer = null;

// --- OTP flow ---

async function sendOtp(phone) {
  var digits = phone.replace(/\D/g, '');
  if (digits.length === 11 && digits.startsWith('01')) {
    digits = '880' + digits.substring(1);
  }
  if (!/^880\d{10}$/.test(digits)) {
    showError('login-error', 'সঠিক ফোন নম্বর দিন (01XXXXXXXXX)');
    return;
  }

  currentPhone = '+' + digits;
  var btn = document.getElementById('btn-send-otp');
  btn.disabled = true;
  btn.textContent = 'পাঠানো হচ্ছে...';
  hideError('login-error');

  try {
    var result = await supabaseClient.auth.signInWithOtp({ phone: currentPhone });
    if (result.error) throw result.error;
    showScreen('screen-otp');
    startResendTimer();
  } catch (err) {
    showError('login-error', err.message || 'OTP পাঠানো যায়নি');
  } finally {
    btn.disabled = false;
    btn.textContent = 'OTP পাঠান';
  }
}

async function verifyOtp(code) {
  if (code.length !== 6) {
    showError('otp-error', '৬ সংখ্যার কোড দিন');
    return;
  }

  var btn = document.getElementById('btn-verify');
  btn.disabled = true;
  btn.textContent = 'যাচাই হচ্ছে...';
  hideError('otp-error');

  try {
    var result = await supabaseClient.auth.verifyOtp({
      phone: currentPhone,
      token: code,
      type: 'sms',
    });
    if (result.error) throw result.error;
  } catch (err) {
    showError('otp-error', err.message || 'কোড সঠিক নয়');
    btn.disabled = false;
    btn.textContent = 'যাচাই করুন';
  }
}

// --- Resend timer ---

function startResendTimer() {
  var seconds = 60;
  var resendBtn = document.getElementById('btn-resend');
  resendBtn.disabled = true;

  if (resendTimer) clearInterval(resendTimer);

  resendBtn.textContent = 'আবার পাঠান (' + seconds + 's)';
  resendTimer = setInterval(function() {
    seconds--;
    if (seconds <= 0) {
      clearInterval(resendTimer);
      resendBtn.disabled = false;
      resendBtn.textContent = 'আবার পাঠান';
    } else {
      resendBtn.textContent = 'আবার পাঠান (' + seconds + 's)';
    }
  }, 1000);
}

async function resendOtp() {
  try {
    var result = await supabaseClient.auth.signInWithOtp({ phone: currentPhone });
    if (result.error) throw result.error;
    startResendTimer();
  } catch (err) {
    showError('otp-error', err.message || 'আবার পাঠানো যায়নি');
  }
}

// --- Shop setup ---

async function createProfile(shopName) {
  if (!shopName.trim()) {
    showError('setup-error', 'দোকানের নাম লিখুন');
    return;
  }

  var btn = document.getElementById('btn-setup');
  btn.disabled = true;
  btn.textContent = 'সেভ হচ্ছে...';
  hideError('setup-error');

  try {
    var session = (await supabaseClient.auth.getSession()).data.session;
    var response = await fetch('/api/auth/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + session.access_token,
      },
      body: JSON.stringify({ shop_name: shopName.trim() }),
    });

    if (!response.ok) {
      var errData = await response.json();
      throw new Error(errData.detail || 'প্রোফাইল তৈরি হয়নি');
    }

    showScreen('screen-dashboard');
  } catch (err) {
    showError('setup-error', err.message);
    btn.disabled = false;
    btn.textContent = 'শুরু করুন';
  }
}

// --- Session check + routing ---

async function checkAuthState() {
  var sessionResult = await supabaseClient.auth.getSession();
  var session = sessionResult.data.session;

  if (!session) {
    showScreen('screen-login');
    return;
  }

  try {
    var response = await fetch('/api/auth/me', {
      headers: { 'Authorization': 'Bearer ' + session.access_token },
    });

    if (response.status === 404) {
      showScreen('screen-setup');
    } else if (response.ok) {
      showScreen('screen-dashboard');
    } else {
      await supabaseClient.auth.signOut();
      showScreen('screen-login');
    }
  } catch (err) {
    showScreen('screen-login');
  }
}

// --- Sign out ---

async function signOut() {
  await supabaseClient.auth.signOut();
  showScreen('screen-login');
}

// --- UI helpers ---

function showError(elementId, message) {
  var el = document.getElementById(elementId);
  el.textContent = message;
  el.style.display = 'block';
}

function hideError(elementId) {
  var el = document.getElementById(elementId);
  el.textContent = '';
  el.style.display = 'none';
}

// --- Auth state listener ---

supabaseClient.auth.onAuthStateChange(function(event, session) {
  if (event === 'SIGNED_IN' && session) {
    checkAuthState();
  } else if (event === 'SIGNED_OUT') {
    showScreen('screen-login');
  }
});

// --- Event listeners ---

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('form-login').addEventListener('submit', function(e) {
    e.preventDefault();
    sendOtp(document.getElementById('input-phone').value);
  });

  document.getElementById('form-otp').addEventListener('submit', function(e) {
    e.preventDefault();
    verifyOtp(document.getElementById('input-otp').value);
  });

  document.getElementById('btn-resend').addEventListener('click', function() {
    resendOtp();
  });

  document.getElementById('btn-back-login').addEventListener('click', function() {
    showScreen('screen-login');
  });

  document.getElementById('form-setup').addEventListener('submit', function(e) {
    e.preventDefault();
    createProfile(document.getElementById('input-shop-name').value);
  });

  document.getElementById('btn-signout').addEventListener('click', function() {
    signOut();
  });

  checkAuthState();
});
