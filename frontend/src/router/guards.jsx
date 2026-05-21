import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSession } from '../state/SessionContext.jsx';
import { ROUTES } from './routes.js';

// RequireRole: redirects to overview if the current role is not in the allowed list.
// `roles` can contain canonical ROLE values or legacy display values ('exec', 'supervisor').
export function RequireRole({ roles, children }) {
  const { role } = useSession();
  if (!roles.includes(role)) {
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
