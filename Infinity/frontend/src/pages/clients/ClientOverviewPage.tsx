import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, User, Target, Calendar, Briefcase, CheckSquare, Package } from 'lucide-react'
import apiClient from '@/lib/api-client'
import { formatDate, formatCurrency, formatPhone, enumToLabel } from '@/lib/utils'
import StatusBadge from '@/components/shared/StatusBadge'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import type { ClientOverview } from '@/types'
import { toast } from 'sonner'

export default function ClientOverviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [overview, setOverview] = useState<ClientOverview | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) loadOverview()
  }, [id])

  const loadOverview = async () => {
    try {
      const { data } = await apiClient.get(`/clients/${id}/overview`)
      setOverview(data)
    } catch {
      toast.error('Failed to load client')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner />
  if (!overview) return <p className="text-center text-gray-500 py-12">Client not found</p>

  const { client } = overview
  const tabs = [
    { key: 'overview', label: 'Overview', icon: User },
    { key: 'goals', label: 'Goals', icon: Target },
    { key: 'touchpoints', label: 'Touchpoints', icon: Calendar },
    { key: 'opportunities', label: 'Opportunities', icon: Briefcase },
    { key: 'tasks', label: 'Tasks', icon: CheckSquare },
  ]

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/clients')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} /> Back to Clients
      </button>

      {/* Client Header */}
      <div className="card p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
              <span className="text-2xl font-bold text-primary-700">
                {client.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h1 className="text-2xl font-bold">{client.name}</h1>
              <p className="text-gray-500">{formatPhone(client.phone)} {client.email && `| ${client.email}`}</p>
              <div className="flex items-center gap-2 mt-1">
                {client.risk_profile && <StatusBadge status={client.risk_profile} />}
                {client.area && <span className="text-sm text-gray-500">{client.area}</span>}
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">AUM</p>
            <p className="text-xl font-bold text-primary-700">{formatCurrency(client.aum)}</p>
            <p className="text-sm text-gray-500 mt-1">SIP: {formatCurrency(client.sip_amount)}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-1">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon size={16} /> {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card p-4">
            <h3 className="font-semibold mb-3">Personal Details</h3>
            <dl className="space-y-2 text-sm">
              {[
                ['Gender', enumToLabel(client.gender)],
                ['Marital Status', enumToLabel(client.marital_status)],
                ['Occupation', enumToLabel(client.occupation)],
                ['Income Group', enumToLabel(client.income_group)],
                ['Age', client.age ? `${client.age} years` : '-'],
                ['Birthdate', formatDate(client.birthdate)],
                ['Address', client.address || '-'],
                ['Source', enumToLabel(client.source)],
                ['Referred By', client.referred_by || '-'],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between">
                  <dt className="text-gray-500">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="card p-4">
            <h3 className="font-semibold mb-3">Financial Summary</h3>
            <dl className="space-y-2 text-sm">
              {[
                ['Total AUM', formatCurrency(client.aum)],
                ['SIP Amount', formatCurrency(client.sip_amount)],
                ['Term Insurance', formatCurrency(client.term_insurance)],
                ['Health Insurance', formatCurrency(client.health_insurance)],
                ['Client Since', formatDate(client.created_at)],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between">
                  <dt className="text-gray-500">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
          {client.notes && (
            <div className="card p-4 col-span-full">
              <h3 className="font-semibold mb-2">Notes</h3>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{client.notes}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'goals' && (
        <div className="card">
          <div className="divide-y divide-gray-100">
            {overview.goals.length === 0 && <p className="p-6 text-center text-gray-500">No goals</p>}
            {overview.goals.map((goal) => (
              <div key={goal.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{goal.goal_name}</p>
                    <p className="text-sm text-gray-500">{enumToLabel(goal.goal_type)} | Target: {formatCurrency(goal.target_amount)}</p>
                  </div>
                  <div className="text-right">
                    <StatusBadge status={goal.status} />
                    <p className="text-sm text-gray-500 mt-1">{goal.progress_percent}% complete</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'touchpoints' && (
        <div className="card">
          <div className="divide-y divide-gray-100">
            {overview.recent_touchpoints.length === 0 && <p className="p-6 text-center text-gray-500">No touchpoints</p>}
            {overview.recent_touchpoints.map((tp) => (
              <div key={tp.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{enumToLabel(tp.interaction_type)}</p>
                    <p className="text-sm text-gray-500">{formatDate(tp.scheduled_date)} {tp.scheduled_time && `at ${tp.scheduled_time}`}</p>
                  </div>
                  <StatusBadge status={tp.status} />
                </div>
                {tp.agenda && <p className="text-sm text-gray-500 mt-1">{tp.agenda}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'opportunities' && (
        <div className="card">
          <div className="divide-y divide-gray-100">
            {overview.open_opportunities.length === 0 && <p className="p-6 text-center text-gray-500">No opportunities</p>}
            {overview.open_opportunities.map((bo) => (
              <div key={bo.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{enumToLabel(bo.opportunity_type)}</p>
                    <p className="text-sm text-gray-500">{formatCurrency(bo.expected_amount)} | {enumToLabel(bo.opportunity_stage)}</p>
                  </div>
                  <StatusBadge status={bo.outcome || bo.opportunity_stage} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="card">
          <div className="divide-y divide-gray-100">
            {overview.pending_tasks.length === 0 && <p className="p-6 text-center text-gray-500">No pending tasks</p>}
            {overview.pending_tasks.map((task) => (
              <div key={task.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{task.title}</p>
                    <p className="text-sm text-gray-500">Due: {formatDate(task.due_date)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={task.priority} />
                    <StatusBadge status={task.status} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
