import { useState, useEffect } from 'react'
import { Sun, Clock, Moon, RefreshCw } from 'lucide-react'
import apiClient from '@/lib/api-client'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import StatusBadge from '@/components/shared/StatusBadge'
import { formatDate, formatCurrency } from '@/lib/utils'
import { toast } from 'sonner'

export default function SchedulerPage() {
  const [activeTab, setActiveTab] = useState<'morning' | 'progress' | 'eod'>('morning')
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      const endpoints = { morning: '/scheduler/daily-schedule', progress: '/scheduler/progress', eod: '/scheduler/eod-summary' }
      const { data } = await apiClient.get(endpoints[activeTab])
      setData(data)
    } catch { toast.error('Failed to load schedule') }
    finally { setLoading(false) }
  }

  const scheduleToday = async () => {
    try {
      await apiClient.post('/scheduler/notifications/schedule-today')
      toast.success('Notifications scheduled for today')
    } catch { toast.error('Failed to schedule') }
  }

  const tabs = [
    { key: 'morning' as const, label: 'Daily Schedule', icon: Sun },
    { key: 'progress' as const, label: 'Progress', icon: Clock },
    { key: 'eod' as const, label: 'EOD Summary', icon: Moon },
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Scheduler</h1>
        <button onClick={scheduleToday} className="btn-primary flex items-center gap-2"><RefreshCw size={18} /> Schedule Today</button>
      </div>

      <div className="flex gap-1 border-b border-gray-200">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)} className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeTab === key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner /> : (
        <div className="card p-6">
          {data ? (
            <div className="space-y-4">
              {activeTab === 'morning' && (
                <>
                  <h3 className="font-semibold">Today's Schedule</h3>
                  {(data as Record<string, unknown[]>).tasks?.length > 0 && (
                    <div><h4 className="text-sm font-medium text-gray-500 mb-2">Tasks</h4>
                      {((data as Record<string, unknown[]>).tasks as Record<string, unknown>[]).map((t, i) => (
                        <div key={i} className="p-2 bg-gray-50 rounded mb-1 text-sm">{(t as Record<string, string>).title || (t as Record<string, string>).description || JSON.stringify(t)}</div>
                      ))}
                    </div>
                  )}
                  {(data as Record<string, unknown[]>).touchpoints?.length > 0 && (
                    <div><h4 className="text-sm font-medium text-gray-500 mb-2">Touchpoints</h4>
                      {((data as Record<string, unknown[]>).touchpoints as Record<string, unknown>[]).map((t, i) => (
                        <div key={i} className="p-2 bg-gray-50 rounded mb-1 text-sm">{(t as Record<string, string>).client_name || ''} - {(t as Record<string, string>).interaction_type || ''}</div>
                      ))}
                    </div>
                  )}
                  {(data as Record<string, unknown[]>).birthdays?.length > 0 && (
                    <div><h4 className="text-sm font-medium text-gray-500 mb-2">Birthdays</h4>
                      {((data as Record<string, unknown[]>).birthdays as Record<string, unknown>[]).map((b, i) => (
                        <div key={i} className="p-2 bg-yellow-50 rounded mb-1 text-sm">{(b as Record<string, string>).name}</div>
                      ))}
                    </div>
                  )}
                </>
              )}
              {activeTab === 'progress' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-green-50 rounded-lg"><p className="text-sm text-green-700">Completed</p><p className="text-2xl font-bold text-green-800">{(data as Record<string, number>).completed_count || 0}</p></div>
                    <div className="p-4 bg-yellow-50 rounded-lg"><p className="text-sm text-yellow-700">Remaining</p><p className="text-2xl font-bold text-yellow-800">{(data as Record<string, number>).remaining_count || 0}</p></div>
                  </div>
                </>
              )}
              {activeTab === 'eod' && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-green-50 rounded-lg"><p className="text-sm text-green-700">Completed</p><p className="text-2xl font-bold text-green-800">{(data as Record<string, number>).completed_count || 0}</p></div>
                    <div className="p-4 bg-orange-50 rounded-lg"><p className="text-sm text-orange-700">Carry Forward</p><p className="text-2xl font-bold text-orange-800">{(data as Record<string, number>).carry_forward_count || 0}</p></div>
                  </div>
                </>
              )}
              <details className="mt-4">
                <summary className="text-sm text-gray-500 cursor-pointer">Raw Data</summary>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-x-auto">{JSON.stringify(data, null, 2)}</pre>
              </details>
            </div>
          ) : (
            <p className="text-center text-gray-500">No data available</p>
          )}
        </div>
      )}
    </div>
  )
}
