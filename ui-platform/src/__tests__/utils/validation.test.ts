import { describe, it, expect } from 'vitest';
import * as validation from '../../utils/validation';

describe('Validation Utilities', () => {
  describe('isValidEmail', () => {
    it('validates correct email addresses', () => {
      expect(validation.isValidEmail('user@example.com')).toBe(true);
      expect(validation.isValidEmail('john.doe+tag@company.co.uk')).toBe(true);
    });

    it('rejects invalid email addresses', () => {
      expect(validation.isValidEmail('notanemail')).toBe(false);
      expect(validation.isValidEmail('user@')).toBe(false);
      expect(validation.isValidEmail('user@domain')).toBe(false);
    });
  });

  describe('isValidPassword', () => {
    it('validates strong passwords', () => {
      expect(validation.isValidPassword('SecurePass123!')).toBe(true);
      expect(validation.isValidPassword('MyP@ssw0rd')).toBe(true);
    });

    it('rejects weak passwords', () => {
      expect(validation.isValidPassword('short')).toBe(false);
      expect(validation.isValidPassword('NoNumbers!')).toBe(false);
      expect(validation.isValidPassword('nouppercase123!')).toBe(false);
      expect(validation.isValidPassword('NOLOWERCASE123!')).toBe(false);
    });
  });

  describe('getPasswordStrength', () => {
    it('rates password strength', () => {
      expect(validation.getPasswordStrength('weak')).toBe('weak');
      expect(validation.getPasswordStrength('Better1!')).toBe('fair');
      expect(validation.getPasswordStrength('StrongPass123!')).toBe('strong');
    });
  });

  describe('isValidURL', () => {
    it('validates correct URLs', () => {
      expect(validation.isValidURL('https://example.com')).toBe(true);
      expect(validation.isValidURL('http://subdomain.example.co.uk/path')).toBe(true);
    });

    it('rejects invalid URLs', () => {
      expect(validation.isValidURL('not a url')).toBe(false);
      expect(validation.isValidURL('example.com')).toBe(false);
    });
  });

  describe('isValidPhoneNumber', () => {
    it('validates phone numbers', () => {
      expect(validation.isValidPhoneNumber('+1-555-123-4567')).toBe(true);
      expect(validation.isValidPhoneNumber('555-123-4567')).toBe(true);
      expect(validation.isValidPhoneNumber('+44 20 7946 0958')).toBe(true);
    });

    it('rejects invalid phone numbers', () => {
      expect(validation.isValidPhoneNumber('123')).toBe(false);
      expect(validation.isValidPhoneNumber('not a phone')).toBe(false);
    });
  });

  describe('isValidTenantName', () => {
    it('validates tenant names', () => {
      expect(validation.isValidTenantName('Acme Corporation')).toBe(true);
      expect(validation.isValidTenantName('Company-123')).toBe(true);
      expect(validation.isValidTenantName('Valid Name')).toBe(true);
    });

    it('rejects invalid tenant names', () => {
      expect(validation.isValidTenantName('A')).toBe(false);
      expect(validation.isValidTenantName('')).toBe(false);
      expect(validation.isValidTenantName('!@#$%')).toBe(false);
    });
  });

  describe('sanitizeInput', () => {
    it('removes potentially harmful content', () => {
      expect(validation.sanitizeInput('<script>alert("xss")</script>')).not.toContain('<script>');
      expect(validation.sanitizeInput('Hello & World')).toBe('Hello & World');
    });
  });

  describe('validateQuotaUsage', () => {
    it('validates quota usage ratios', () => {
      expect(validation.validateQuotaUsage(50, 100)).toBe(true);
      expect(validation.validateQuotaUsage(100, 100)).toBe(true);
      expect(validation.validateQuotaUsage(101, 100)).toBe(false);
    });
  });

  describe('isQuotaExceeded', () => {
    it('detects quota exceeded', () => {
      expect(validation.isQuotaExceeded(150, 100)).toBe(true);
      expect(validation.isQuotaExceeded(100, 100)).toBe(false);
      expect(validation.isQuotaExceeded(50, 100)).toBe(false);
    });
  });

  describe('isQuotaWarning', () => {
    it('detects quota warnings', () => {
      expect(validation.isQuotaWarning(95, 100)).toBe(true); // 95%
      expect(validation.isQuotaWarning(75, 100)).toBe(true); // 75%
      expect(validation.isQuotaWarning(50, 100)).toBe(false); // 50%
      expect(validation.isQuotaWarning(40, 100)).toBe(false); // 40%
    });
  });

  describe('validateLoginForm', () => {
    it('validates complete login forms', () => {
      const validForm = {
        email: 'user@example.com',
        password: 'SecurePass123!',
      };
      expect(validation.validateLoginForm(validForm).valid).toBe(true);
    });

    it('rejects invalid login forms', () => {
      const invalidForm = {
        email: 'notanemail',
        password: 'weak',
      };
      expect(validation.validateLoginForm(invalidForm).valid).toBe(false);
    });
  });

  describe('hasValidationErrors', () => {
    it('detects validation errors', () => {
      const errorsPresent = { email: 'Invalid email' };
      expect(validation.hasValidationErrors(errorsPresent)).toBe(true);

      const noErrors = {};
      expect(validation.hasValidationErrors(noErrors)).toBe(false);
    });
  });
});
