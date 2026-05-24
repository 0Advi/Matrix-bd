import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSession } from '../state/SessionContext.jsx';
import { ROUTES } from './routes.js';

// RequireRole: redirects to overview if the current role is not in the allowed list.
// `roles` can contain canonical ROLE values or legacy display values.
// Treats 'exec' and 'executive' as the same role so HTTP-mode JWTs (which
// always emit 'executive') match guards that still list the legacy 'exec' alias.
export function RequireRole({ roles, children }) {
  const { role } = useSession();
  const allowed = new Set(roles);
  if (allowed.has('exec'))      allowed.add('executive');
  if (allowed.has('executive')) allowed.add('exec');
  if (!allowed.has(role)) {
    return <Navigate to={ROUTES.OVERVIEW} replace />;
  }
  return children;
}

// RequireScope: gates a route by scope kind.
// `kind` is 'own' | 'city' | 'department' | 'tenant'
// For the current MVP with a mock session this always passes — wire real logic
// once the identity service is integrated.
export function RequireScope({ kind, children }) {
  // TODO(auth): enforce scope from session claims
  return children;
}
