import React from 'react';
import { getDesignAdminQueue, adminReviewDeliverable } from '../../services/api/designApi.js';

// Site-grouped list: each site, and under it the 2D/3D deliverables a design
// supervisor has approved that now need the business_admin's second-tier approval.

const KIND_LABEL = { '2d': '2D design', '3d': '3D design' };

const card = {
  border: '1px solid rgba(255,255,255,0.12)', borderRadius: 12,
  background: 'rgba(255,255,255,0.03)', padding: 16,
};
const btn = (bg) => ({
  height: 30, padding: '0 12px', borderRadius: 8, border: 'none',
  background: bg, color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer',
});

export default function DesignDeliverableApprovals() {
  const [state, setState] = React.useState({ status: 'loading', items: [], error: null });
  const [comments, setComments] = React.useState({}); // `${siteId}:${kind}` -> text
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(() => {
    setState({ status: 'loading', items: [], error: null });
    getDesignAdminQueue()
      .then((d) => setState({ status: 'ready', items: d.items, error: null }))
      .catch((e) => setState({ status: 'error', items: [], error: e?.detail || e?.message || 'Failed to load approvals' }));
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const key = (siteId, kind) => `${siteId}:${kind}`;
  const setComment = (siteId, kind, v) => setComments((c) => ({ ...c, [key(siteId, kind)]: v }));

  const decide = async (siteId, kind, decision) => {
    const c = comments[key(siteId, kind)] || '';
    if (decision === 'reject' && !c.trim()) { window.alert('Comments are required to send back.'); return; }
    setBusy(true);
    try { await adminReviewDeliverable(siteId, kind, { decision, comments: c }); load(); }
    catch (e) { window.alert(e?.detail || 'Decision failed'); }
    finally { setBusy(false); }
  };

  if (state.status === 'loading') return <div style={{ ...card, color: 'rgba(255,255,255,0.6)' }}>Loading…</div>;
  if (state.status === 'error') return <div style={{ ...card, color: '#f0888c' }}>{state.error}</div>;
  if (state.items.length === 0) {
    return <div style={{ ...card, color: 'rgba(255,255,255,0.55)' }}>No 2D / 3D deliverables awaiting approval.</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {state.items.map((site) => (
        <div key={site.siteId} style={card}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'rgba(255,255,255,0.6)' }}>{site.siteCode}</span>
            <strong style={{ fontSize: 14 }}>{site.siteName}</strong>
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>{site.city}</span>
          </div>

          {site.deliverables.map((d) => (
            <div key={d.kind} style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 12, marginTop: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 8, minWidth: 0 }}>
                <span style={{ fontWeight: 700, fontSize: 13 }}>{KIND_LABEL[d.kind] || d.kind}</span>
                {d.downloadUrl
                  ? <a href={d.downloadUrl} target="_blank" rel="noreferrer" style={{ color: '#7aa2ff', fontSize: 12.5, wordBreak: 'break-all', overflowWrap: 'anywhere' }}>{d.fileName || 'Open document'}</a>
                  : <span style={{ fontSize: 12.5, color: 'rgba(255,255,255,0.7)', wordBreak: 'break-all' }}>{d.fileName || '(no file)'}</span>}
              </div>
              <textarea
                placeholder="Comments (visible to the supervisor; required to send back)"
                value={comments[key(site.siteId, d.kind)] || ''}
                onChange={(e) => setComment(site.siteId, d.kind, e.target.value)}
                style={{
                  width: '100%', boxSizing: 'border-box', minHeight: 54, padding: 8, borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.18)', background: 'rgba(255,255,255,0.04)',
                  color: '#fff', fontSize: 12.5, resize: 'vertical', marginBottom: 8,
                }}
              />
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="button" disabled={busy} style={{ ...btn('#2f9e5e'), opacity: busy ? 0.6 : 1 }} onClick={() => decide(site.siteId, d.kind, 'approve')}>
                  Approve
                </button>
                <button type="button" disabled={busy} style={{ ...btn('#c0413f'), opacity: busy ? 0.6 : 1 }} onClick={() => decide(site.siteId, d.kind, 'reject')}>
                  Send back
                </button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
