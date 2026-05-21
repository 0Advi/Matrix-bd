import { ROLE } from './roles.js';

// ACTION -> allowed roles map
// Keep in sync with backend app/rbac/permissions.py
export const PERMISSIONS = {
  create_draft:               [ROLE.EXECUTIVE],
  save_draft_details:         [ROLE.EXECUTIVE],
  submit_details_for_review:  [ROLE.EXECUTIVE],
  upload_loi:                 [ROLE.EXECUTIVE],
  view_own_loi:               [ROLE.EXECUTIVE],

  shortlist:                  [ROLE.SUPERVISOR, ROLE.SUB_SUPERVISOR],
  approve_details:            [ROLE.SUPERVISOR, ROLE.SUB_SUPERVISOR],
  reject:                     [ROLE.SUPERVISOR, ROLE.SUB_SUPERVISOR],
  archive:                    [ROLE.SUPERVISOR, ROLE.SUB_SUPERVISOR],
  set_loi_timeline:           [ROLE.SUPERVISOR, ROLE.SUB_SUPERVISOR],
  push_to_payments:           [ROLE.SUPERVISOR, ROLE.SUB_SUPERVISOR],
  reassign_site:              [ROLE.SUPERVISOR],
  assign_sub_supervisor:      [ROLE.SUPERVISOR],
};

export function can(role, action) {
  const allowed = PERMISSIONS[action];
  if (!allowed) return false;
  return allowed.includes(role);
}
