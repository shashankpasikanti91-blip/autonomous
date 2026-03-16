/**
 * Validation Utilities
 * Common validation functions
 */

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidPassword(password: string): boolean {
  // At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special char
  const passwordRegex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
}

export function getPasswordStrength(password: string): "weak" | "fair" | "good" | "strong" {
  let score = 0;

  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[@$!%*?&]/.test(password)) score++;

  if (score <= 1) return "weak";
  if (score <= 2) return "fair";
  if (score <= 3) return "good";
  return "strong";
}

export function isValidURL(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function isValidPhoneNumber(phone: string): boolean {
  // Basic validation - adjust regex based on your requirements
  const phoneRegex = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/;
  return phoneRegex.test(phone.replace(/\s/g, ""));
}

export function isValidTenantName(name: string): boolean {
  return name.length >= 3 && name.length <= 255 && /^[a-zA-Z0-9\s-_]+$/.test(name);
}

export function isValidAppName(name: string): boolean {
  return name.length >= 1 && name.length <= 255 && /^[a-zA-Z0-9\s-_]+$/.test(name);
}

export function sanitizeInput(input: string): string {
  return input.replace(/[<>]/g, "");
}

export function validateQuotaUsage(used: number, limit: number): boolean {
  return used >= 0 && limit > 0 && used <= limit;
}

export function getQuotaPercentage(used: number, limit: number): number {
  if (limit === 0) return 0;
  return Math.min(100, (used / limit) * 100);
}

export function isQuotaExceeded(used: number, limit: number): boolean {
  return used > limit;
}

export function isQuotaWarning(used: number, limit: number, threshold = 80): boolean {
  return getQuotaPercentage(used, limit) >= threshold && !isQuotaExceeded(used, limit);
}

export interface ValidationError {
  field: string;
  message: string;
}

export function validateLoginForm(email: string, password: string): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!email) {
    errors.push({ field: "email", message: "Email is required" });
  } else if (!isValidEmail(email)) {
    errors.push({ field: "email", message: "Invalid email format" });
  }

  if (!password) {
    errors.push({ field: "password", message: "Password is required" });
  } else if (password.length < 6) {
    errors.push({ field: "password", message: "Password must be at least 6 characters" });
  }

  return errors;
}

export function validateUserForm(
  email: string,
  password: string,
  confirmPassword: string
): ValidationError[] {
  const errors = validateLoginForm(email, password);

  if (password !== confirmPassword) {
    errors.push({ field: "confirmPassword", message: "Passwords do not match" });
  }

  return errors;
}

export function hasValidationErrors(errors: ValidationError[]): boolean {
  return errors.length > 0;
}

export function getFieldError(
  errors: ValidationError[],
  field: string
): string | undefined {
  return errors.find((e) => e.field === field)?.message;
}
