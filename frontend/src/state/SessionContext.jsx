import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { DEFAULT_SESSION, me as fetchMe, logout as logoutApi } from '../services/api/authService.js';
import { can, PERMISSIONS } from '../rbac/permissions.js';
import { ROLE } from '../rbac/roles.js';
import {
  SESSION_EXPIRED_EVENT,
  subscribeAuthToken,
  getAuthToken,
  clearAuthToken,
  notifySessionExpired,
} from '../services/api/authToken.js';
import { signOut as supabaseSignOut } from '../services/api/supabaseAuth.js';

// SessionContext — holds the current user session and role.
// In MOCK mode the session comes from DEFAULT_SESSION (legacy: Riya Sharma as supervisor).
// In HTTP mode the session is populated from /users/me after login.
// Role switcher only works in mock mode; in HTTP mode role comes from the JWT.

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;

// Build initial session from DEFAULT_SESSION to preserve legacy behavior.
// Legacy default was 'supervisor' for the role switcher.
const INITIAL_SESSION = {
  ...DEFAULT_SESSION,
  role: 'supervisor',
};

const SessionContext = createContext(null);

// Only a genuine auth rejection (401/403) means the token is stale and should
// be dropped. A timeout / network blip / 5xx surfaces as ApiError status 0 or
// >=500 — those must NOT log the user out (a Railway cold start would sign
// everyone out on refresh). Exported for tests. (#128)
export function isAuthRejection(err) {
  const status = err?.status;
  return status === 401 || status === 403;
}

