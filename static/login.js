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
function creationOptionsFromJSON(o) {
  return {
    ...o,
    challenge: b64urlToBuf(o.challenge),
    user: { ...o.user, id: b64urlToBuf(o.user.id) },
    excludeCredentials: (o.excludeCredentials || []).map(c => ({ ...c, id: b64urlToBuf(c.id) })),
  };
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
}
function showError(msg) {
  document.getElementById('login-error').textContent = msg;
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

document.getElementById('show-register').onclick = e => { e.preventDefault(); showStep('register-form'); };
document.getElementById('show-login').onclick = e => { e.preventDefault(); showStep('login-form'); };

let pendingTotpToken = null;

document.getElementById('login-form').onsubmit = async e => {
  e.preventDefault();
  const username = document.getElementById('li-username').value.trim();
  const password = document.getElementById('li-password').value;
  const { ok, data } = await postJSON('/api/auth/login', { username, password });
  if (!ok) { showError(data.error || 'Login failed'); return; }
  if (data.totp_required) {
    pendingTotpToken = data.pending_token;
    showStep('totp-form');
    return;
  }
  location.href = '/';
};

document.getElementById('register-form').onsubmit = async e => {
  e.preventDefault();
  const username = document.getElementById('re-username').value.trim();
  const password = document.getElementById('re-password').value;
  const { ok, data } = await postJSON('/api/auth/register', { username, password });
  if (!ok) { showError(data.error || 'Could not create account'); return; }
  location.href = '/';
};

document.getElementById('totp-form').onsubmit = async e => {
  e.preventDefault();
  const code = document.getElementById('totp-code').value.trim();
  const { ok, data } = await postJSON('/api/auth/totp/verify', { pending_token: pendingTotpToken, code });
  if (!ok) { showError(data.error || 'Invalid code'); return; }
  location.href = '/';
};

// ── Passkey login ──
if (window.PublicKeyCredential) {
  document.getElementById('passkey-login-btn').style.display = '';
}
document.getElementById('passkey-login-btn').onclick = async () => {
  const username = document.getElementById('li-username').value.trim();
  try {
    const { ok, data } = await postJSON('/api/auth/passkey/login/options', username ? { username } : {});
    if (!ok) { showError(data.error || 'Passkey sign-in unavailable'); return; }
    const publicKey = requestOptionsFromJSON(data.options);
    const assertion = await navigator.credentials.get({ publicKey });
    const verify = await postJSON('/api/auth/passkey/login/verify', {
      challenge_token: data.challenge_token,
      credential: credentialToJSON(assertion),
    });
    if (!verify.ok) { showError(verify.data.error || 'Passkey sign-in failed'); return; }
    location.href = '/';
  } catch (err) {
    showError(err.message || 'Passkey sign-in failed');
  }
};
