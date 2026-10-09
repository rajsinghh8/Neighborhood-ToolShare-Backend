export function validateRequired(value: string, label: string): string {
  return value.trim() ? '' : `${label} is required`
}

export function validateOptionalEmail(value: string): string {
  if (!value.trim()) return ''
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()) ? '' : 'Enter a valid email address'
}

export function validateOptionalPhone(value: string): string {
  if (!value.trim()) return ''
  return /^\+?[0-9\s-]{7,15}$/.test(value.trim()) ? '' : 'Enter a valid phone number (7-15 digits)'
}

export function validateClassLevel(value: number): string {
  return Number.isInteger(value) && value >= 1 && value <= 12 ? '' : 'Class must be between 1 and 12'
}
