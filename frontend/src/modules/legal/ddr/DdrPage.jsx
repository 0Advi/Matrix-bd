import React from 'react';
import ModuleChecklistPage from '../../shared/checklist/ModuleChecklistPage.jsx';

const DDR_CHECKS = [
  { id: 'title_doc', label: 'Title / ownership verified' },
  { id: 'sanctioned_plan', label: 'Sanctioned plan verified' },
  { id: 'oc_cc', label: 'OC / CC verified' },
  { id: 'commercial_use', label: 'Commercial usage verified' },
  { id: 'property_tax', label: 'Property tax verified' },
  { id: 'electricity', label: 'Electricity connection verified' },
  { id: 'fire_noc', label: 'Fire NOC verified' },
];

const SITE = {
  code: 'BT-MUM-0144',
  name: 'BKC One - East Wing',
  city: 'Mumbai',
  owner: 'Riya Sharma',
  loiDate: '2026-05-18',
  stage: 'LEGAL_REVIEW',
  icon: 'shield',
  iconBg: 'var(--zm-plum-soft)',
  iconColor: 'var(--zm-plum)',
};

export default function DdrPage() {
  return (
    <ModuleChecklistPage
      checks={DDR_CHECKS}
      site={SITE}
      moduleName="legal"
      meta={[
        ['Site', SITE.name],
        ['Owner', SITE.owner],
        ['LOI date', SITE.loiDate],
      ]}
      trail={[
        ['LOI uploaded', SITE.loiDate],
        ['Legal review', 'DDR checks in progress'],
        ['Legal decision', 'Positive / negative pending'],
      ]}
      header={{
        file: 'No. 05',
        eyebrow: 'Legal module · DDR',
        title: <>Due diligence <em>review</em></>,
        lede: 'Mark each due-diligence check as Yes or No before the legal supervisor confirms the site verdict.',
        tagIcon: 'shield',
      }}
      tableLabel="DDR field"
      moduleShort="DDR"
      handoffText="A positive DDR continues toward agreement; a negative DDR closes the legal path and notifies BD."
      otherPlaceholder="Other DDR field"
      otherTitle="Need another document check?"
      otherDescription="Add as many custom Other rows as the due-diligence review requires."
    />
  );
}
