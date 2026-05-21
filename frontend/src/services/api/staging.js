import { api } from './client.js';

export async function listExecStaging() {
  // TODO(db): return api.get('/staging/exec');
  throw new Error('listExecStaging: not yet implemented');
}

export async function listSupervisorStaging() {
  // TODO(db): return api.get('/staging/supervisor');
  throw new Error('listSupervisorStaging: not yet implemented');
}

export async function pushToPayments(siteId) {
  // TODO(db): return api.post(`/staging/${siteId}/push`);
  throw new Error('pushToPayments: not yet implemented');
}
