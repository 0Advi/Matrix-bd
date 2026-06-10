import React from 'react';
import PageHeader, { HeaderTag } from '../shared/page-header/PageHeader.jsx';

// NSO module overview — KPI cards + drill-down + deep links into the
// queue. Scaffolding stub: replaced by the module-overview implementation.
export default function NsoOverviewPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      <PageHeader
        file="No. 10" eyebrow="NSO module" title="Overview"
        lede="Module KPIs and drill-downs."
        right={<HeaderTag icon="dashboard" label="OVERVIEW"/>}
      />
      <div style={{ padding: 48, textAlign: 'center', color: 'var(--zm-fg-3)', fontFamily: 'var(--zm-font-body)', fontSize: 13, background: 'var(--zm-surface)', border: '1px dashed var(--zm-line)', borderRadius: 12 }}>
        Overview KPIs are on their way.
      </div>
    </div>
  );
}
