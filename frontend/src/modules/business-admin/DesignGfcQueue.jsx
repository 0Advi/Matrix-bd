import React from 'react';
import { getDesignGfcQueue, getDesignGfcReview, decideGfc } from '../../services/api/designApi.js';

// Dark-themed (matches TeamDashboard #0B0C10). Lets the business_admin review a
// site's design package and give / withhold the Good-For-Construction approval.

const KIND_LABEL = { recce: 'Recce', '2d': '2D design', '3d': '3D design', boq: 'BOQ + estimate' };

const card = {
  border: '1px solid rgba(255,255,255,0.12)', borderRadius: 12,
  background: 'rgba(255,255,255,0.03)', padding: 16,
};
const btn = (bg) => ({
  height: 32, padding: '0 14px', borderRadius: 8, border: 'none',
  background: bg, color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer',
});

export default function DesignGfcQueue() {
  const [state, setState] = React.useState({ status: 'loading', items: [], error: null });
  const [openSite, setOpenSite] = React.useState(null);
  const [detail, setDetail] = React.useState(null);
  const [comments, setComments] = React.useState('');
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(() => {
    setState({ status: 'loading', items: [], error: null });
    getDesignGfcQueue()
      .then((d) => setState({ status: 'ready', items: d.items, error: null }))
      .catch((e) => setState({ status: 'error', items: [], error: e?.detail || e?.message || 'Failed to load GFC queue' }));
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const openReview = async (siteId) => {
    setOpenSite(siteId); setDetail(null); setComments('');
    try { setDetail(await getDesignGfcReview(siteId)); } catch (e) { window.alert(e?.detail || 'Failed to load package'); }
  };

  const decide = async (decision) => {
    if (decision === 'reject' && !comments.trim()) { window.alert('Comments are required to send back.'); return; }
    setBusy(true);
    try {
      await decideGfc(openSite, { decision, comments });
      setOpenSite(null); setDetail(null); setComments('');
      load();
    } catch (e) { window.alert(e?.detail || 'Decision failed'); }
    finally { setBusy(false); }
  };

  if (state.status === 'loading') {
    return <div style={{ ...card, color: 'rgba(255,255,255,0.6)' }}>Loading…</div>;
  }
  if (state.status === 'error') {
    return <div style={{ ...card, color: '#f0888c' }}>{state.error}</div>;
  }
  if (state.items.length === 0) {
    return <div style={{ ...card, color: 'rgba(255,255,255,0.55)' }}>No sites are awaiting GFC approval.</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {state.items.map((row) => (
        <div key={row.siteId} style={card}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'rgba(255,255,255,0.6)' }}>{row.siteCode}</span>
            <strong style={{ fontSize: 14 }}>{row.siteName}</strong>
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>{row.city}</span>
            {row.boqEstimatedAmount != null && (
              <span style={{ fontFamily: 'monospace', fontSize: 13, color: '#7fd1a8' }}>
                ₹{Number(row.boqEstimatedAmount).toLocaleString('en-IN')}
              </span>
            )}
            <span style={{ flex: 1 }}/>
            <button type="button" style={btn('#3b6ef0')} onClick={() => (openSite === row.siteId ? setOpenSite(null) : openReview(row.siteId))}>
              {openSite === row.siteId ? 'Close' : 'Review GFC'}
            </button>
          </div>

          {openSite === row.siteId && (
            <div style={{ marginTop: 14, borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: 14 }}>
              {!detail && <div style={{ color: 'rgba(255,255,255,0.6)' }}>Loading package…</div>}
              {detail && (
                <>
                  <div style={{ display: 'grid', gap: 8, marginBottom: 12 }}>
                    {(detail.deliverables || []).map((d) => (
                      <div key={d.kind} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12.5, color: 'rgba(255,255,255,0.85)' }}>
                        <span style={{ width: 110, color: 'rgba(255,255,255,0.6)' }}>{KIND_LABEL[d.kind] || d.kind}</span>
                        <span style={{ textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.1em', color: d.status === 'approved' ? '#7fd1a8' : 'rgba(255,255,255,0.5)' }}>{d.status}</span>
                        {d.fileUrl
                          ? <a href={d.fileUrl} target="_blank" rel="noreferrer" style={{ color: '#7aa2ff' }}>{d.fileName || d.fileUrl}</a>
                          : <span style={{ color: 'rgba(255,255,255,0.7)' }}>{d.fileName || ''}</span>}
                        {d.kind === 'boq' && d.estimatedAmount != null && (
                          <span style={{ fontFamily: 'monospace', color: '#7fd1a8' }}>₹{Number(d.estimatedAmount).toLocaleString('en-IN')}</span>
                        )}
                      </div>
                    ))}
                  </div>
                  <textarea
                    placeholder="Comments (visible to the design supervisor; required to send back)"
                    value={comments} onChange={(e) => setComments(e.target.value)}
                    style={{
                      width: '100%', minHeight: 64, padding: 10, borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.18)', background: 'rgba(255,255,255,0.04)',
                      color: '#fff', fontSize: 12.5, resize: 'vertical', marginBottom: 10,
                    }}
                  />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button type="button" disabled={busy} style={{ ...btn('#2f9e5e'), opacity: busy ? 0.6 : 1 }} onClick={() => decide('approve')}>
                      Approve (Good-For-Construction)
                    </button>
                    <button type="button" disabled={busy} style={{ ...btn('#c0413f'), opacity: busy ? 0.6 : 1 }} onClick={() => decide('reject')}>
                      Send back
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
