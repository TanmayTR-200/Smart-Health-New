/**
 * Tests for health-score badge color logic.
 * Extracted from Dashboard.jsx's getStatusColor / getStatusDot / getSeverityColor.
 */

// Replicate the exact logic from Dashboard.jsx
function getStatusColor(status) {
  switch (status) {
    case 'good': return 'bg-emerald-100 text-emerald-700 border border-emerald-200';
    case 'warning': return 'bg-amber-100 text-amber-700 border border-amber-200';
    case 'critical': return 'bg-rose-100 text-rose-700 border border-rose-200';
    default: return 'bg-slate-100 text-slate-700 border border-slate-200';
  }
}

function getStatusDot(status) {
  switch (status) {
    case 'good': return 'bg-emerald-500';
    case 'warning': return 'bg-amber-500';
    case 'critical': return 'bg-rose-500';
    default: return 'bg-slate-400';
  }
}

function getSeverityColor(severity) {
  switch (severity) {
    case 'critical': return 'bg-rose-50 text-rose-700 border-rose-200';
    case 'high': return 'bg-orange-50 text-orange-700 border-orange-200';
    case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
    default: return 'bg-sky-50 text-sky-700 border-sky-200';
  }
}

import { describe, it, expect } from 'vitest';

describe('getStatusColor', () => {
  it('returns emerald classes for good status', () => {
    expect(getStatusColor('good')).toContain('bg-emerald-100');
    expect(getStatusColor('good')).toContain('text-emerald-700');
  });

  it('returns amber classes for warning status', () => {
    expect(getStatusColor('warning')).toContain('bg-amber-100');
    expect(getStatusColor('warning')).toContain('text-amber-700');
  });

  it('returns rose classes for critical status', () => {
    expect(getStatusColor('critical')).toContain('bg-rose-100');
    expect(getStatusColor('critical')).toContain('text-rose-700');
  });

  it('returns slate classes for unknown status', () => {
    expect(getStatusColor('unknown')).toContain('bg-slate-100');
    expect(getStatusColor('unknown')).toContain('text-slate-700');
  });
});

describe('getStatusDot', () => {
  it('returns emerald dot for good', () => {
    expect(getStatusDot('good')).toBe('bg-emerald-500');
  });

  it('returns amber dot for warning', () => {
    expect(getStatusDot('warning')).toBe('bg-amber-500');
  });

  it('returns rose dot for critical', () => {
    expect(getStatusDot('critical')).toBe('bg-rose-500');
  });

  it('returns slate dot for unknown', () => {
    expect(getStatusDot('unknown')).toBe('bg-slate-400');
  });
});

describe('getSeverityColor', () => {
  it('returns rose for critical severity', () => {
    expect(getSeverityColor('critical')).toContain('bg-rose-50');
    expect(getSeverityColor('critical')).toContain('text-rose-700');
  });

  it('returns orange for high severity', () => {
    expect(getSeverityColor('high')).toContain('bg-orange-50');
    expect(getSeverityColor('high')).toContain('text-orange-700');
  });

  it('returns amber for medium severity', () => {
    expect(getSeverityColor('medium')).toContain('bg-amber-50');
    expect(getSeverityColor('medium')).toContain('text-amber-700');
  });

  it('returns sky for low/default severity', () => {
    expect(getSeverityColor('low')).toContain('bg-sky-50');
    expect(getSeverityColor('low')).toContain('text-sky-700');
  });
});
