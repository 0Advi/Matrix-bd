// Public site service — all site reads and writes go through here.
// Components never call adapters or mock/* directly.
// All functions return promises with canonical site shape.

import { adapter } from './adapters/index.js';
import { SiteStatus } from '../../lib/stateMachine.js';

// Core transition function — validates the transition via assertTransition (inside adapter),
// applies the change, writes an audit entry, and returns the updated site.
export async function transitionSite(siteId, nextStatus, payload = {}) {
  return adapter.patchSiteStatus(siteId, nextStatus, payload);
}

// Convenience wrappers — all go through transitionSite

export async function shortlistSite(siteId, by) {
  return transitionSite(siteId, SiteStatus.SHORTLISTED, { by });
}

export async function submitDetails(siteId, formData, by) {
  return transitionSite(siteId, SiteStatus.DETAILS_SUBMITTED, {
    by,
    details: formData,
    score: Number(formData.score) || undefined,
    estSales: Number(formData.estSales) / 100000 || undefined,
    carpet: Number(formData.carpet) || undefined,
    rent: Math.round(Number(formData.rent) / 1000) || undefined,
    rentType: formData.rentType,
    totalOpCost: formData.totalOpCost,
  });
}

export async function approveSite(siteId, days, by, spocName) {
  return transitionSite(siteId, SiteStatus.APPROVED, {
    expectedLoiDays: days,
    by,
    spocName,
  });
}

export async function uploadLoi(siteId, file, uploadedBy) {
  return adapter.uploadLoi(siteId, { ...file, uploadedBy });
}

export async function pushToPayments(siteId, by) {
  return transitionSite(siteId, SiteStatus.PUSHED_TO_PAYMENTS, { by });
}

export async function rejectSite(siteId, reasons, comment, by) {
  return adapter.rejectSite(siteId, reasons, comment);
}

export async function archiveSite(siteId, note, by) {
  return adapter.archiveSite(siteId, note);
}

// Read operations

export async function listSites(filter = {}) {
  return adapter.listSites(filter);
}

export async function getSite(id) {
  return adapter.getSite(id);
}

export async function createSite(payload) {
  return adapter.createSite(payload);
}

export async function assignSite(siteId, execId) {
  return adapter.assignSite(siteId, execId);
}

// Save partial details (stays in current status, does not transition)
export async function saveDraftDetails(siteId, formData) {
  return adapter.patchSiteDetails(siteId, { ...formData, _savedAt: new Date().toISOString() });
}
