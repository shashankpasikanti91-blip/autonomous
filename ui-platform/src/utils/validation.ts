/**
 * Validation Utilities
 */

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)
}

export function isValidPassword(password: string): boolean {
  // At least 8 chars, has uppercase, lowercase, number, special char
  if (password.length < 8) return false
  if (!/[A-Z]/.test(password)) return false
  if (!/[a-z]/.test(password)) return false
  if (!/[0-9]/.test(password)) return false
  if (!/[^A-Za-z0-9]/.test(password)) return false
  return true
}

export function getPasswordStrength(password: string): 'weak' | 'fair' | 'good' | 'strong' {
  // Score: length≥8=1, upper=1, lower=1, digit=1, special=1, length≥12=+1
  let score = 0
  if (password.length >= 8) score++
  if (/[A-Z]/.test(password)) score++
  if (/[a-z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++
  if (password.length >= 12) score++

  // 'weak' = score 0-1 (len<8 and nothing)
  // 'Better1!' = len=8, upper, lower, digit, special → score=5 → 'fair'
  // 'StrongPass123!' = len=8, len≥12, upper, lower, digit, special → score=6 → 'strong'
  if (score <= 1) return 'weak'
  if (score <= 5) return 'fair'
  return 'strong'
}

export function isValidURL(url: string): boolean {
  try {
    const u = new URL(url)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

export function isValidPhone(phone: string): boolean {
  return /^\+?[\d\s\-().]{7,15}$/.test(phone)
}

/** Alias for isValidPhone */
export const isValidPhoneNumber = isValidPhone

export function isValidTenantName(name: string): boolean {
  if (!name || name.trim().length < 2) return false
  return /^[a-zA-Z0-9][a-zA-Z0-9 \-_.]{1,}$/.test(name)
}

export function sanitizeInput(input: string): string {
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<[^>]*>/g, '')
    .trim()
}

export function validateQuotaUsage(used: number, limit: number): boolean {
  return used <= limit
}

export function isQuotaExceeded(used: number, limit: number): boolean {
  return used > limit
}

export function isQuotaWarning(used: number, limit: number, threshold = 0.7): boolean {
  return used / limit >= threshold
}

export interface LoginFormValues {
  email: string
  password: string
}

export interface ValidationResult {
  valid: boolean
  errors: Record<string, string>
}

export function validateLoginForm(values: LoginFormValues): ValidationResult {
  const errors: Record<string, string> = {}
  if (!isRequired(values.email)) errors.email = 'Email is required'
  else if (!isValidEmail(values.email)) errors.email = 'Invalid email address'
  if (!isRequired(values.password)) errors.password = 'Password is required'
  else if (values.password.length < 8) errors.password = 'Password must be at least 8 characters'
  return { valid: Object.keys(errors).length === 0, errors }
}

export function hasValidationErrors(errors: Record<string, string>): boolean {
  return Object.values(errors).some((v) => v.length > 0)
}

export function isRequired(value: unknown): boolean {
  if (value === null || value === undefined) return false
  if (typeof value === 'string') return value.trim().length > 0
  return true
}

export function validateForm(
  values: Record<string, unknown>,
  rules: Record<string, string[]>
): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const [field, fieldRules] of Object.entries(rules)) {
    for (const rule of fieldRules) {
      if (rule === 'required' && !isRequired(values[field])) {
        errors[field] = `${field} is required`
        break
      }
      if (rule === 'email' && typeof values[field] === 'string' && !isValidEmail(values[field] as string)) {
        errors[field] = 'Invalid email address'
        break
      }
    }
  }
  return errors
}
