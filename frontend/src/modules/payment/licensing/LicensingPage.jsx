import React from 'react';
import ModuleChecklistPage from '../../shared/checklist/ModuleChecklistPage.jsx';

const LICENSING_CHECKS = [
  { id: 'fssai', label: 'FSSAI license verified' },
  { id: 'health_trade', label: 'Health / trade license verified' },
  { id: 'shops_estab_reg', label: 'Shop & establishment registration verified' },
  { id: 'fire_noc', label: 'Fire NOC verified' },
  { id: 'storage_license', label: 'Signage / storage license verified' },
];

const SITE = {
  code: 'BT-MUM-0144',
  name: 'BKC One - East Wing',
  city: 'Mumbai',
  owner: 'Riya Sharma',
  agreementDate: '2026-05-23',
  stage: 'READY_FOR_LICENSING',
  icon: 'card',
  iconBg: 'var(--zm-copper-soft)',
  iconColor: 'var(--zm-copper)',
};

export default function LicensingPage() {
  return (
    <ModuleChecklistPage
      checks={LICENSING_CHECKS}
      site={SITE}
      moduleName="payment"
      meta={[
        ['Site', SITE.name],
        ['Owner', SITE.owner],
        ['Agreement date', SITE.agreementDate],
      ]}
      trail={[
        ['Agreement registered', SITE.agreementDate],
        ['Licensing review', 'Checklist in progress'],
        ['Payment handoff', 'Completion pending'],
      ]}
      header={{
        file: 'No. 06',
        eyebrow: 'Payment module · Licensing',
        title: <>Licensing <em>review</em></>,
        lede: 'Mark each statutory license check as Yes or No before the payment-side handoff is cleared.',
        tagIcon: 'card',
      }}
      tableLabel="Licensing field"
      moduleShort="Licensing"
      handoffText="When all license checks are clear, the site can be mirrored as licensing complete for BD visibility."
      otherPlaceholder="Other licensing field"
      otherTitle="Need another license check?"
      otherDescription="Add as many custom Other rows as this licensing review requires."
    />
  );
}
