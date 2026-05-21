// Data transform extracted from App.jsx buildDrawerSite helper.
// Pure function — no UI, no side effects.

export function buildDrawerSite(row) {
  return {
    ...row,
    id: row.id || row.code,
    code: row.code,
    name: row.name,
    city: row.city,
    stage: row.stage || 'shortlist',
    carpet: row.carpet || 1000,
    opCost: row.totalOpCost || 100000,
    rent: row.rent || 80000,
    cam: row.cam || 18000,
    deposit: row.deposit || 400000,
    lockin: row.lockin || 36,
    escalation: row.escalation || 5,
    rentFree: row.rentFreeDays || 30,
    estSales: (row.estSales || 12) * 100000,
    model: row.model || 'Café · 900–1200 sqft',
    spocName: row.spocName || row.createdBy || row.by || 'TBD',
    spocPhone: '+91 ••••• •••••',
    pin: row.googlePin || row.pin || '—',
    loiSignedAt: row.loiUploadedAt || '—',
    loiSubmittedAt: row.loiUploadedAt || '—',
    days: row.days ?? row.daysSinceApproval ?? 0,
    createdAt: row.createdAt || row.visitDate || '—',
  };
}
