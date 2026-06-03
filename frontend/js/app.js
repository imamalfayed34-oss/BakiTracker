// Baki Tracker — Phase 0 connection check
// Pings the backend and DB, registers the service worker, and updates the status UI.

function setStatus(key, ok, text) {
  const dot = document.getElementById('dot-' + key);
  const val = document.getElementById('val-' + key);
  dot.classList.remove('ok', 'fail');
  val.classList.remove('ok', 'fail');
  dot.classList.add(ok ? 'ok' : 'fail');
  val.classList.add(ok ? 'ok' : 'fail');
  val.textContent = text;
}

async function checkServer() {
  try {
    const r = await fetch('/api/health');
    const d = await r.json();
    setStatus('server', d.status === 'ok', d.status === 'ok' ? 'live · ' + d.env : 'down');
  } catch {
    setStatus('server', false, 'unreachable');
  }
}

async function checkDb() {
  try {
    const r = await fetch('/api/health/db');
    const d = await r.json();
    if (d.status === 'ok') setStatus('db', true, 'connected');
    else if (d.status === 'not_configured') setStatus('db', false, 'set env vars');
    else setStatus('db', false, 'error');
  } catch {
    setStatus('db', false, 'unreachable');
  }
}

function checkPwa() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
      .then(() => setStatus('pwa', true, 'registered'))
      .catch(() => setStatus('pwa', false, 'failed'));
  } else {
    setStatus('pwa', false, 'unsupported');
  }
}

checkServer();
checkDb();
checkPwa();
