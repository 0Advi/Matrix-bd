// HTTP adapter — calls the real FastAPI backend.
// Uses axios with base URL from VITE_API_BASE_URL.
// Stubs match routes in .claude/artifacts/routes-manifest.json.

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const client = axios.create({ baseURL: BASE_URL });

// Attach auth header when a token is present
client.interceptors.request.use(cfg => {
  const token = typeof window !== 'undefined' ? window.__zm_token : null;
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// Unwrap data from axios response
const get = (url, params) => client.get(url, { params }).then(r => r.data);
const post = (url, data) => client.post(url, data).then(r => r.data);
const patch = (url, data) => client.patch(url, data).then(r => r.data);

// ---- Sites ----

export async function listSites(filter = {}) {
  const params = {};
  if (filter.status) params.status = Array.isArray(filter.status) ? filter.status.join(',') : filter.status;
  if (filter.createdBy) params.created_by = filter.createdBy;
  if (filter.city) params.city = filter.city;
  return get('/sites', params);
}

export async function getSite(id) {
  return get(`/sites/${id}`);
}

export async function createSite(payload) {
  return post('/sites', payload);
}

export async function patchSiteStatus(id, status, payload = {}) {
  return patch(`/sites/${id}/status`, { status, payload });
}

export async function patchSiteDetails(id, details) {
  return patch(`/sites/${id}/details`, { details });
}

export async function uploadLoi(id, file) {
  const form = new FormData();
  form.append('file', file);
  return client.post(`/sites/${id}/loi`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
}

export async function archiveSite(id, note) {
  return post(`/sites/${id}/archive`, { note });
}

export async function rejectSite(id, reasons, comment) {
  return post(`/sites/${id}/reject`, { reasons, comment });
}

export async function assignSite(id, execId) {
  return post(`/sites/${id}/assign`, { exec_id: execId });
}

// ---- Users ----

export async function listUsers() {
  return get('/users');
}

export async function me() {
  return get('/users/me');
}

// ---- Auth ----

export async function login(credentials) {
  return post('/auth/login', credentials);
}

export async function logout() {
  return post('/auth/logout');
}
