"""Action -> allowed roles map.  Mirrors frontend src/rbac/permissions.js."""
from app.rbac.roles import Role

PERMISSIONS: dict[str, list[Role]] = {
    "create_draft":               [Role.EXECUTIVE],
    "save_draft_details":         [Role.EXECUTIVE],
    "submit_details_for_review":  [Role.EXECUTIVE],
    "upload_loi":                 [Role.EXECUTIVE],
    "view_own_loi":               [Role.EXECUTIVE],

    "shortlist":                  [Role.SUPERVISOR, Role.SUB_SUPERVISOR],
    "approve_details":            [Role.SUPERVISOR, Role.SUB_SUPERVISOR],
    "reject":                     [Role.SUPERVISOR, Role.SUB_SUPERVISOR],
    "archive":                    [Role.SUPERVISOR, Role.SUB_SUPERVISOR],
    "set_loi_timeline":           [Role.SUPERVISOR, Role.SUB_SUPERVISOR],
    "push_to_payments":           [Role.SUPERVISOR, Role.SUB_SUPERVISOR],
    "reassign_site":              [Role.SUPERVISOR],
    "assign_sub_supervisor":      [Role.SUPERVISOR],
}


def can(role: Role, action: str) -> bool:
    allowed = PERMISSIONS.get(action, [])
    return role in allowed
