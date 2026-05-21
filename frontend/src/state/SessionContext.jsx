import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { DEFAULT_SESSION } from '../services/api/authService.js';
import { can, PERMISSIONS } from '../rbac/permissions.js';
import { ROLE } from '../rbac/roles.js';

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

export function SessionProvider({ children }) {
  const [session, setSession] = useState(INITIAL_SESSION);
  const [dark, setDark] = useState(false);

  // role is the display/canonical string used by existing components:
  // 'exec' | 'supervisor' | 'sub_supervisor'
  const role = session.role;

  // setRole: allows role switcher to change role locally in mock mode.
  const setRole = (newRole) => {
    setSession(prev => ({ ...prev, role: newRole }));
  };

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.body.dataset.theme = dark ? 'dark' : 'light';
  }, [dark]);

  const toggleDark = () => setDark(d => !d);

  // Derive permissions from role using the RBAC engine.
  const permissions = useMemo(() => {
    const canonicalRole =
      role === 'exec' ? ROLE.EXECUTIVE :
      role === 'supervisor' ? ROLE.SUPERVISOR :
      role === 'sub_supervisor' ? ROLE.SUB_SUPERVISOR : role;
    return Object.entries(PERMISSIONS)
      .filter(([, roles]) => roles.includes(canonicalRole))
      .map(([action]) => action);
  }, [role]);

  // user object — preserves the exact { name, email, city, tenantId } shape
  // that existing components destructure from useSession().user
  const user = {
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
    cityScope: session.cityScope || user.city,
    permissions,
    dark,
    toggleDark,
    can: (action) => can(role, action),
    isMockMode: USE_MOCK,
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}
