// Client-side mirror of backend app/domain/state_machine.py
// Keep in sync with the backend enum and transition table.

export const SiteStatus = {
  DRAFT_SUBMITTED:    'DRAFT_SUBMITTED',
  SHORTLISTED:        'SHORTLISTED',
  DETAILS_SUBMITTED:  'DETAILS_SUBMITTED',
  APPROVED:           'APPROVED',
  LOI_UPLOADED:       'LOI_UPLOADED',
  PUSHED_TO_PAYMENTS: 'PUSHED_TO_PAYMENTS',
  REJECTED:           'REJECTED',
  ARCHIVED:           'ARCHIVED',
};

// Allowed transitions: { fromStatus: [toStatus, ...] }
export const ALLOWED_TRANSITIONS = {
  [SiteStatus.DRAFT_SUBMITTED]:    [SiteStatus.SHORTLISTED, SiteStatus.REJECTED, SiteStatus.ARCHIVED],
  [SiteStatus.SHORTLISTED]:        [SiteStatus.DETAILS_SUBMITTED, SiteStatus.REJECTED, SiteStatus.ARCHIVED],
  [SiteStatus.DETAILS_SUBMITTED]:  [SiteStatus.APPROVED, SiteStatus.REJECTED, SiteStatus.ARCHIVED],
  [SiteStatus.APPROVED]:           [SiteStatus.LOI_UPLOADED, SiteStatus.REJECTED, SiteStatus.ARCHIVED],
  [SiteStatus.LOI_UPLOADED]:       [SiteStatus.PUSHED_TO_PAYMENTS, SiteStatus.REJECTED, SiteStatus.ARCHIVED],
  [SiteStatus.PUSHED_TO_PAYMENTS]: [], // terminal
  [SiteStatus.REJECTED]:           [], // terminal
  [SiteStatus.ARCHIVED]:           [], // terminal
};

export function canTransition(fromStatus, toStatus) {
  const allowed = ALLOWED_TRANSITIONS[fromStatus] || [];
  return allowed.includes(toStatus);
}

export function assertTransition(fromStatus, toStatus) {
  if (!canTransition(fromStatus, toStatus)) {
    throw new Error(`Invalid transition: ${fromStatus} -> ${toStatus}`);
  }
}

// LEGACY_STAGE_MAP: maps legacy display stage strings to canonical SiteStatus values.
// Used by SitesContext to back-compat components reading site.stage === 'draft' etc.
export const LEGACY_STAGE_MAP = {
  draft:       SiteStatus.DRAFT_SUBMITTED,
  shortlist:   SiteStatus.SHORTLISTED,
  inReview:    SiteStatus.DETAILS_SUBMITTED,
  staging:     SiteStatus.APPROVED,
  overdue:     SiteStatus.APPROVED,
  uploaded:    SiteStatus.LOI_UPLOADED,
  completed:   SiteStatus.PUSHED_TO_PAYMENTS,
  rejected:    SiteStatus.REJECTED,
  archived:    SiteStatus.ARCHIVED,
};

// Reverse map: canonical SiteStatus -> legacy stage string used by page components.
const STATUS_TO_LEGACY = {
  [SiteStatus.DRAFT_SUBMITTED]:    'draft',
  [SiteStatus.SHORTLISTED]:        'shortlist',
  [SiteStatus.DETAILS_SUBMITTED]:  'shortlist', // inReview is derived separately via inReview boolean
  [SiteStatus.APPROVED]:           'staging',
  [SiteStatus.LOI_UPLOADED]:       'uploaded',
  [SiteStatus.PUSHED_TO_PAYMENTS]: 'completed',
  [SiteStatus.REJECTED]:           'rejected',
  [SiteStatus.ARCHIVED]:           'archived',
};

// Returns the legacy stage string that render bodies expect.
// inReview flag is set separately on DETAILS_SUBMITTED sites.
export function legacyStageFor(status) {
  return STATUS_TO_LEGACY[status] || 'draft';
}
