/**
 * Tests for LanguageContext — language switching and translation lookup.
 */
import { describe, it, expect } from 'vitest';
import { render, renderHook, act } from '@testing-library/react';
import { LanguageProvider, useLanguage } from '../contexts/LanguageContext';

function wrapper({ children }) {
  return <LanguageProvider>{children}</LanguageProvider>;
}

describe('LanguageContext', () => {
  it('defaults to English', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.language).toBe('en');
  });

  it('switches to Hindi', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => {
      result.current.setLanguage('hi');
    });
    expect(result.current.language).toBe('hi');
  });

  it('switches to Kannada', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => {
      result.current.setLanguage('kn');
    });
    expect(result.current.language).toBe('kn');
  });

  it('returns English text for known key in English mode', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.t('dashboard')).toBe('Dashboard');
  });

  it('returns Hindi text for known key after switching to Hindi', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => {
      result.current.setLanguage('hi');
    });
    expect(result.current.t('dashboard')).toBe('डैशबोर्ड');
  });

  it('returns Kannada text for known key after switching to Kannada', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => {
      result.current.setLanguage('kn');
    });
    expect(result.current.t('dashboard')).toBe('ಡ್ಯಾಶ್‌ಬೋರ್ಡ್');
  });

  it('falls back to English for unknown key', () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => {
      result.current.setLanguage('hi');
    });
    expect(result.current.t('nonexistent_key_xyz')).toBe('nonexistent_key_xyz');
  });
});
