// ── base64url <-> ArrayBuffer helpers for WebAuthn ──
function b64urlToBuf(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const bin = atob(s);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}
function bufToB64url(buf) {
  const bytes = new Uint8Array(buf);
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function requestOptionsFromJSON(o) {
  return {
    ...o,
    challenge: b64urlToBuf(o.challenge),
    allowCredentials: (o.allowCredentials || []).map(c => ({ ...c, id: b64urlToBuf(c.id) })),
  };
}
function credentialToJSON(cred) {
  if (typeof cred.toJSON === 'function') return cred.toJSON();
  const json = {
    id: cred.id,
    rawId: bufToB64url(cred.rawId),
    type: cred.type,
    clientExtensionResults: cred.getClientExtensionResults ? cred.getClientExtensionResults() : {},
  };
  if (cred.response.attestationObject) {
    json.response = {
      clientDataJSON: bufToB64url(cred.response.clientDataJSON),
      attestationObject: bufToB64url(cred.response.attestationObject),
      transports: cred.response.getTransports ? cred.response.getTransports() : [],
    };
  } else {
    json.response = {
      clientDataJSON: bufToB64url(cred.response.clientDataJSON),
      authenticatorData: bufToB64url(cred.response.authenticatorData),
      signature: bufToB64url(cred.response.signature),
      userHandle: cred.response.userHandle ? bufToB64url(cred.response.userHandle) : undefined,
    };
  }
  return json;
}

// ── UI plumbing ──
function showStep(id) {
  document.querySelectorAll('.login-step').forEach(f => f.style.display = 'none');
  document.getElementById(id).style.display = '';
  showError('');
  showInfo('');
  document.getElementById('resend-link-wrap').style.display = 'none';
}
function showError(msg) {
  document.getElementById('login-error').textContent = msg;
  if (msg) showInfo('');
}
function showInfo(msg) {
  document.getElementById('login-info').textContent = msg;
  if (msg) document.getElementById('login-error').textContent = '';
}
async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, data };
}

const showRegisterLink = document.getElementById('show-register');
if (showRegisterLink) showRegisterLink.onclick = e => { e.preventDefault(); showStep('register-form'); };
const showLoginLink = document.getElementById('show-login');
if (showLoginLink) showLoginLink.onclick = e => { e.preventDefault(); showStep('login-form'); };

let pendingTotpToken = null;

/** After any successful login: straight into the app, unless this
 *  account has no baby yet, in which case offer to add one first. */
async function afterLogin() {
  try {
    const babies = await (await fetch('/api/babies')).json();
    if (Array.isArray(babies) && babies.length === 0) {
      showStep('onboarding-baby-step');
      return;
    }
  } catch {}
  location.href = '/';
}

document.getElementById('login-form').onsubmit = async e => {
  e.preventDefault();
  const email = document.getElementById('li-email').value.trim();
  const password = document.getElementById('li-password').value;
  const { ok, data } = await postJSON('/api/auth/login', { email, password });
  if (!ok) {
    showError(data.error || 'Login failed');
    document.getElementById('resend-link-wrap').style.display =
      data.error === 'email not verified' ? '' : 'none';
    return;
  }
  if (data.totp_required) {
    pendingTotpToken = data.pending_token;
    showStep('totp-form');
    return;
  }
  afterLogin();
};

document.getElementById('resend-link').onclick = async e => {
  e.preventDefault();
  const email = document.getElementById('li-email').value.trim();
  const password = document.getElementById('li-password').value;
  const { ok, data } = await postJSON('/api/auth/resend-verification', { email, password });
  if (!ok) { showError(data.error || 'Could not resend'); return; }
  showInfo('Confirmation email sent — check your inbox.');
  document.getElementById('resend-link-wrap').style.display = 'none';
};

const registerForm = document.getElementById('register-form');
if (registerForm) registerForm.onsubmit = async e => {
  e.preventDefault();
  const email = document.getElementById('re-email').value.trim();
  const password = document.getElementById('re-password').value;
  const password2 = document.getElementById('re-password2').value;
  if (password !== password2) { showError('Passwords do not match'); return; }
  const { ok, data } = await postJSON('/api/auth/register', { email, password });
  if (!ok) { showError(data.error || 'Could not create account'); return; }
  document.getElementById('verify-sent-email').textContent = email;
  showStep('verify-sent-step');
};

document.getElementById('verify-back-btn').onclick = () => showStep('login-form');

document.getElementById('totp-form').onsubmit = async e => {
  e.preventDefault();
  const code = document.getElementById('totp-code').value.trim();
  const { ok, data } = await postJSON('/api/auth/totp/verify', { pending_token: pendingTotpToken, code });
  if (!ok) { showError(data.error || 'Invalid code'); return; }
  afterLogin();
};

// ── Landed here from the confirmation email ──
{
  const params = new URLSearchParams(location.search);
  const verify = params.get('verify');
  if (verify === 'ok') showInfo('Email confirmed — log in below.');
  else if (verify === 'expired') showError('That link expired or was already used. Log in and resend it below.');
  if (verify) history.replaceState({}, '', location.pathname);
}

// ── First-baby onboarding, right after registration ──
document.getElementById('ob-create-btn').onclick = async () => {
  const name = document.getElementById('ob-baby-name').value.trim();
  const birthday = document.getElementById('ob-baby-birthday').value;
  if (name) {
    await postJSON('/api/babies', { name, birthday });
  }
  location.href = '/';
};
document.getElementById('ob-skip-btn').onclick = () => { location.href = '/'; };

// ── Passkey login ──
if (window.PublicKeyCredential) {
  document.getElementById('passkey-login-btn').style.display = '';
}
document.getElementById('passkey-login-btn').onclick = async () => {
  const email = document.getElementById('li-email').value.trim();
  try {
    const { ok, data } = await postJSON('/api/auth/passkey/login/options', email ? { email } : {});
    if (!ok) { showError(data.error || 'Passkey sign-in unavailable'); return; }
    const publicKey = requestOptionsFromJSON(data.options);
    const assertion = await navigator.credentials.get({ publicKey });
    const verify = await postJSON('/api/auth/passkey/login/verify', {
      challenge_token: data.challenge_token,
      credential: credentialToJSON(assertion),
    });
    if (!verify.ok) { showError(verify.data.error || 'Passkey sign-in failed'); return; }
    afterLogin();
  } catch (err) {
    showError(err.message || 'Passkey sign-in failed');
  }
};

// PWA install eligibility on Android needs an active service worker.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}
