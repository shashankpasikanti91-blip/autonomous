import { describe, it, expect } from 'vitest';
import * as formatting from '../../utils/formatting';

describe('Formatting Utilities', () => {
  describe('formatCurrency', () => {
    it('formats USD currency correctly', () => {
      expect(formatting.formatCurrency(1234.56, 'USD')).toBe('$1,234.56');
      expect(formatting.formatCurrency(10000000, 'USD')).toBe('$10,000,000.00');
      expect(formatting.formatCurrency(0.99, 'USD')).toBe('$0.99');
    });

    it('formats EUR currency correctly', () => {
      expect(formatting.formatCurrency(1234.56, 'EUR')).toContain('1,234.56');
    });

    it('handles zero and negative values', () => {
      expect(formatting.formatCurrency(0, 'USD')).toBe('$0.00');
      expect(formatting.formatCurrency(-100, 'USD')).toBe('-$100.00');
    });
  });

  describe('formatNumberCompact', () => {
    it('formats numbers to compact format', () => {
      expect(formatting.formatNumberCompact(1200000)).toBe('1.2M');
      expect(formatting.formatNumberCompact(1200)).toBe('1.2K');
      expect(formatting.formatNumberCompact(999)).toBe('999');
      expect(formatting.formatNumberCompact(1234567)).toBe('1.2M');
    });
  });

  describe('formatBytes', () => {
    it('formats bytes to human readable', () => {
      expect(formatting.formatBytes(1024)).toBe('1 KB');
      expect(formatting.formatBytes(1024 * 1024)).toBe('1 MB');
      expect(formatting.formatBytes(1024 * 1024 * 1024)).toBe('1 GB');
      expect(formatting.formatBytes(512)).toBe('512 B');
    });
  });

  describe('formatDuration', () => {
    it('formats milliseconds to readable duration', () => {
      expect(formatting.formatDuration(500)).toBe('500ms');
      expect(formatting.formatDuration(1500)).toBe('1.5s');
      expect(formatting.formatDuration(60000)).toBe('1m');
      expect(formatting.formatDuration(150000)).toBe('2.5m');
    });
  });

  describe('formatPercentage', () => {
    it('formats percentages correctly', () => {
      expect(formatting.formatPercentage(0.955, 1)).toBe('95.5%');
      expect(formatting.formatPercentage(0.333, 2)).toBe('33.30%');
      expect(formatting.formatPercentage(1, 0)).toBe('100%');
    });
  });

  describe('formatDate', () => {
    it('formats date in short format', () => {
      const date = new Date('2024-01-15T00:00:00Z');
      const formatted = formatting.formatDate(date, 'short');
      expect(formatted).toContain('Jan');
      expect(formatted).toContain('15');
    });
  });

  describe('truncateString', () => {
    it('truncates strings correctly', () => {
      expect(formatting.truncateString('Hello World', 5)).toBe('Hello...');
      expect(formatting.truncateString('Hi', 5)).toBe('Hi');
      expect(formatting.truncateString('Testing truncation', 10)).toBe('Testing...');
    });
  });

  describe('capitalizeFirst', () => {
    it('capitalizes first letter', () => {
      expect(formatting.capitalizeFirst('hello')).toBe('Hello');
      expect(formatting.capitalizeFirst('WORLD')).toBe('WORLD');
      expect(formatting.capitalizeFirst('a')).toBe('A');
    });
  });

  describe('titleCase', () => {
    it('converts to title case', () => {
      expect(formatting.titleCase('hello world')).toBe('Hello World');
      expect(formatting.titleCase('the quick brown fox')).toBe('The Quick Brown Fox');
    });
  });
});
