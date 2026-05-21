// User service — public read API for user data.
import { adapter } from './adapters/index.js';

export async function listUsers() {
  return adapter.listUsers();
}

export async function me() {
  return adapter.me();
}
