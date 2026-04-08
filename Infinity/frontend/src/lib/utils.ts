import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { format, formatDistanceToNow, isToday, isTomorrow, isYesterday, parseISO } from 'date-fns'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? parseISO(date) : date
  if (isToday(d)) return 'Today'
  if (isTomorrow(d)) return 'Tomorrow'
  if (isYesterday(d)) return 'Yesterday'
  return format(d, 'MMM d, yyyy')
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? parseISO(date) : date
  return format(d, 'MMM d, yyyy h:mm a')
}

export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? parseISO(date) : date
  return formatDistanceToNow(d, { addSuffix: true })
}

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '-'
  if (amount >= 10000000) return `${(amount / 10000000).toFixed(2)} Cr`
  if (amount >= 100000) return `${(amount / 100000).toFixed(2)} L`
  if (amount >= 1000) return `${(amount / 1000).toFixed(1)}K`
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

export function formatCurrencyFull(amount: number | null | undefined): string {
  if (amount == null) return '-'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null) return '-'
  return `${value.toFixed(1)}%`
}

export function formatPhone(phone: string | null | undefined): string {
  if (!phone) return '-'
  if (phone.startsWith('+91') && phone.length === 13) {
    return `+91 ${phone.slice(3, 8)} ${phone.slice(8)}`
  }
  return phone
}

/**
 * Normalize phone to +91XXXXXXXXXX format.
 * Strips spaces, dashes, brackets, leading 0s, and adds +91 if missing.
 */
export function normalizePhone(phone: string | null | undefined): string {
  if (!phone) return ''
  // Remove all non-digit characters except leading +
  let digits = phone.replace(/[^0-9]/g, '')
  // Remove leading 0s (e.g. 0XXXXXXXXXX)
  digits = digits.replace(/^0+/, '')
  // If starts with 91 and has 12 digits, strip the 91 prefix
  if (digits.startsWith('91') && digits.length === 12) {
    digits = digits.slice(2)
  }
  // Should now be 10 digits
  if (digits.length === 10) {
    return `+91${digits}`
  }
  // Return as-is if can't normalize (let backend validation catch it)
  return phone.trim()
}

export function enumToLabel(value: string | null | undefined): string {
  if (!value) return '-'
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function getInitials(name: string | null | undefined): string {
  if (!name) return '?'
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.response?.data?.message || error.message
  }
  if (error instanceof Error) return error.message
  return 'An unexpected error occurred'
}

import axios from 'axios'
