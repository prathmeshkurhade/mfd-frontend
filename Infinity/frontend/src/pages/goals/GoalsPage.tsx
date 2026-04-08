import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EntitySearch from '@/components/shared/EntitySearch'
import { GOAL_TYPES, GOAL_STATUS } from '@/lib/constants'
import { formatDate, formatCurrency, formatPercent, getErrorMessage, enumToLabel } from '@/lib/utils'
import type { Goal, GoalCreate, GoalWithSubgoals } from '@/types'
import { toast } from 'sonner'

export default function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showForm, setShowForm] = useState(false)
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null)
  const [deletingGoal, setDeletingGoal] = useState<Goal | null>(null)
  const [expandedGoal, setExpandedGoal] = useState<GoalWithSubgoals | null>(null)

  const [form, setForm] = useState<GoalCreate>({
    client_id: '', goal_type: 'wealth_creation', goal_name: '', target_amount: 0,
  })
  const [clientName, setClientName] = useState<string | null>(null)

  useEffect(() => { loadGoals() }, [page, typeFilter, statusFilter, sortBy, sortOrder])

  const loadGoals = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, limit: 20, sort_by: sortBy, sort_order: sortOrder }
      if (typeFilter) params.goal_type = typeFilter
      if (statusFilter) params.status = statusFilter
      const { data } = await apiClient.get('/goals', { params })
      setGoals(data.goals)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch { toast.error('Failed to load goals') }
    finally { setLoading(false) }
  }

  const handleToggleSubgoals = async (goal: Goal) => {
    if (expandedGoal?.parent_goal.id === goal.id) { setExpandedGoal(null); return }
    try {
      const { data } = await apiClient.get(`/goals/${goal.id}/with-subgoals`)
      setExpandedGoal(data)
    } catch { toast.error('Failed to load sub-goals') }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingGoal) { await apiClient.put(`/goals/${editingGoal.id}`, form); toast.success('Updated') }
      else { await apiClient.post('/goals', form); toast.success('Created') }
      setShowForm(false); loadGoals()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingGoal) return
    try { await apiClient.delete(`/goals/${deletingGoal.id}`); toast.success('Deleted'); setDeletingGoal(null); loadGoals() }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const openCreateForm = () => {
    setEditingGoal(null)
    setForm({ client_id: '', goal_type: 'wealth_creation', goal_name: '', target_amount: 0 })
    setClientName(null)
    setShowForm(true)
  }

  const columns: Column<Goal>[] = [
    { key: 'goal_name', label: 'Goal', sortable: true, render: (g) => (
      <div className="flex items-center gap-2">
        <button onClick={(e) => { e.stopPropagation(); handleToggleSubgoals(g) }} className="p-0.5 rounded hover:bg-gray-100">
          {expandedGoal?.parent_goal.id === g.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        <span className="font-medium">{g.goal_name}</span>
      </div>
    )},
    { key: 'client_name', label: 'Client', render: (g) => g.client_name || '-' },
    { key: 'goal_type', label: 'Type', render: (g) => enumToLabel(g.goal_type) },
    { key: 'target_amount', label: 'Target', sortable: true, render: (g) => formatCurrency(g.target_amount) },
    { key: 'monthly_sip', label: 'Monthly SIP', render: (g) => formatCurrency(g.monthly_sip) },
    { key: 'progress_percent', label: 'Progress', render: (g) => (
      <div className="flex items-center gap-2">
        <div className="w-20 bg-gray-200 rounded-full h-2">
          <div className="bg-primary-600 h-2 rounded-full" style={{ width: `${Math.min(g.progress_percent, 100)}%` }} />
        </div>
        <span className="text-xs">{formatPercent(g.progress_percent)}</span>
      </div>
    )},
    { key: 'status', label: 'Status', render: (g) => <StatusBadge status={g.status} /> },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Goals</h1>
        <button onClick={openCreateForm} className="btn-primary flex items-center gap-2"><Plus size={18} /> Add Goal</button>
      </div>

      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <EnumSelect options={GOAL_TYPES} value={typeFilter} onChange={(v) => { setTypeFilter(v); setPage(1) }} allowEmpty emptyLabel="All Types" className="w-48" />
          <EnumSelect options={GOAL_STATUS} value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1) }} allowEmpty emptyLabel="All Status" className="w-40" />
        </div>
      </div>

      <DataTable columns={columns} data={goals} total={total} page={page} limit={20} totalPages={totalPages} onPageChange={setPage}
        onSort={(k, o) => { setSortBy(k); setSortOrder(o) }} sortBy={sortBy} sortOrder={sortOrder} loading={loading} emptyMessage="No goals found"
        actions={(goal) => (
          <div className="flex items-center gap-1">
            <button onClick={() => { setEditingGoal(goal); setForm({ client_id: goal.client_id, goal_type: goal.goal_type, goal_name: goal.goal_name, target_amount: goal.target_amount, target_date: goal.target_date, current_investment: goal.current_investment, monthly_sip: goal.monthly_sip, lumpsum_investment: goal.lumpsum_investment, expected_return_rate: goal.expected_return_rate }); setClientName(goal.client_name); setShowForm(true) }} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>
            <button onClick={() => setDeletingGoal(goal)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>
          </div>
        )}
      />

      {/* Subgoals display */}
      {expandedGoal && expandedGoal.sub_goals.length > 0 && (
        <div className="card p-4 ml-8 border-l-4 border-primary-400">
          <h4 className="text-sm font-semibold mb-2">Sub-goals of "{expandedGoal.parent_goal.goal_name}"</h4>
          <p className="text-xs text-gray-500 mb-3">Total Target: {formatCurrency(expandedGoal.total_target)} | Total SIP: {formatCurrency(expandedGoal.total_monthly_sip)}</p>
          <div className="divide-y divide-gray-100">
            {expandedGoal.sub_goals.map((sg) => (
              <div key={sg.id} className="py-2 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{sg.goal_name}</p>
                  <p className="text-xs text-gray-500">{enumToLabel(sg.goal_type)} | {formatCurrency(sg.target_amount)}</p>
                </div>
                <StatusBadge status={sg.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingGoal ? 'Edit Goal' : 'Add Goal'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Client *</label><EntitySearch entityType="clients" value={form.client_id || null} selectedName={clientName} onChange={(id, n) => { setForm({ ...form, client_id: id || '' }); setClientName(n) }} /></div>
            <div><label className="block text-sm font-medium mb-1">Goal Type *</label><EnumSelect options={GOAL_TYPES} value={form.goal_type} onChange={(v) => setForm({ ...form, goal_type: v })} /></div>
            <div className="col-span-2"><label className="block text-sm font-medium mb-1">Goal Name *</label><input type="text" value={form.goal_name} onChange={(e) => setForm({ ...form, goal_name: e.target.value })} className="input-field" required /></div>
            <div><label className="block text-sm font-medium mb-1">Target Amount *</label><input type="number" value={form.target_amount} onChange={(e) => setForm({ ...form, target_amount: Number(e.target.value) })} className="input-field" min={0} required /></div>
            <div><label className="block text-sm font-medium mb-1">Target Date</label><input type="date" value={form.target_date || ''} onChange={(e) => setForm({ ...form, target_date: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Monthly SIP</label><input type="number" value={form.monthly_sip || ''} onChange={(e) => setForm({ ...form, monthly_sip: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">Lumpsum Investment</label><input type="number" value={form.lumpsum_investment || ''} onChange={(e) => setForm({ ...form, lumpsum_investment: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">Current Investment</label><input type="number" value={form.current_investment || ''} onChange={(e) => setForm({ ...form, current_investment: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">Expected Return %</label><input type="number" value={form.expected_return_rate || ''} onChange={(e) => setForm({ ...form, expected_return_rate: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} max={50} step={0.5} /></div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingGoal ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingGoal} onClose={() => setDeletingGoal(null)} onConfirm={handleDelete} title="Delete Goal" message={`Delete "${deletingGoal?.goal_name}" and all sub-goals?`} />
    </div>
  )
}
