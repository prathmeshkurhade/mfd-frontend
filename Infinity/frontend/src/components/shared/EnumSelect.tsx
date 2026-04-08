import { cn } from '@/lib/utils'

interface EnumSelectProps {
  options: readonly { value: string; label: string }[]
  value: string | null | undefined
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  allowEmpty?: boolean
  emptyLabel?: string
  disabled?: boolean
}

export default function EnumSelect({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  className,
  allowEmpty = false,
  emptyLabel = 'All',
  disabled = false,
}: EnumSelectProps) {
  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      className={cn('input-field', className)}
      disabled={disabled}
    >
      {allowEmpty && <option value="">{emptyLabel}</option>}
      {!allowEmpty && !value && <option value="" disabled>{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
