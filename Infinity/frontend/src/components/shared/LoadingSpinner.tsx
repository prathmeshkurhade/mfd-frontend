import { cn } from '@/lib/utils'

export default function LoadingSpinner({ className, size = 'md' }: { className?: string; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }[size]
  return (
    <div className={cn('flex items-center justify-center p-8', className)}>
      <div className={cn('animate-spin rounded-full border-b-2 border-primary-600', sizeClass)} />
    </div>
  )
}
