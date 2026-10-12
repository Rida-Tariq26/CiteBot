import React from 'react';

export default function CitationChip({ num, isActive, onClick, citation }) {
  const label = citation
    ? `Citation ${num}: ${citation.document_name}${citation.page_number ? `, page ${citation.page_number}` : ''}`
    : `Citation ${num}`;
  return (
    <button
      type="button"
      onClick={() => onClick(num)}
      title={citation ? `${citation.document_name} (Page ${citation.page_number || 'N/A'})` : `Citation [${num}]`}
      aria-label={label}
      aria-pressed={!!isActive}
      className="cite-chip"
    >
      {num}
    </button>
  );
}
