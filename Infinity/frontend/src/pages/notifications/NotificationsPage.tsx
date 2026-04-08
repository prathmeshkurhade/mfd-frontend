import { useState, useEffect } from 'react'
import { Bell, Check, Trash2 } from 'lucide-react'
import apiClient from '@/lib/api-client'
import { formatRelativeTime, cn } from '@/lib/utils'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import EmptyState from '@/components/shared/EmptyState'
import type { Notification } from '@/types'
import { toast } from 'sonner'

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [total, setTotal] = useState(0)
  const [unreadCount, setUnreadCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  useEffect(() => { loadNotifications() }, [page, filter])

  const loadNotifications = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/notifications', { params: { page, limit: 20, unread_only: filter === 'unread' } })
      setNotifications(data.notifications)
      setTotal(data.total)
      setUnreadCount(data.unread_count)
    } catch { toast.error('Failed to load notifications') }
    finally { setLoading(false) }
  }

  const markAsRead = async (ids: string[]) => {
    try {
      await apiClient.post('/notifications/mark-read', { notification_ids: ids })
      loadNotifications()
    } catch { toast.error('Failed to mark as read') }
  }

  const markAllRead = async () => {
    try {
      await apiClient.post('/notifications/mark-all-read')
      toast.success('All marked as read')
      loadNotifications()
    } catch { toast.error('Failed') }
  }

  const deleteNotification = async (id: string) => {
    try {
      await apiClient.delete(`/notifications/${id}`)
      loadNotifications()
    } catch { toast.error('Failed to delete') }
  }

  if (loading && page === 1) return <LoadingSpinner />

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <div className="flex items-center gap-3">
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button onClick={() => { setFilter('all'); setPage(1) }} className={`px-3 py-1.5 text-sm rounded-md ${filter === 'all' ? 'bg-white shadow font-medium' : 'text-gray-600'}`}>All</button>
            <button onClick={() => { setFilter('unread'); setPage(1) }} className={`px-3 py-1.5 text-sm rounded-md ${filter === 'unread' ? 'bg-white shadow font-medium' : 'text-gray-600'}`}>Unread ({unreadCount})</button>
          </div>
          {unreadCount > 0 && <button onClick={markAllRead} className="btn-secondary text-sm">Mark All Read</button>}
        </div>
      </div>

      <div className="card divide-y divide-gray-100">
        {notifications.length === 0 ? (
          <EmptyState icon={Bell} title="No notifications" description="You're all caught up!" />
        ) : (
          notifications.map((n) => (
            <div key={n.id} className={cn('p-4 flex items-start gap-3 hover:bg-gray-50', !n.is_read && 'bg-primary-50/30')}>
              <div className={cn('w-2 h-2 rounded-full mt-2 shrink-0', n.is_read ? 'bg-transparent' : 'bg-primary-500')} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{n.title}</p>
                <p className="text-sm text-gray-600 mt-0.5">{n.message}</p>
                <p className="text-xs text-gray-400 mt-1">{formatRelativeTime(n.created_at)}</p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {!n.is_read && <button onClick={() => markAsRead([n.id])} className="p-1 rounded hover:bg-gray-100" title="Mark read"><Check size={14} className="text-gray-400" /></button>}
                <button onClick={() => deleteNotification(n.id)} className="p-1 rounded hover:bg-gray-100" title="Delete"><Trash2 size={14} className="text-red-400" /></button>
              </div>
            </div>
          ))
        )}
      </div>

      {total > 20 && (
        <div className="flex justify-center gap-2">
          <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="btn-secondary text-sm">Previous</button>
          <span className="px-3 py-2 text-sm">Page {page}</span>
          <button onClick={() => setPage(page + 1)} disabled={notifications.length < 20} className="btn-secondary text-sm">Next</button>
        </div>
      )}
    </div>
  )
}
