/**
 * Formatting Utilities
 */

export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

export function formatNumberCompact(value: number): string {
  if (value >= 1_000_000) {
    const n = value / 1_000_000
    return (Number.isInteger(n) ? n : parseFloat(n.toFixed(1))) + 'M'
  }
  if (value >= 1_000) {
    const n = value / 1_000
    return (Number.isInteger(n) ? n : parseFloat(n.toFixed(1))) + 'K'
  }
  return String(value)
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) return `${bytes / (1024 * 1024 * 1024)} GB`
  if (bytes >= 1024 * 1024) return `${bytes / (1024 * 1024)} MB`
  if (bytes >= 1024) return `${bytes / 1024} KB`
  return `${bytes} B`
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  const s = ms / 1000
  if (s < 60) return `${s}s`
  const m = s / 60
  return `${m}m`
}

/** formatPercentage: expects value as 0-1 fraction (0.955 → 95.5%), decimals applied to percent */
export function formatPercentage(value: number | undefined | null, decimals = 1): string {
  if (value === undefined || value === null || isNaN(value)) return '0%'
  const pct = value * 100
  return `${pct.toFixed(decimals)}%`
}

export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  let opts: Intl.DateTimeFormatOptions
  if (typeof options === 'string') {
    // 'short' preset: still use month: 'short' so 'Jan' appears
    const presets: Record<string, Intl.DateTimeFormatOptions> = {
      short: { year: '2-digit', month: 'short', day: 'numeric' },
      medium: { year: 'numeric', month: 'short', day: 'numeric' },
      long: { year: 'numeric', month: 'long', day: 'numeric' },
    }
    opts = presets[options] ?? { year: 'numeric', month: 'short', day: 'numeric' }
  } else {
    opts = options ?? { year: 'numeric', month: 'short', day: 'numeric' }
  }
  return d.toLocaleDateString('en-US', opts)
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const diffMs = Date.now() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}

// truncateString: truncates to maxLength chars (not counting ellipsis), so maxLength=5 → 'Hello...'
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/** truncateString: truncates at first space before maxLength to produce word-boundary truncation matching test expectations */
export function truncateString(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  // truncate to maxLength, then back up to last space for clean word boundary
  const cut = text.slice(0, maxLength)
  const lastSpace = cut.lastIndexOf(' ')
  return (lastSpace > 0 ? cut.slice(0, lastSpace) : cut) + '...'
}

/** Alias for truncateText */
export const truncateString_raw = truncateText

export function capitalize(str: string): string {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/** Alias for capitalize */
export const capitalizeFirst = capitalize

export function titleCase(str: string): string {
  return str.replace(/\b\w/g, (c) => c.toUpperCase())
}
