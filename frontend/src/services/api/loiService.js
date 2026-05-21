// LOI service — upload and query LOI data.
import { adapter } from './adapters/index.js';

/**
 * Upload a LOI file for a site.
 * Returns { url: string, uploadedAt: string }
 */
export async function uploadLoi(siteId, file, uploadedBy) {
  return adapter.uploadLoi(siteId, { ...file, uploadedBy });
}
