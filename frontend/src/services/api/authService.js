// Auth service — login/logout via adapter.
// Returns a session object: { id, name, email, role, cityScope, permissions, tenantId, token }
import { adapter } from './adapters/index.js';
import { DEFAULT_SESSION } from './mock/mockAuth.js';

// Default session for mock mode — used by SessionContext to bootstrap.
// In HTTP mode this is replaced by the /users/me response.
export { DEFAULT_SESSION };

export async function login(credentials) {
  return adapter.login(credentials);
}

export async function logout() {
  return adapter.logout();
}
