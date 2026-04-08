import { cn } from '@/lib/utils'

const statusColors: Record<string, string> = {
  // Lead status
  follow_up: 'bg-blue-100 text-blue-700',
  meeting_scheduled: 'bg-purple-100 text-purple-700',
  converted: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  // Task status
  pending: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  carried_forward: 'bg-orange-100 text-orange-700',
  // Touchpoint
  scheduled: 'bg-blue-100 text-blue-700',
  rescheduled: 'bg-orange-100 text-orange-700',
  // BO outcome
  open: 'bg-blue-100 text-blue-700',
  won: 'bg-green-100 text-green-700',
  lost: 'bg-red-100 text-red-700',
  // BO stages
  identified: 'bg-gray-100 text-gray-700',
  inbound: 'bg-blue-100 text-blue-700',
  proposed: 'bg-purple-100 text-purple-700',
  // Goal status
  active: 'bg-blue-100 text-blue-700',
  on_track: 'bg-green-100 text-green-700',
  behind: 'bg-red-100 text-red-700',
  achieved: 'bg-emerald-100 text-emerald-700',
  paused: 'bg-gray-100 text-gray-700',
  // Priority
  high: 'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
  // Product
  stopped: 'bg-gray-100 text-gray-700',
  redeemed: 'bg-orange-100 text-orange-700',
  matured: 'bg-green-100 text-green-700',
  lapsed: 'bg-red-100 text-red-700',
  surrendered: 'bg-red-100 text-red-700',
}

interface StatusBadgeProps {
  status: string | null | undefined
  className?: string
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  if (!status) return null
  const colorClass = statusColors[status] || 'bg-gray-100 text-gray-700'
  const label = status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', colorClass, className)}>
      {label}
    </span>
  )
}
