import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Check, ArrowRight } from 'lucide-react'
import { format, addDays } from 'date-fns'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EntitySearch from '@/components/shared/EntitySearch'
import { TASK_STATUS, TASK_PRIORITY, TASK_MEDIUM } from '@/lib/constants'
import { formatDate, getErrorMessage } from '@/lib/utils'
import type { Task, TaskCreate, TodayTasksResponse } from '@/types'
import { toast } from 'sonner'

export default function TasksPage() {
  const [view, setView] = useState<'all' | 'today'>('today')
  const [tasks, setTasks] = useState<Task[]>([])
  const [todayTasks, setTodayTasks] = useState<TodayTasksResponse | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [sortBy, setSortBy] = useState('due_date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [deletingTask, setDeletingTask] = useState<Task | null>(null)
  const [selectedIds, setSelectedIds] = useState<string[]>([])

  const [form, setForm] = useState<TaskCreate>({
    title: '', due_date: format(new Date(), 'yyyy-MM-dd'), priority: 'medium',
  })
  const [clientName, setClientName] = useState<string | null>(null)
  const [leadName, setLeadName] = useState<string | null>(null)

  useEffect(() => {
    if (view === 'all') loadTasks()
    else loadTodayTasks()
  }, [view, page, statusFilter, priorityFilter, sortBy, sortOrder])

  const loadTasks = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, limit: 20, sort_by: sortBy, sort_order: sortOrder }
      if (statusFilter) params.status = statusFilter
      if (priorityFilter) params.priority = priorityFilter
      const { data } = await apiClient.get('/tasks', { params })
      setTasks(data.tasks)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch { toast.error('Failed to load tasks') }
    finally { setLoading(false) }
  }

  const loadTodayTasks = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/tasks/today')
      setTodayTasks(data)
    } catch { toast.error('Failed to load today tasks') }
    finally { setLoading(false) }
  }

  const reload = () => view === 'all' ? loadTasks() : loadTodayTasks()

  const handleComplete = async (taskId: string) => {
    try {
      await apiClient.post(`/tasks/${taskId}/complete`)
      toast.success('Task completed')
      reload()
    } catch { toast.error('Failed to complete task') }
  }

  const handleCarryForward = async (taskId: string) => {
    const tomorrow = format(addDays(new Date(), 1), 'yyyy-MM-dd')
    try {
      await apiClient.post(`/tasks/${taskId}/carry-forward`, null, { params: { new_date: tomorrow } })
      toast.success('Carried forward')
      reload()
    } catch { toast.error('Failed to carry forward') }
  }

  const handleBulkComplete = async () => {
    if (!selectedIds.length) return
    try {
      await apiClient.post('/tasks/bulk-complete', { task_ids: selectedIds })
      toast.success(`${selectedIds.length} tasks completed`)
      setSelectedIds([])
      reload()
    } catch { toast.error('Failed to bulk complete') }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingTask) {
        await apiClient.put(`/tasks/${editingTask.id}`, form)
        toast.success('Task updated')
      } else {
        await apiClient.post('/tasks', form)
        toast.success('Task created')
      }
      setShowForm(false)
      reload()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingTask) return
    try {
      await apiClient.delete(`/tasks/${deletingTask.id}`)
      toast.success('Task deleted')
      setDeletingTask(null)
      reload()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const openCreateForm = () => {
    setEditingTask(null)
    setForm({ title: '', due_date: format(new Date(), 'yyyy-MM-dd'), priority: 'medium' })
    setClientName(null)
    setLeadName(null)
    setShowForm(true)
  }

  const openEditForm = (task: Task) => {
    setEditingTask(task)
    setForm({ title: task.title || '', description: task.description, client_id: task.client_id, lead_id: task.lead_id, priority: task.priority, medium: task.medium, due_date: task.due_date, due_time: task.due_time, all_day: task.all_day, product_type: task.product_type, is_business_opportunity: task.is_business_opportunity })
    setClientName(task.client_name)
    setLeadName(task.lead_name)
    setShowForm(true)
  }

  const renderTaskCard = (task: Task) => (
    <div key={task.id} className="p-3 flex items-center justify-between hover:bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {task.status === 'pending' && (
          <input type="checkbox" checked={selectedIds.includes(task.id)} onChange={(e) => {
            setSelectedIds(e.target.checked ? [...selectedIds, task.id] : selectedIds.filter((i) => i !== task.id))
          }} className="rounded" />
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{task.title}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <StatusBadge status={task.priority} />
            {(task.client_name || task.lead_name) && <span className="text-xs text-gray-500">{task.client_name || task.lead_name}</span>}
            {task.due_time && <span className="text-xs text-gray-400">{task.due_time}</span>}
            {task.carry_forward_count > 0 && <span className="text-xs text-orange-500">CF x{task.carry_forward_count}</span>}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-1 ml-2">
        {task.status === 'pending' && (
          <>
            <button onClick={() => handleComplete(task.id)} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200">Done</button>
            <button onClick={() => handleCarryForward(task.id)} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded hover:bg-orange-200">CF</button>
          </>
        )}
        <button onClick={() => openEditForm(task)} className="p-1 rounded hover:bg-gray-100"><Edit size={14} className="text-gray-400" /></button>
        <button onClick={() => setDeletingTask(task)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={14} className="text-red-400" /></button>
      </div>
    </div>
  )

  const columns: Column<Task>[] = [
    { key: 'title', label: 'Title', sortable: true, render: (t) => <span className="font-medium">{t.title || '-'}</span> },
    { key: 'client_name', label: 'Client/Lead', render: (t) => t.client_name || t.lead_name || '-' },
    { key: 'priority', label: 'Priority', sortable: true, render: (t) => <StatusBadge status={t.priority} /> },
    { key: 'status', label: 'Status', sortable: true, render: (t) => <StatusBadge status={t.status} /> },
    { key: 'due_date', label: 'Due Date', sortable: true, render: (t) => formatDate(t.due_date) },
    { key: 'medium', label: 'Medium', render: (t) => t.medium?.replace(/_/g, ' ') || '-' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Tasks</h1>
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button onClick={() => setView('today')} className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === 'today' ? 'bg-white shadow font-medium' : 'text-gray-600'}`}>Today</button>
            <button onClick={() => setView('all')} className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === 'all' ? 'bg-white shadow font-medium' : 'text-gray-600'}`}>All Tasks</button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.length > 0 && (
            <button onClick={handleBulkComplete} className="btn-primary text-sm">Complete {selectedIds.length} Selected</button>
          )}
          <button onClick={openCreateForm} className="btn-primary flex items-center gap-2"><Plus size={18} /> Add Task</button>
        </div>
      </div>

      {view === 'today' ? (
        <div className="space-y-4">
          {loading ? (
            <div className="card p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
          ) : (
            <>
              {/* Overdue */}
              {todayTasks && todayTasks.overdue.length > 0 && (
                <div className="card">
                  <div className="p-3 border-b border-gray-200 bg-red-50"><h3 className="text-sm font-semibold text-red-700">Overdue ({todayTasks.overdue_count})</h3></div>
                  <div className="divide-y divide-gray-100">{todayTasks.overdue.map(renderTaskCard)}</div>
                </div>
              )}
              {/* Pending */}
              <div className="card">
                <div className="p-3 border-b border-gray-200 bg-yellow-50"><h3 className="text-sm font-semibold text-yellow-700">Pending ({todayTasks?.pending_count || 0})</h3></div>
                <div className="divide-y divide-gray-100">
                  {todayTasks?.pending.length === 0 && <p className="p-4 text-center text-sm text-gray-500">No pending tasks</p>}
                  {todayTasks?.pending.map(renderTaskCard)}
                </div>
              </div>
              {/* Completed */}
              <div className="card">
                <div className="p-3 border-b border-gray-200 bg-green-50"><h3 className="text-sm font-semibold text-green-700">Completed ({todayTasks?.completed_count || 0})</h3></div>
                <div className="divide-y divide-gray-100">
                  {todayTasks?.completed.length === 0 && <p className="p-4 text-center text-sm text-gray-500">No completed tasks</p>}
                  {todayTasks?.completed.map(renderTaskCard)}
                </div>
              </div>
            </>
          )}
        </div>
      ) : (
        <>
          <div className="card p-4">
            <div className="flex flex-wrap items-center gap-3">
              <EnumSelect options={TASK_STATUS} value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1) }} allowEmpty emptyLabel="All Status" className="w-40" />
              <EnumSelect options={TASK_PRIORITY} value={priorityFilter} onChange={(v) => { setPriorityFilter(v); setPage(1) }} allowEmpty emptyLabel="All Priority" className="w-40" />
            </div>
          </div>
          <DataTable columns={columns} data={tasks} total={total} page={page} limit={20} totalPages={totalPages} onPageChange={setPage} onSort={(k, o) => { setSortBy(k); setSortOrder(o) }} sortBy={sortBy} sortOrder={sortOrder} loading={loading} emptyMessage="No tasks found"
            actions={(task) => (
              <div className="flex items-center gap-1">
                {task.status === 'pending' && <button onClick={() => handleComplete(task.id)} className="p-1 rounded hover:bg-gray-100"><Check size={16} className="text-green-500" /></button>}
                <button onClick={() => openEditForm(task)} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>
                <button onClick={() => setDeletingTask(task)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>
              </div>
            )}
          />
        </>
      )}

      {/* Form Modal */}
      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingTask ? 'Edit Task' : 'Add Task'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Title *</label>
              <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Client</label>
              <EntitySearch entityType="clients" value={form.client_id || null} selectedName={clientName} onChange={(id, name) => { setForm({ ...form, client_id: id }); setClientName(name) }} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Lead</label>
              <EntitySearch entityType="leads" value={form.lead_id || null} selectedName={leadName} onChange={(id, name) => { setForm({ ...form, lead_id: id }); setLeadName(name) }} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Priority</label>
              <EnumSelect options={TASK_PRIORITY} value={form.priority || 'medium'} onChange={(v) => setForm({ ...form, priority: v })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Medium</label>
              <EnumSelect options={TASK_MEDIUM} value={form.medium || ''} onChange={(v) => setForm({ ...form, medium: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Due Date *</label>
              <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Due Time</label>
              <input type="time" value={form.due_time || ''} onChange={(e) => setForm({ ...form, due_time: e.target.value || null })} className="input-field" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value || null })} className="input-field" rows={3} />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingTask ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingTask} onClose={() => setDeletingTask(null)} onConfirm={handleDelete} title="Delete Task" message={`Delete "${deletingTask?.title}"?`} />
    </div>
  )
}
