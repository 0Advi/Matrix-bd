import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { signInWithWorkspaceCode, PendingApprovalError } from '../../services/api/supabaseAuth.js';

// Mount the full static landing page (kept in /public/landing) as the
// unauthenticated entry surface. We slot the demo's <style> block and <body>
// content into the React tree, then re-implement the modal's open/close,
// tab-switch, and form-submit handlers in scoped JS that talks to Supabase.
//
// Why this shape instead of a JSX port: the static file is the design source
// of truth — keeping it intact means visual tweaks land by editing one HTML
// file, not by re-syncing two parallel representations.

const LANDING_HTML_URL = '/landing/matrix_bd_landing_page_demo.html';
const ASSET_PREFIX_REWRITE = [
  // The static page references `matrix_landing_assets/foo.jpg` relative to its
  // own URL. When rendered at the app root, those paths must be absolute.
  [/matrix_landing_assets\//g, '/landing/matrix_landing_assets/'],
];

function splitDocument(text) {
  const style = text.match(/<style>([\s\S]*?)<\/style>/);
  const body  = text.match(/<body>([\s\S]*?)<\/body>/);
  let bodyHtml = body ? body[1] : '';
  // Strip the inline <script> — we re-implement its behavior in React below.
  bodyHtml = bodyHtml.replace(/<script[\s\S]*?<\/script>/g, '');
  for (const [pattern, replacement] of ASSET_PREFIX_REWRITE) {
    bodyHtml = bodyHtml.replace(pattern, replacement);
  }
  return { css: style ? style[1] : '', body: bodyHtml };
}

export default function LandingPage() {
  const wrapperRef = useRef(null);
  const [doc, setDoc] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    fetch(LANDING_HTML_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then((text) => alive && setDoc(splitDocument(text)))
      .catch((err) => alive && setError(err.message || String(err)));
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!doc || !wrapperRef.current) return;
    const root = wrapperRef.current;
    const modal = root.querySelector('.auth-modal');
    if (!modal) return; // bail if the HTML doesn't include the modal

    // ── Rewrite the Login form's "password" field as a "workspace code" ──
    // The static landing HTML ships with a generic Login + Register modal.
    // Auth model is email + workspace_code (no passwords). We mutate the
    // Login panel's second field at runtime instead of touching the HTML.
    const loginPanelEl = modal.querySelector('[data-panel="login"]');
    if (loginPanelEl) {
      const intro = loginPanelEl.querySelector('h2');
      if (intro) intro.textContent = 'Sign in to your workspace';
      const sub = loginPanelEl.querySelector('p');
      if (sub) sub.textContent = 'Enter the work email you used and your workspace code.';

      const passInput = loginPanelEl.querySelector('#login-password');
      if (passInput) {
        passInput.type        = 'text';
        passInput.id          = 'login-code';
        passInput.placeholder = 'BTOKAI-7X9F';
        passInput.setAttribute('autocomplete', 'off');
        passInput.setAttribute('spellcheck', 'false');
        passInput.style.textTransform = 'uppercase';
        passInput.style.letterSpacing = '0.1em';
        const passLabel = loginPanelEl.querySelector('label[for="login-password"]');
        if (passLabel) {
          passLabel.setAttribute('for', 'login-code');
          passLabel.textContent = 'Workspace code';
        }
      }

      // The "Forgot password?" mini-link is meaningless in this auth model.
      const miniLink = loginPanelEl.querySelector('.mini-link');
      if (miniLink) miniLink.remove();

      const securityNote = loginPanelEl.querySelector('.security-note');
      if (securityNote) {
        securityNote.textContent =
          'First time signing in? You\'ll land in your supervisor\'s queue until they assign you a role.';
      }
    }

    const tabs   = root.querySelectorAll('[data-tab]');
    const panels = root.querySelectorAll('[data-panel]');

    const setMode = (mode) => {
      tabs.forEach((t) => {
        const active = t.getAttribute('data-tab') === mode;
        t.classList.toggle('active', active);
        t.setAttribute('aria-selected', String(active));
      });
      panels.forEach((p) => p.classList.toggle('active', p.getAttribute('data-panel') === mode));
    };

    const open = (mode = 'login') => {
      setMode(mode);
      modal.classList.add('is-open');
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      const firstField = root.querySelector('.form-panel.active input');
      window.setTimeout(() => firstField && firstField.focus(), 180);
    };

    const close = () => {
      modal.classList.remove('is-open');
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    };

    // Track listeners so cleanup can remove them.
    const cleanup = [];

    root.querySelectorAll('[data-open-auth]').forEach((btn) => {
      const handler = () => open(btn.getAttribute('data-open-auth'));
      btn.addEventListener('click', handler);
      cleanup.push(() => btn.removeEventListener('click', handler));
    });

    root.querySelectorAll('[data-close-auth]').forEach((btn) => {
      btn.addEventListener('click', close);
      cleanup.push(() => btn.removeEventListener('click', close));
    });

    tabs.forEach((tab) => {
      const handler = () => setMode(tab.getAttribute('data-tab'));
      tab.addEventListener('click', handler);
      cleanup.push(() => tab.removeEventListener('click', handler));
    });

    // In-page anchor links (e.g. href="#workflow") would otherwise pollute the
    // HashRouter URL. Intercept them and scrollIntoView the target.
    root.querySelectorAll('a[href^="#"]').forEach((a) => {
      const handler = (e) => {
        const targetId = a.getAttribute('href').slice(1);
        if (!targetId || targetId === '/') return; // bare "#" is just a no-op brand link
        const target = root.querySelector(`#${CSS.escape(targetId)}`);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      };
      a.addEventListener('click', handler);
      cleanup.push(() => a.removeEventListener('click', handler));
    });

    const onKey = (e) => {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) close();
    };
    window.addEventListener('keydown', onKey);
    cleanup.push(() => window.removeEventListener('keydown', onKey));

    // Login form submit. The static page uses type="button" so there's no
    // native submit; we trigger on click of the primary button inside the
    // login panel.
    const loginPanel = root.querySelector('[data-panel="login"]');
    const loginBtn   = loginPanel ? loginPanel.querySelector('button.btn-primary') : null;
    const errorSlot  = (() => {
      if (!loginPanel) return null;
      const el = document.createElement('div');
      el.className = 'security-note';
      el.style.borderColor = 'rgba(222, 117, 111, 0.5)';
      el.style.background  = 'rgba(222, 117, 111, 0.12)';
      el.style.color       = '#fcd5d2';
      el.style.display     = 'none';
      loginPanel.appendChild(el);
      return el;
    })();
    const showError = (msg) => {
      if (!errorSlot) return;
      errorSlot.textContent = msg;
      errorSlot.style.display = 'flex';
    };
    const clearError = () => { if (errorSlot) errorSlot.style.display = 'none'; };

    if (loginBtn && loginPanel) {
      const loginForm  = loginPanel; // the panel IS the <form> element
      const emailInput = loginPanel.querySelector('#login-email');
      // The field id flipped from #login-password to #login-code when we
      // rewrote the panel above. Fall back to the old id if the rewrite
      // didn't happen (defensive).
      const codeInput  = loginPanel.querySelector('#login-code')
                      || loginPanel.querySelector('#login-password');
      const originalLabel = loginBtn.textContent;
      loginBtn.setAttribute('type', 'submit');
      const EMAIL_RE_L = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const CODE_RE_L  = /^[A-Za-z0-9\-]{4,32}$/;

      const onSubmit = async (e) => {
        e.preventDefault();
        clearError();
        const email = emailInput ? emailInput.value.trim() : '';
        const code  = codeInput  ? codeInput.value.trim().toUpperCase() : '';
        if (!email || !code) {
          showError('Enter your work email and workspace code.');
          return;
        }
        if (!EMAIL_RE_L.test(email)) {
          showError('Email looks invalid — use the form you@company.com.');
          return;
        }
        if (!CODE_RE_L.test(code)) {
          showError('Workspace code looks invalid. Ask your supervisor for the exact code.');
          return;
        }
        loginBtn.disabled    = true;
        loginBtn.textContent = 'Signing in…';
        try {
          await signInWithWorkspaceCode(email, code);
          // Token is stashed; useAuthToken bounces the route to / automatically.
          close();
        } catch (err) {
          if (err && err.isPending) {
            // Special-case the "queued" response so the messaging is warm,
            // not alarming.
            showError(err.message);
          } else {
            const msg = err && err.message ? err.message : String(err);
            showError(`Sign-in failed: ${msg}`);
          }
          loginBtn.disabled    = false;
          loginBtn.textContent = originalLabel;
        }
      };
      loginForm.addEventListener('submit', onSubmit);
      cleanup.push(() => loginForm.removeEventListener('submit', onSubmit));
    }

    // Register form ("Request workspace"). The backend doesn't yet expose a
    // self-service tenant-provisioning endpoint, so we validate inputs, queue
    // the request in sessionStorage for the future POST /api/tenancy/request,
    // and surface a friendly success state. When that endpoint lands the only
    // change here is swapping `queueRequest` for a real fetch().
    const registerPanel = root.querySelector('[data-panel="register"]');
    const registerBtn   = registerPanel ? registerPanel.querySelector('button.btn-primary') : null;
    const registerStatus = (() => {
      if (!registerPanel) return null;
      const el = document.createElement('div');
      el.className = 'security-note';
      el.style.display = 'none';
      registerPanel.appendChild(el);
      return el;
    })();
    const showRegisterStatus = (msg, tone = 'success') => {
      if (!registerStatus) return;
      registerStatus.textContent = msg;
      registerStatus.style.display = 'flex';
      if (tone === 'error') {
        registerStatus.style.borderColor = 'rgba(222, 117, 111, 0.5)';
        registerStatus.style.background  = 'rgba(222, 117, 111, 0.12)';
        registerStatus.style.color       = '#fcd5d2';
      } else {
        registerStatus.style.borderColor = 'rgba(70, 234, 209, 0.32)';
        registerStatus.style.background  = 'rgba(70, 234, 209, 0.12)';
        registerStatus.style.color       = 'rgba(249, 241, 223, 0.86)';
      }
    };

    if (registerBtn && registerPanel) {
      const registerForm  = registerPanel; // the panel IS the <form>
      const companyInput  = registerPanel.querySelector('#company-name');
      const adminInput    = registerPanel.querySelector('#admin-email');
      const sizeInput     = registerPanel.querySelector('#company-size');
      const originalLabel = registerBtn.textContent;
      const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      registerBtn.setAttribute('type', 'submit'); // Enter key submits

      const onSubmit = async (e) => {
        e.preventDefault();
        const company    = companyInput ? companyInput.value.trim() : '';
        const adminEmail = adminInput   ? adminInput.value.trim()   : '';
        const teamSize   = sizeInput    ? sizeInput.value           : '';

        if (!company || !adminEmail) {
          showRegisterStatus('Company name and admin email are required.', 'error');
          return;
        }
        if (!EMAIL_RE.test(adminEmail)) {
          showRegisterStatus('Admin email looks invalid — use the form name@company.com.', 'error');
          return;
        }

        registerBtn.disabled    = true;
        registerBtn.textContent = 'Submitting…';

        // Hit the public POST /api/tenancy/request-workspace endpoint. This is
        // the ONE unauthenticated POST in the platform — it captures the
        // workspace request into the workspace_requests table for admin review.
        const apiBase = (import.meta && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '/api';
        try {
          const res = await fetch(`${apiBase}/tenancy/request-workspace`, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ company, admin_email: adminEmail, team_size: teamSize }),
          });
          const body = await res.json().catch(() => ({}));
          if (!res.ok) {
            const detail = body && body.detail ? body.detail : `HTTP ${res.status}`;
            const detailStr = Array.isArray(detail)
              ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
              : String(detail);
            throw new Error(detailStr);
          }
          showRegisterStatus(
            body.message || `Request received for ${company}. We will email ${adminEmail} once provisioned.`,
            'success',
          );
          if (companyInput) companyInput.value = '';
          if (adminInput)   adminInput.value   = '';
          registerBtn.textContent = 'Request submitted ✓';
          window.setTimeout(() => {
            registerBtn.disabled    = false;
            registerBtn.textContent = originalLabel;
          }, 2400);
        } catch (err) {
          const msg = err && err.message ? err.message : String(err);
          showRegisterStatus(`Could not submit request: ${msg}`, 'error');
          registerBtn.disabled    = false;
          registerBtn.textContent = originalLabel;
        }
      };
      registerForm.addEventListener('submit', onSubmit);
      cleanup.push(() => registerForm.removeEventListener('submit', onSubmit));
    }

    return () => {
      cleanup.forEach((fn) => { try { fn(); } catch { /* noop */ } });
      document.body.style.overflow = '';
    };
  }, [doc, navigate]);

  if (error) {
    return (
      <div style={{ padding: 24, color: '#fff', background: '#111', minHeight: '100vh' }}>
        Landing page failed to load: {error}
      </div>
    );
  }
  if (!doc) {
    return (
      <div style={{ padding: 24, color: '#bbb', background: '#0b1114', minHeight: '100vh' }}>
        Loading…
      </div>
    );
  }

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: doc.css }} />
      <div ref={wrapperRef} dangerouslySetInnerHTML={{ __html: doc.body }} />
    </>
  );
}
