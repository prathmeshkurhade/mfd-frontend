import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, UserPlus, Briefcase, TrendingUp, CheckSquare, Calendar, Cake, Plus, Download } from 'lucide-react'
import { format, addDays, subDays, isToday } from 'date-fns'
import apiClient from '@/lib/api-client'
import { formatCurrency, cn } from '@/lib/utils'
import StatCard from '@/components/shared/StatCard'
import StatusBadge from '@/components/shared/StatusBadge'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import type { DashboardStats, Task, Touchpoint, Lead, Client } from '@/types'
import { toast } from 'sonner'
import { supabase } from '@/lib/supabase'

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [todayData, setTodayData] = useState<{
    tasks: Task[]
    touchpoints: Touchpoint[]
    followups: Lead[]
    birthdays: Client[]
    opportunities: Array<Record<string, unknown>>
  } | null>(null)
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    loadStats()
  }, [])

  useEffect(() => {
    loadDailyData()
  }, [selectedDate])

  const loadStats = async () => {
    try {
      const statsRes = await apiClient.get('/dashboard/stats')
      setStats(statsRes.data)
    } catch (err) {
      toast.error('Failed to load dashboard stats')
    }
  }

  const loadDailyData = async () => {
    try {
      setLoading(true)
      const dateStr = format(selectedDate, 'yyyy-MM-dd')
      const { data } = await apiClient.get('/dashboard/today', { params: { target_date: dateStr } })
      setTodayData({
        tasks: data.tasks_pending || [],
        touchpoints: data.touchpoints_today || [],
        followups: data.leads_to_followup || [],
        birthdays: data.birthdays_today || [],
        opportunities: data.opportunities || [],
      })
    } catch {
      toast.error('Failed to load daily data')
    } finally {
      setLoading(false)
    }
  }

  const handleCompleteTask = async (taskId: string) => {
    try {
      await apiClient.post(`/tasks/${taskId}/complete`)
      toast.success('Task completed')
      loadDashboard()
    } catch {
      toast.error('Failed to complete task')
    }
  }

  const handleImportFromSheets = async () => {
    setImporting(true)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) {
        toast.error('Please log in again')
        return
      }

      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
      const res = await fetch(`${supabaseUrl}/functions/v1/import-from-sheet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({}),
      })

      const data = await res.json()

      if (res.ok) {
        toast.success('Data synced from Excel successfully!')
        loadDashboard()
      } else {
        toast.error(data?.error || 'Import failed')
      }
    } catch (err) {
      toast.error('Failed to connect to import service')
    } finally {
      setImporting(false)
    }
  }

  const handleCarryForward = async (taskId: string) => {
    const tomorrow = format(addDays(new Date(), 1), 'yyyy-MM-dd')
    try {
      await apiClient.post(`/tasks/${taskId}/carry-forward`, null, { params: { new_date: tomorrow } })
      toast.success('Task carried forward to tomorrow')
      loadDashboard()
    } catch {
      toast.error('Failed to carry forward task')
    }
  }

  // Date strip
  const dateRange = Array.from({ length: 7 }, (_, i) => addDays(subDays(new Date(), 3), i))

  if (loading) return <LoadingSpinner />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleImportFromSheets}
            disabled={importing}
            className="btn-secondary flex items-center gap-2"
          >
            <Download size={18} /> {importing ? 'Importing...' : 'Import from Sheets'}
          </button>
          <button onClick={() => navigate('/leads')} className="btn-primary flex items-center gap-2">
            <Plus size={18} /> Quick Add
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard title="Total Clients" value={stats?.total_clients || 0} icon={Users} onClick={() => navigate('/clients')} />
        <StatCard title="Total Leads" value={stats?.total_leads || 0} icon={UserPlus} onClick={() => navigate('/leads')} />
        <StatCard title="Portfolio Value" value={formatCurrency(stats?.total_aum || 0)} icon={TrendingUp} />
        <StatCard title="Pipeline Value" value={formatCurrency(stats?.total_pipeline_value || 0)} icon={Briefcase} onClick={() => navigate('/opportunities')} />
        <StatCard
          title="Conversion Rate"
          value={`${(stats?.conversion_rate || 0).toFixed(1)}%`}
          icon={TrendingUp}
        />
      </div>

      {/* Date Strip */}
      <div className="card p-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {dateRange.map((date) => (
            <button
              key={date.toISOString()}
              onClick={() => setSelectedDate(date)}
              className={cn(
                'flex flex-col items-center px-4 py-2 rounded-lg min-w-[70px] transition-colors',
                format(date, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd')
                  ? 'bg-primary-600 text-white'
                  : isToday(date)
                  ? 'bg-primary-50 text-primary-700'
                  : 'hover:bg-gray-100'
              )}
            >
              <span className="text-xs font-medium">{format(date, 'EEE')}</span>
              <span className="text-lg font-bold">{format(date, 'd')}</span>
              <span className="text-xs">{format(date, 'MMM')}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Overview Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard title="Opportunities" value={todayData?.opportunities?.length || 0} icon={Briefcase} />
        <StatCard title="Touchpoints" value={todayData?.touchpoints?.length || 0} icon={Calendar} />
        <StatCard title="Birthdays" value={todayData?.birthdays?.length || 0} icon={Cake} />
        <StatCard title="Tasks Today" value={todayData?.tasks?.length || 0} icon={CheckSquare} />
        <StatCard title="Follow-ups" value={todayData?.followups?.length || 0} icon={UserPlus} />
      </div>

      {/* Expandable Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tasks Section */}
        <div className="card">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <CheckSquare size={18} className="text-primary-600" /> Today's Tasks
            </h3>
            <button onClick={() => navigate('/tasks')} className="text-sm text-primary-600 hover:underline">View All</button>
          </div>
          <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
            {todayData?.tasks?.length === 0 && (
              <p className="p-4 text-sm text-gray-500 text-center">No tasks for today</p>
            )}
            {todayData?.tasks?.map((task) => (
              <div key={task.id} className="p-3 flex items-center justify-between hover:bg-gray-50">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{task.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <StatusBadge status={task.priority} />
                    {task.client_name && <span className="text-xs text-gray-500">{task.client_name}</span>}
                  </div>
                </div>
                {task.status === 'pending' && (
                  <div className="flex items-center gap-1 ml-2">
                    <button onClick={() => handleCompleteTask(task.id)} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200">Done</button>
                    <button onClick={() => handleCarryForward(task.id)} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded hover:bg-orange-200">CF</button>
                  </div>
                )}
                {task.status !== 'pending' && <StatusBadge status={task.status} />}
              </div>
            ))}
          </div>
        </div>

        {/* Touchpoints Section */}
        <div className="card">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <Calendar size={18} className="text-primary-600" /> Touchpoints
            </h3>
            <button onClick={() => navigate('/touchpoints')} className="text-sm text-primary-600 hover:underline">View All</button>
          </div>
          <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
            {todayData?.touchpoints?.length === 0 && (
              <p className="p-4 text-sm text-gray-500 text-center">No touchpoints scheduled</p>
            )}
            {todayData?.touchpoints?.map((tp) => (
              <div key={tp.id} className="p-3 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{tp.client_name || tp.lead_name || 'Unknown'}</p>
                  <StatusBadge status={tp.status} />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {tp.interaction_type?.replace(/_/g, ' ')} {tp.scheduled_time && `at ${tp.scheduled_time}`}
                  {tp.location && ` - ${tp.location}`}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Follow-ups Section */}
        <div className="card">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <UserPlus size={18} className="text-primary-600" /> Follow-ups
            </h3>
            <button onClick={() => navigate('/leads')} className="text-sm text-primary-600 hover:underline">View All</button>
          </div>
          <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
            {todayData?.followups?.length === 0 && (
              <p className="p-4 text-sm text-gray-500 text-center">No follow-ups today</p>
            )}
            {todayData?.followups?.map((lead) => (
              <div key={lead.id} className="p-3 hover:bg-gray-50">
                <p className="text-sm font-medium">{lead.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <StatusBadge status={lead.status} />
                  {lead.phone && <span className="text-xs text-gray-500">{lead.phone}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Birthdays Section */}
        <div className="card">
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-semibold flex items-center gap-2">
              <Cake size={18} className="text-primary-600" /> Birthdays
            </h3>
          </div>
          <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
            {todayData?.birthdays?.length === 0 && (
              <p className="p-4 text-sm text-gray-500 text-center">No birthdays today</p>
            )}
            {todayData?.birthdays?.map((client) => (
              <div key={client.id} className="p-3 hover:bg-gray-50 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{client.name}</p>
                  <p className="text-xs text-gray-500">{client.phone}</p>
                </div>
                <Cake size={16} className="text-primary-400" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
