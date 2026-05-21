import { api } from './client.js';

export async function listAuditEvents({ page = 1, limit = 50 } = {}) {
  // TODO(db): return api.get(`/audit?page=${page}&limit=${limit}`);
  throw new Error('listAuditEvents: not yet implemented');
}

export async function getSiteAudit(siteId) {
  // TODO(db): return api.get(`/audit/site/${siteId}`);
  throw new Error('getSiteAudit: not yet implemented');
}
