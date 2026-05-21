import { api } from './client.js';

export async function uploadLOI(siteId, formData) {
  // TODO(db): return api.post(`/loi/${siteId}/upload`, formData);
  throw new Error('uploadLOI: not yet implemented');
}

export async function viewLOI(siteId) {
  // TODO(db): return api.get(`/loi/${siteId}`);
  throw new Error('viewLOI: not yet implemented');
}

export async function setLOITimeline(siteId, days) {
  // TODO(db): return api.post(`/loi/${siteId}/set-timeline`, { expected_loi_days: days });
  throw new Error('setLOITimeline: not yet implemented');
}
