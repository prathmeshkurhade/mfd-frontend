import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, ArrowRight } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import { LEAD_STATUS, SOURCE_OPTIONS, GENDER_OPTIONS, MARITAL_STATUS_OPTIONS, OCCUPATION_OPTIONS, INCOME_GROUP_OPTIONS, AGE_GROUP_OPTIONS, RISK_PROFILE_OPTIONS } from '@/lib/constants'
import { formatDate, formatPhone, normalizePhone, getErrorMessage } from '@/lib/utils'
import type { Lead, LeadCreate, ConvertLeadRequest } from '@/types'
import { toast } from 'sonner'

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showForm, setShowForm] = useState(false)
  const [editingLead, setEditingLead] = useState<Lead | null>(null)
  const [deletingLead, setDeletingLead] = useState<Lead | null>(null)
  const [convertingLead, setConvertingLead] = useState<Lead | null>(null)
  const [convertForm, setConvertForm] = useState<ConvertLeadRequest>({ lead_id: '', birthdate: '' })

  // Form state
  const [form, setForm] = useState<LeadCreate>({
    name: '', phone: '', source: 'natural_market', status: 'follow_up',
  })

  useEffect(() => { loadLeads() }, [page, statusFilter, sourceFilter, sortBy, sortOrder])

  const loadLeads = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, limit: 20, sort_by: sortBy, sort_order: sortOrder }
      if (search) params.search = search
      if (statusFilter) params.status = statusFilter
      if (sourceFilter) params.source = sourceFilter
      const { data } = await apiClient.get('/leads', { params })
      setLeads(data.leads)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch (err) {
      toast.error('Failed to load leads')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadLeads()
  }

  const openCreateForm = () => {
    setEditingLead(null)
    setForm({ name: '', phone: '', source: 'natural_market', status: 'follow_up' })
    setShowForm(true)
  }

  const openEditForm = (lead: Lead) => {
    setEditingLead(lead)
    setForm({
      name: lead.name || '',
      phone: lead.phone || '',
      email: lead.email,
      gender: lead.gender,
      marital_status: lead.marital_status,
      occupation: lead.occupation,
      income_group: lead.income_group,
      age_group: lead.age_group,
      area: lead.area,
      source: lead.source || 'natural_market',
      referred_by: lead.referred_by,
      dependants: lead.dependants,
      source_description: lead.source_description,
      status: lead.status,
      scheduled_date: lead.scheduled_date,
      scheduled_time: lead.scheduled_time,
      notes: lead.notes,
    })
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = { ...form, phone: normalizePhone(form.phone) }
      if (editingLead) {
        await apiClient.put(`/leads/${editingLead.id}`, payload)
        toast.success('Lead updated')
      } else {
        await apiClient.post('/leads', payload)
        toast.success('Lead created')
      }
      setShowForm(false)
      loadLeads()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleDelete = async () => {
    if (!deletingLead) return
    try {
      await apiClient.delete(`/leads/${deletingLead.id}`)
      toast.success('Lead deleted')
      setDeletingLead(null)
      loadLeads()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleStatusChange = async (leadId: string, status: string) => {
    try {
      await apiClient.patch(`/leads/${leadId}/status`, { status })
      toast.success('Status updated')
      loadLeads()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const openConvertForm = (lead: Lead) => {
    setConvertingLead(lead)
    setConvertForm({
      lead_id: lead.id,
      birthdate: '',
      email: lead.email || '',
      address: '',
      risk_profile: '',
    })
  }

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!convertingLead) return
    try {
      const payload: ConvertLeadRequest = {
        lead_id: convertingLead.id,
        birthdate: convertForm.birthdate,
        email: convertForm.email || null,
        address: convertForm.address || null,
        risk_profile: convertForm.risk_profile || null,
      }
      await apiClient.post('/clients/convert-from-lead', payload)
      toast.success(`"${convertingLead.name}" converted to client!`)
      setConvertingLead(null)
      loadLeads()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const columns: Column<Lead>[] = [
    { key: 'name', label: 'Name', sortable: true, render: (l) => <span className="font-medium">{l.name || '-'}</span> },
    { key: 'phone', label: 'Phone', render: (l) => formatPhone(l.phone) },
    { key: 'source', label: 'Source', render: (l) => <span className="capitalize">{l.source?.replace(/_/g, ' ') || '-'}</span> },
    { key: 'status', label: 'Status', sortable: true, render: (l) => <StatusBadge status={l.status} /> },
    { key: 'scheduled_date', label: 'Follow-up', sortable: true, render: (l) => formatDate(l.scheduled_date) },
    { key: 'area', label: 'Area', render: (l) => l.area || '-' },
    { key: 'created_at', label: 'Created', sortable: true, render: (l) => formatDate(l.created_at) },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Leads</h1>
        <button onClick={openCreateForm} className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Lead
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <form onSubmit={handleSearch} className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search by name, phone, email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field"
              onBlur={() => { setPage(1); loadLeads() }}
            />
          </form>
          <EnumSelect options={LEAD_STATUS} value={statusFilter} onChange={(v) => { setStatusFilter(v); setPage(1) }} allowEmpty emptyLabel="All Status" className="w-40" />
          <EnumSelect options={SOURCE_OPTIONS} value={sourceFilter} onChange={(v) => { setSourceFilter(v); setPage(1) }} allowEmpty emptyLabel="All Sources" className="w-40" />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={leads}
        total={total}
        page={page}
        limit={20}
        totalPages={totalPages}
        onPageChange={setPage}
        onSort={(key, order) => { setSortBy(key); setSortOrder(order) }}
        sortBy={sortBy}
        sortOrder={sortOrder}
        loading={loading}
        emptyMessage="No leads found"
        actions={(lead) => (
          <div className="flex items-center gap-1">
            {lead.status !== 'converted' && !lead.converted_to_client_id && (
              <button onClick={() => openConvertForm(lead)} className="p-1 rounded hover:bg-gray-100" title="Convert to Client">
                <ArrowRight size={16} className="text-green-600" />
              </button>
            )}
            <button onClick={() => openEditForm(lead)} className="p-1 rounded hover:bg-gray-100" title="Edit">
              <Edit size={16} className="text-gray-500" />
            </button>
            <button onClick={() => setDeletingLead(lead)} className="p-1 rounded hover:bg-gray-100" title="Delete">
              <Trash2 size={16} className="text-red-500" />
            </button>
          </div>
        )}
      />

      {/* Create/Edit Modal */}
      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingLead ? 'Edit Lead' : 'Add Lead'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone *</label>
              <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input-field" placeholder="+91XXXXXXXXXX" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input type="email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value || null })} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Source *</label>
              <EnumSelect options={SOURCE_OPTIONS} value={form.source} onChange={(v) => setForm({ ...form, source: v })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <EnumSelect options={LEAD_STATUS} value={form.status || 'follow_up'} onChange={(v) => setForm({ ...form, status: v })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Gender</label>
              <EnumSelect options={GENDER_OPTIONS} value={form.gender || ''} onChange={(v) => setForm({ ...form, gender: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Marital Status</label>
              <EnumSelect options={MARITAL_STATUS_OPTIONS} value={form.marital_status || ''} onChange={(v) => setForm({ ...form, marital_status: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Occupation</label>
              <EnumSelect options={OCCUPATION_OPTIONS} value={form.occupation || ''} onChange={(v) => setForm({ ...form, occupation: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Income Group</label>
              <EnumSelect options={INCOME_GROUP_OPTIONS} value={form.income_group || ''} onChange={(v) => setForm({ ...form, income_group: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Age Group</label>
              <EnumSelect options={AGE_GROUP_OPTIONS} value={form.age_group || ''} onChange={(v) => setForm({ ...form, age_group: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Area</label>
              <input type="text" value={form.area || ''} onChange={(e) => setForm({ ...form, area: e.target.value || null })} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Referred By</label>
              <input type="text" value={form.referred_by || ''} onChange={(e) => setForm({ ...form, referred_by: e.target.value || null })} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Follow-up Date</label>
              <input type="date" value={form.scheduled_date || ''} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value || null })} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Follow-up Time</label>
              <input type="time" value={form.scheduled_time || ''} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value || null })} className="input-field" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Notes</label>
            <textarea value={form.notes || ''} onChange={(e) => setForm({ ...form, notes: e.target.value || null })} className="input-field" rows={3} />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingLead ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog
        open={!!deletingLead}
        onClose={() => setDeletingLead(null)}
        onConfirm={handleDelete}
        title="Delete Lead"
        message={`Are you sure you want to delete "${deletingLead?.name}"? This cannot be undone.`}
      />

      {/* Convert Lead to Client Modal */}
      <FormModal open={!!convertingLead} onClose={() => setConvertingLead(null)} title={`Convert "${convertingLead?.name}" to Client`} size="md">
        <form onSubmit={handleConvert} className="space-y-4">
          <div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-700">
            Lead details (name, phone, gender, source, etc.) will be carried over to the new client record.
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Birthdate *</label>
              <input type="date" value={convertForm.birthdate} onChange={(e) => setConvertForm({ ...convertForm, birthdate: e.target.value })} className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input type="email" value={convertForm.email || ''} onChange={(e) => setConvertForm({ ...convertForm, email: e.target.value || null })} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Address</label>
              <input type="text" value={convertForm.address || ''} onChange={(e) => setConvertForm({ ...convertForm, address: e.target.value || null })} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Risk Profile</label>
              <EnumSelect options={RISK_PROFILE_OPTIONS} value={convertForm.risk_profile || ''} onChange={(v) => setConvertForm({ ...convertForm, risk_profile: v || null })} allowEmpty emptyLabel="Select..." />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setConvertingLead(null)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Convert to Client</button>
          </div>
        </form>
      </FormModal>
    </div>
  )
}
