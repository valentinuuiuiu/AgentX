import { describe, it, expect } from 'vitest';
import { cn } from './utils';

describe('cn utility', () => {
  it('should merge class names', () => {
    expect(cn('class1', 'class2')).toBe('class1 class2');
  });

  it('should handle conditional classes', () => {
    expect(cn('class1', true && 'class2', false && 'class3')).toBe('class1 class2');
  });

  it('should handle arrays of classes', () => {
    expect(cn(['class1', 'class2'], 'class3')).toBe('class1 class2 class3');
  });

  it('should handle object notation', () => {
    expect(cn({ class1: true, class2: false, class3: true })).toBe('class1 class3');
  });

  it('should handle falsy values', () => {
    expect(cn('class1', null, undefined, 0, false, '', 'class2')).toBe('class1 class2');
  });

  it('should merge tailwind classes properly', () => {
    expect(cn('p-4 px-2')).toBe('p-4 px-2');
    expect(cn('p-4', 'p-2')).toBe('p-2');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500');
    expect(cn('flex', 'inline-flex')).toBe('inline-flex');
  });

  it('should correctly merge complex tailwind classes', () => {
    expect(
      cn(
        'text-sm font-medium transition-colors hover:bg-slate-100 hover:text-slate-900',
        'bg-transparent',
        true && 'text-slate-900',
        false && 'text-slate-500'
      )
    ).toBe('text-sm font-medium transition-colors hover:bg-slate-100 hover:text-slate-900 bg-transparent text-slate-900');
  });
});
