// Site CRUD + state transitions.
// Currently all methods are pass-throughs to the mock layer.
// TODO(db): swap each function body for the real api.* call.

import { api } from './client.js';

export async function getSite(id) {
  // TODO(db): return api.get(`/sites/${id}`);
  throw new Error('getSite: not yet implemented — wire to GET /api/sites/:id');
}

export async function listSites({ role, tenantId } = {}) {
  // TODO(db): return api.get('/sites');
  throw new Error('listSites: not yet implemented — wire to GET /api/sites');
}

// State transitions — each calls the appropriate backend route.
export async function createDraft(payload) {
  // TODO(db): return api.post('/bd/drafts', payload);
  throw new Error('createDraft: not yet implemented');
}

export async function shortlistDraft(id) {
  // TODO(db): return api.post(`/bd/drafts/${id}/shortlist`);
  throw new Error('shortlistDraft: not yet implemented');
}

export async function rejectDraft(id, payload) {
  // TODO(db): return api.post(`/bd/drafts/${id}/reject`, payload);
  throw new Error('rejectDraft: not yet implemented');
}

export async function submitDetailsForReview(id, payload) {
  // TODO(db): return api.post(`/bd/shortlist/${id}/details/submit`, payload);
  throw new Error('submitDetailsForReview: not yet implemented');
}

export async function saveDraftDetails(id, payload) {
  // TODO(db): return api.post(`/bd/shortlist/${id}/details/save`, payload);
  throw new Error('saveDraftDetails: not yet implemented');
}

export async function approveShortlist(id, payload) {
  // TODO(db): return api.post(`/bd/shortlist/${id}/approve`, payload);
  throw new Error('approveShortlist: not yet implemented');
}
