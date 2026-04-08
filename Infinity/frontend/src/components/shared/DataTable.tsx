import { useState } from 'react'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface Column<T> {
  key: string
  label: string
  sortable?: boolean
  render?: (item: T) => React.ReactNode
  className?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  total: number
  page: number
  limit: number
  totalPages: number
  onPageChange: (page: number) => void
  onSort?: (key: string, order: 'asc' | 'desc') => void
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onRowClick?: (item: T) => void
  loading?: boolean
  emptyMessage?: string
  actions?: (item: T) => React.ReactNode
}

export default function DataTable<T extends { id: string }>({
  columns,
  data,
  total,
  page,
  limit,
  totalPages,
  onPageChange,
  onSort,
  sortBy,
  sortOrder,
  onRowClick,
  loading,
  emptyMessage = 'No data found',
  actions,
}: DataTableProps<T>) {
  const handleSort = (key: string) => {
    if (!onSort) return
    const newOrder = sortBy === key && sortOrder === 'asc' ? 'desc' : 'asc'
    onSort(key, newOrder)
  }

  const SortIcon = ({ columnKey }: { columnKey: string }) => {
    if (sortBy !== columnKey) return <ArrowUpDown size={14} className="text-gray-400" />
    return sortOrder === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
  }

  if (loading) {
    return (
      <div className="card">
        <div className="p-8 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider',
                    col.sortable && 'cursor-pointer hover:text-gray-900 select-none',
                    col.className
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && <SortIcon columnKey={col.key} />}
                  </div>
                </th>
              ))}
              {actions && <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-12 text-center text-gray-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((item) => (
                <tr
                  key={item.id}
                  className={cn(
                    'border-b border-gray-100 hover:bg-gray-50 transition-colors',
                    onRowClick && 'cursor-pointer'
                  )}
                  onClick={() => onRowClick?.(item)}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={cn('px-4 py-3 text-sm', col.className)}>
                      {col.render ? col.render(item) : (item as Record<string, unknown>)[col.key] as string}
                    </td>
                  ))}
                  {actions && (
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      {actions(item)}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total}
          </p>
          <div className="flex items-center gap-1">
            <button onClick={() => onPageChange(1)} disabled={page === 1} className="p-1 rounded hover:bg-gray-100 disabled:opacity-50">
              <ChevronsLeft size={18} />
            </button>
            <button onClick={() => onPageChange(page - 1)} disabled={page === 1} className="p-1 rounded hover:bg-gray-100 disabled:opacity-50">
              <ChevronLeft size={18} />
            </button>
            <span className="px-3 py-1 text-sm">Page {page} of {totalPages}</span>
            <button onClick={() => onPageChange(page + 1)} disabled={page === totalPages} className="p-1 rounded hover:bg-gray-100 disabled:opacity-50">
              <ChevronRight size={18} />
            </button>
            <button onClick={() => onPageChange(totalPages)} disabled={page === totalPages} className="p-1 rounded hover:bg-gray-100 disabled:opacity-50">
              <ChevronsRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
