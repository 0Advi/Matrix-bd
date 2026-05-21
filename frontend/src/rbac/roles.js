// ROLE enum — mirrors backend app/rbac/roles.py
export const ROLE = {
  EXECUTIVE: 'executive',
  SUPERVISOR: 'supervisor',
  SUB_SUPERVISOR: 'sub_supervisor',
};

// Legacy aliases used in the existing component prop (`role === 'exec'`)
// Components compare against these strings; do not rename without updating all call sites.
export const ROLE_DISPLAY = {
  [ROLE.EXECUTIVE]: 'exec',
  [ROLE.SUPERVISOR]: 'supervisor',
  [ROLE.SUB_SUPERVISOR]: 'sub_supervisor',
};

// Convert from display/legacy value to canonical ROLE enum value
export function canonicalRole(displayRole) {
  if (displayRole === 'exec') return ROLE.EXECUTIVE;
  if (displayRole === 'supervisor') return ROLE.SUPERVISOR;
  if (displayRole === 'sub_supervisor') return ROLE.SUB_SUPERVISOR;
  return displayRole;
}
