import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Check, Calendar } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EntitySearch from '@/components/shared/EntitySearch'
import { TOUCHPOINT_STATUS, INTERACTION_TYPES } from '@/lib/constants'
import { formatDate, getErrorMessage } from '@/lib/utils'
import type { Touchpoint, TouchpointCreate, TouchpointComplete } from '@/types'
import { toast } from 'sonner'
import { format } from 'date-fns'

export default function TouchpointsPage() {
  const [touchpoints, setTouchpoints] = useState<Touchpoint[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [sortBy, setSortBy] = useState('scheduled_date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showForm, setShowForm] = useState(false)
  const [showCompleteForm, setShowCompleteForm] = useState(false)
  const [editingTp, setEditingTp] = useState<Touchpoint | null>(null)
  const [completingTp, setCompletingTp] = useState<Touchpoint | null>(null)
  const [deletingTp, setDeletingTp] = useState<Touchpoint | null>(null)

  const [form, setForm] = useState<TouchpointCreate>({
    interaction_type: 'meeting_office', scheduled_date: format(new Date(), 'yyyy-MM-dd'),
  })
  const [completeForm, setCompleteForm] = useState<TouchpointComplete>({})
  const [clientName, setClientName] = useState<string | null>(null)
  const [leadName, setLeadName] = useState<string | null>(null)

  useEffect(() => { loadData() }, [page, statusFilter, typeFilter, sortBy, sortOrder])

  const loadData = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, limit: 20, sort_by: sortBy, sort_order: sortOrder }
      if (statusFilter) params.status = statusFilter
      if (typeFilter) params.interaction_type = typeFilter
      const { data } = await apiClient.get('/touchpoints', { params })
      setTouchpoints(data.touchpoints)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch { toast.error('Failed to load touchpoints') }
    finally { setLoading(false) }
  }

  const openCreateForm = () => {
    setEditingTp(null)
    setForm({ interaction_type: 'meeting_office', scheduled_date: format(new Date(), 'yyyy-MM-dd') })
    setClientName(null); setLeadName(null)
    setShowForm(true)
  }

  const openEditForm = (tp: Touchpoint) => {
    setEditingTp(tp)
    setForm({ client_id: tp.client_id, lead_id: tp.lead_id, interaction_type: tp.interaction_type, scheduled_date: tp.scheduled_date, scheduled_time: tp.scheduled_time, location: tp.location, agenda: tp.agenda })
    setClientName(tp.client_name); setLeadName(tp.lead_name)
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingTp) { await apiClient.put(`/touchpoints/${editingTp.id}`, form); toast.success('Updated') }
      else { await apiClient.post('/touchpoints', form); toast.success('Created') }
      setShowForm(false); loadData()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleComplete = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!completingTp) return
    try {
      await apiClient.post(`/touchpoints/${completingTp.id}/complete`, completeForm)
      toast.success('Touchpoint completed')
      setShowCompleteForm(false); loadData()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingTp) return
    try { await apiClient.delete(`/touchpoints/${deletingTp.id}`); toast.success('Deleted'); setDeletingTp(null); loadData() }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const columns: Column<Touchpoint>[] = [
    { key: 'client_name', label: 'Client/Lead', render: (t) => <span className="font-medium">{t.client_name || t.lead_name || '-'}</span> },
    { key: 'interaction_type', label: 'Type', render: (t) => t.interaction_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) },
    { key: 'scheduled_date', label: 'Date', sortable: true, render: (t) => formatDate(t.scheduled_date) },
    { key: 'scheduled_time', label: 'Time', render: (t) => t.scheduled_time || '-' },
    { key: 'location', label: 'Location', render: (t) => t.location || '-' },
    { key: 'status', label: 'Status', sortable: true, render: (t) => <StatusBadge status={t.status} /> },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Touchpoints</h1>
        <button onClick={openCreateForm} className="btn-primary flex items-center gap-2"><Plus size={18} /> Add Touchpoint</button>
      </div>

      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <EnumSelect options={TOUCHPOINT_STATUS} value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1) }} allowEmpty emptyLabel="All Status" className="w-40" />
          <EnumSelect options={INTERACTION_TYPES} value={typeFilter} onChange={(v) => { setTypeFilter(v); setPage(1) }} allowEmpty emptyLabel="All Types" className="w-48" />
        </div>
      </div>

      <DataTable columns={columns} data={touchpoints} total={total} page={page} limit={20} totalPages={totalPages} onPageChange={setPage}
        onSort={(k, o) => { setSortBy(k); setSortOrder(o) }} sortBy={sortBy} sortOrder={sortOrder} loading={loading} emptyMessage="No touchpoints found"
        actions={(tp) => (
          <div className="flex items-center gap-1">
            {tp.status === 'scheduled' && <button onClick={() => { setCompletingTp(tp); setCompleteForm({}); setShowCompleteForm(true) }} className="p-1 rounded hover:bg-gray-100" title="Complete"><Check size={16} className="text-green-500" /></button>}
            <button onClick={() => openEditForm(tp)} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>
            <button onClick={() => setDeletingTp(tp)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>
          </div>
        )}
      />

      {/* Create/Edit Form */}
      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingTp ? 'Edit Touchpoint' : 'Add Touchpoint'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Client</label><EntitySearch entityType="clients" value={form.client_id || null} selectedName={clientName} onChange={(id, n) => { setForm({ ...form, client_id: id }); setClientName(n) }} /></div>
            <div><label className="block text-sm font-medium mb-1">Lead</label><EntitySearch entityType="leads" value={form.lead_id || null} selectedName={leadName} onChange={(id, n) => { setForm({ ...form, lead_id: id }); setLeadName(n) }} /></div>
            <div><label className="block text-sm font-medium mb-1">Type *</label><EnumSelect options={INTERACTION_TYPES} value={form.interaction_type} onChange={(v) => setForm({ ...form, interaction_type: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Date *</label><input type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} className="input-field" required /></div>
            <div><label className="block text-sm font-medium mb-1">Time</label><input type="time" value={form.scheduled_time || ''} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Location</label><input type="text" value={form.location || ''} onChange={(e) => setForm({ ...form, location: e.target.value || null })} className="input-field" /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Agenda</label><textarea value={form.agenda || ''} onChange={(e) => setForm({ ...form, agenda: e.target.value || null })} className="input-field" rows={3} /></div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingTp ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      {/* Complete Form */}
      <FormModal open={showCompleteForm} onClose={() => setShowCompleteForm(false)} title="Complete Touchpoint" size="lg">
        <form onSubmit={handleComplete} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Duration (minutes)</label><input type="number" value={completeForm.duration_minutes || ''} onChange={(e) => setCompleteForm({ ...completeForm, duration_minutes: e.target.value ? Number(e.target.value) : undefined })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Outcome</label><EnumSelect options={[{ value: 'open', label: 'Open' }, { value: 'won', label: 'Won' }, { value: 'lost', label: 'Lost' }]} value={completeForm.outcome || ''} onChange={(v) => setCompleteForm({ ...completeForm, outcome: v })} allowEmpty emptyLabel="Select..." /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Minutes of Meeting</label><textarea value={completeForm.mom_text || ''} onChange={(e) => setCompleteForm({ ...completeForm, mom_text: e.target.value || null })} className="input-field" rows={4} placeholder="Key discussion points, decisions, action items..." /></div>
          <div><label className="block text-sm font-medium mb-1">Notes</label><textarea value={completeForm.notes || ''} onChange={(e) => setCompleteForm({ ...completeForm, notes: e.target.value || null })} className="input-field" rows={2} /></div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={completeForm.create_follow_up_task || false} onChange={(e) => setCompleteForm({ ...completeForm, create_follow_up_task: e.target.checked })} className="rounded" /> Create follow-up task</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={completeForm.create_business_opportunity || false} onChange={(e) => setCompleteForm({ ...completeForm, create_business_opportunity: e.target.checked })} className="rounded" /> Create business opportunity</label>
          </div>
          {completeForm.create_follow_up_task && (
            <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg">
              <div><label className="block text-sm font-medium mb-1">Task Title</label><input type="text" value={completeForm.follow_up_task_title || ''} onChange={(e) => setCompleteForm({ ...completeForm, follow_up_task_title: e.target.value })} className="input-field" /></div>
              <div><label className="block text-sm font-medium mb-1">Task Date</label><input type="date" value={completeForm.follow_up_task_date || ''} onChange={(e) => setCompleteForm({ ...completeForm, follow_up_task_date: e.target.value })} className="input-field" /></div>
            </div>
          )}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowCompleteForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Complete</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingTp} onClose={() => setDeletingTp(null)} onConfirm={handleDelete} title="Delete Touchpoint" message="Delete this touchpoint?" />
    </div>
  )
}
