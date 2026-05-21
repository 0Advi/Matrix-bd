import { api } from './client.js';

export async function listNotifications() {
  // TODO(db): return api.get('/notifications');
  throw new Error('listNotifications: not yet implemented');
}

// TODO(mcp): implement real send via notification_service
export async function sendNotification(event) {
  // TODO(db): return api.post('/notifications/send', event);
  console.warn('sendNotification: stub — not yet implemented', event);
}