export function SessionProvider({ children }) {
  const [session, setSession] = useState(INITIAL_SESSION);
  // authReady: false until the first /auth/whoami resolves (HTTP mode). The
  // shell must not fire role-gated calls (e.g. the supervisor-only pending-users
  // badge) while the session still holds the pre-hydration default role
  // ('supervisor'), or a non-supervisor token triggers a transient 403/401.
  // Mock mode is ready immediately — the session is the static default.
  const [authReady, setAuthReady] = useState(USE_MOCK);
  const [sessionExpired, setSessionExpired] = useState(null);
  // Hydrate dark from localStorage so the choice survives refresh and any
  // provider re-mount (e.g. StrictMode double-invoke, route-driven unmount).
  const [dark, setDark] = useState(() => {
    try {
      const stored = window.localStorage.getItem('zm:dark');
      if (stored === '1') return true;
      if (stored === '0') return false;
      return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
    } catch { return false; }
  });

  // role is the display/canonical string used by existing components:
  // 'business_admin' | 'supervisor' | 'executive' | 'exec'
  const role = session.role;

  // setRole: allows role switcher to change role locally in mock mode.
  const setRole = (newRole) => {
    setSession(prev => ({ ...prev, role: newRole }));
  };

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.body.dataset.theme = dark ? 'dark' : 'light';
    try { window.localStorage.setItem('zm:dark', dark ? '1' : '0'); } catch { /* storage disabled */ }
  }, [dark]);

  useEffect(() => {
    if (USE_MOCK || typeof window === 'undefined') return undefined;
    const onExpired = (event) => {
      setSessionExpired(event?.detail || { reason: 'expired' });
    };
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, []);

  // In HTTP mode, hydrate session from /auth/whoami whenever a token appears
  // (sign-in or token refresh) and reset to defaults when it clears.
  useEffect(() => {
    if (USE_MOCK) return;
    let alive = true;
    const hydrate = async (token) => {
      if (!token) {
        if (alive) { setSession(INITIAL_SESSION); setAuthReady(true); }
        return;
      }
      try {
        const claims = await fetchMe(); // GET /auth/whoami
        if (!alive) return;
        setSession({
          ...INITIAL_SESSION,
          name:      claims.email ? claims.email.split('@')[0] : INITIAL_SESSION.name,
          email:     claims.email || INITIAL_SESSION.email,
          role:      claims.role || INITIAL_SESSION.role,
          tenantId:  claims.tenant_id || INITIAL_SESSION.tenantId,
          cityScope: claims.city || INITIAL_SESSION.cityScope,
          module:    claims.module || null,
          // JWT subject id — the DDR licensing tab compares this against the
          // site's legal delegate to decide whether the auto-inherited
          // licensing CTA is unlocked for this user.
          userId:    claims.sub || INITIAL_SESSION.userId || null,
        });
        setSessionExpired(null);
      } catch (err) {
        if (isAuthRejection(err)) {
          // Stale token / missing app_metadata. Keep the token and mounted
          // route until the user chooses to sign in again so in-progress forms
          // are not wiped by an automatic redirect. (#130)
          // eslint-disable-next-line no-console
          console.warn('[session] /auth/whoami unauthorized — preserving route', err);
          notifySessionExpired({ reason: 'whoami_unauthorized', error: err });
        } else {
          // Transient (timeout / network / 5xx). Keep the token so the user
          // isn't logged out by a slow backend; a refresh re-hydrates. (#128)
          // eslint-disable-next-line no-console
          console.warn('[session] /auth/whoami failed transiently — keeping token', err);
        }
      } finally {
        // Session resolved (success or failure) — role is now authoritative,
        // so role-gated shell calls are safe to fire.
        if (alive) setAuthReady(true);
      }
    };
    hydrate(getAuthToken());
    return subscribeAuthToken(hydrate);
  }, []);

  const toggleDark = () => setDark(d => !d);

  const signOut = async () => {
    try { await logoutApi(); } catch { /* best-effort */ }
    try { await supabaseSignOut(); } catch { /* best-effort */ }
    clearAuthToken();
    setSessionExpired(null);
    setSession(INITIAL_SESSION);
  };

  const signInAgain = () => {
    clearAuthToken();
    setSessionExpired(null);
    setSession(INITIAL_SESSION);
  };

  // Derive permissions from role using the RBAC engine.
  const permissions = useMemo(() => {
    const canonicalRole =
      role === 'exec' ? ROLE.EXECUTIVE :
      role === 'supervisor' ? ROLE.SUPERVISOR : role;
    return Object.entries(PERMISSIONS)
      .filter(([, roles]) => roles.includes(canonicalRole))
      .map(([action]) => action);
  }, [role]);

  // user object — preserves the exact { name, email, city, tenantId } shape
  // that existing components destructure from useSession().user
  const user = {
    id: session.userId || session.id || null,
    userId: session.userId || session.id || null,
    name: session.name,
    email: session.email,
    city: session.cityScope || 'Mumbai',
    tenantId: session.tenantId,
  };

  const value = {
    user,
    role,
    setRole: USE_MOCK ? setRole : undefined, // hide switcher in HTTP mode
    session,
    authReady,
    cityScope: session.cityScope || user.city,
    permissions,
    dark,
    toggleDark,
    can: (action) => can(role, action),
    isMockMode: USE_MOCK,
    signOut,
    sessionExpired,
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
      {sessionExpired && !USE_MOCK && (
        <div
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="session-expired-title"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            display: 'grid',
            placeItems: 'center',
            background: 'rgba(7, 12, 10, 0.45)',
            padding: 24,
          }}
        >
          <div
            style={{
              width: 'min(440px, calc(100vw - 32px))',
              borderRadius: 18,
              border: '1px solid rgba(24, 84, 75, 0.22)',
              background: '#fffaf1',
              boxShadow: '0 24px 80px rgba(0,0,0,0.22)',
              padding: 24,
              color: '#181a20',
            }}
          >
            <p style={{ margin: '0 0 8px', color: '#0f6b5f', fontSize: 12, fontWeight: 800, letterSpacing: '0.16em', textTransform: 'uppercase' }}>
              Session paused
            </p>
            <h2 id="session-expired-title" style={{ margin: 0, fontSize: 28, lineHeight: 1.05 }}>
              Sign in again to continue
            </h2>
            <p style={{ margin: '14px 0 22px', color: '#5f626d', lineHeight: 1.45 }}>
              Your workspace session expired. This page is still open so your in-progress form stays visible.
            </p>
            <button
              type="button"
              onClick={signInAgain}
              style={{
                width: '100%',
                minHeight: 48,
                border: 0,
                borderRadius: 14,
                background: '#0f6b5f',
                color: '#fff',
                fontWeight: 800,
                cursor: 'pointer',
              }}
            >
              Go to sign in
            </button>
          </div>
        </div>
      )}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}
