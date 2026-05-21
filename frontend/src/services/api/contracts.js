// API contracts — single source of truth for all endpoints.
// Both mockAdapter and httpAdapter implement these exact signatures.
// Generated: 2026-05-21

export const API_CONTRACTS = {
  listSites: {
    method: 'GET',
    path: '/sites',
    query: {
      status: 'string | string[] (optional)',
      created_by: 'string (optional)',
      city: 'string (optional)',
    },
    response: 'Site[]',
  },
  getSite: {
    method: 'GET',
    path: '/sites/:id',
    params: { id: 'string' },
    response: 'Site',
  },
  createSite: {
    method: 'POST',
    path: '/sites',
    body: {
      name: 'string',
      city: 'string',
      visitDate: 'ISO date string',
      createdBy: '{ id: string, name: string }',
      tenantId: 'string',
    },
    response: 'Site',
  },
  patchSiteStatus: {
    method: 'PATCH',
    path: '/sites/:id/status',
    params: { id: 'string' },
    body: {
      status: 'SiteStatus (UPPER_SNAKE)',
      payload: {
        by: 'string (optional)',
        note: 'string (optional)',
        expectedLoiDays: 'number (optional)',
        rejectionReasons: 'string[] (optional)',
        archiveNote: 'string (optional)',
        details: 'object (optional)',
      },
    },
    response: 'Site',
  },
  uploadLoi: {
    method: 'POST',
    path: '/sites/:id/loi',
    params: { id: 'string' },
    body: 'multipart/form-data { file: File }',
    response: '{ url: string, uploadedAt: string }',
  },
  archiveSite: {
    method: 'POST',
    path: '/sites/:id/archive',
    params: { id: 'string' },
    body: { note: 'string' },
    response: 'Site',
  },
  rejectSite: {
    method: 'POST',
    path: '/sites/:id/reject',
    params: { id: 'string' },
    body: { reasons: 'string[]', comment: 'string' },
    response: 'Site',
  },
  assignSite: {
    method: 'POST',
    path: '/sites/:id/assign',
    params: { id: 'string' },
    body: { exec_id: 'string' },
    response: 'Site',
  },
  me: {
    method: 'GET',
    path: '/users/me',
    response: 'Session { id, name, email, role, cityScope, tenantId, token }',
  },
  login: {
    method: 'POST',
    path: '/auth/login',
    body: { email: 'string', password: 'string' },
    response: 'Session { id, name, email, role, cityScope, tenantId, token }',
  },
  logout: {
    method: 'POST',
    path: '/auth/logout',
    response: '{ ok: true }',
  },
};

export default API_CONTRACTS;
