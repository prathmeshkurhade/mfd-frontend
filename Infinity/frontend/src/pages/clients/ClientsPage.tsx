import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Edit, Trash2, Eye, ArrowRight } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import { GENDER_OPTIONS, SOURCE_OPTIONS, RISK_PROFILE_OPTIONS, MARITAL_STATUS_OPTIONS, OCCUPATION_OPTIONS, INCOME_GROUP_OPTIONS } from '@/lib/constants'
import { formatDate, formatPhone, formatCurrency, normalizePhone, getErrorMessage } from '@/lib/utils'
import type { Client, ClientCreate, Lead, ConvertLeadRequest } from '@/types'
import { toast } from 'sonner'

export default function ClientsPage() {
  const navigate = useNavigate()
  const [clients, setClients] = useState<Client[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [showForm, setShowForm] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [deletingClient, setDeletingClient] = useState<Client | null>(null)

  const [form, setForm] = useState<ClientCreate>({
    name: '', phone: '', gender: 'male', source: 'natural_market',
  })

  // Convert lead state
  const [showConvertModal, setShowConvertModal] = useState(false)
  const [unconvertedLeads, setUnconvertedLeads] = useState<Lead[]>([])
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [convertForm, setConvertForm] = useState<ConvertLeadRequest>({ lead_id: '', birthdate: '' })
  const [loadingLeads, setLoadingLeads] = useState(false)

  useEffect(() => { loadClients() }, [page, riskFilter, sortBy, sortOrder])

  const loadClients = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, limit: 20, sort_by: sortBy, sort_order: sortOrder }
      if (search) params.search = search
      if (riskFilter) params.risk_profile = riskFilter
      const { data } = await apiClient.get('/clients', { params })
      setClients(data.clients)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch {
      toast.error('Failed to load clients')
    } finally {
      setLoading(false)
    }
  }

  const openCreateForm = () => {
    setEditingClient(null)
    setForm({ name: '', phone: '', gender: 'male', source: 'natural_market' })
    setShowForm(true)
  }

  const openEditForm = (client: Client) => {
    setEditingClient(client)
    setForm({
      name: client.name, phone: client.phone, email: client.email, birthdate: client.birthdate,
      gender: client.gender || 'male', marital_status: client.marital_status, occupation: client.occupation,
      income_group: client.income_group, address: client.address, area: client.area,
      risk_profile: client.risk_profile, source: client.source || 'natural_market',
      referred_by: client.referred_by, term_insurance: client.term_insurance,
      health_insurance: client.health_insurance, aum: client.aum, sip_amount: client.sip_amount, notes: client.notes,
    })
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingClient) {
        const payload = { ...form, phone: normalizePhone(form.phone) }
        await apiClient.put(`/clients/${editingClient.id}`, payload)
        toast.success('Client updated')
      } else {
        const payload = { ...form, phone: normalizePhone(form.phone) }
        await apiClient.post('/clients', payload)
        toast.success('Client created')
      }
      setShowForm(false)
      loadClients()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleDelete = async () => {
    if (!deletingClient) return
    try {
      await apiClient.delete(`/clients/${deletingClient.id}`)
      toast.success('Client deleted')
      setDeletingClient(null)
      loadClients()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const openConvertModal = async () => {
    setShowConvertModal(true)
    setSelectedLead(null)
    setConvertForm({ lead_id: '', birthdate: '' })
    setLoadingLeads(true)
    try {
      // Fetch unconverted leads (status != converted)
      const { data } = await apiClient.get('/leads', { params: { limit: 100, status: 'follow_up' } })
      const allLeads: Lead[] = data.leads || []
      // Also fetch meeting_scheduled leads
      const { data: data2 } = await apiClient.get('/leads', { params: { limit: 100, status: 'meeting_scheduled' } })
      const moreLeads: Lead[] = data2.leads || []
      setUnconvertedLeads([...allLeads, ...moreLeads].filter(l => !l.converted_to_client_id))
    } catch {
      toast.error('Failed to load leads')
    } finally {
      setLoadingLeads(false)
    }
  }

  const selectLeadForConversion = (lead: Lead) => {
    setSelectedLead(lead)
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
    if (!selectedLead) return
    try {
      const payload: ConvertLeadRequest = {
        lead_id: selectedLead.id,
        birthdate: convertForm.birthdate,
        email: convertForm.email || null,
        address: convertForm.address || null,
        risk_profile: convertForm.risk_profile || null,
      }
      await apiClient.post('/clients/convert-from-lead', payload)
      toast.success(`"${selectedLead.name}" converted to client!`)
      setShowConvertModal(false)
      setSelectedLead(null)
      loadClients()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const columns: Column<Client>[] = [
    { key: 'name', label: 'Name', sortable: true, render: (c) => <span className="font-medium">{c.name}</span> },
    { key: 'phone', label: 'Phone', render: (c) => formatPhone(c.phone) },
    { key: 'area', label: 'Area', render: (c) => c.area || '-' },
    { key: 'risk_profile', label: 'Risk Profile', render: (c) => <StatusBadge status={c.risk_profile} /> },
    { key: 'aum', label: 'AUM', sortable: true, render: (c) => formatCurrency(c.aum) },
    { key: 'sip_amount', label: 'SIP', render: (c) => formatCurrency(c.sip_amount) },
    { key: 'created_at', label: 'Since', sortable: true, render: (c) => formatDate(c.created_at) },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Clients</h1>
        <div className="flex items-center gap-2">
          <button onClick={openConvertModal} className="btn-secondary flex items-center gap-2">
            <ArrowRight size={18} /> Convert Lead
          </button>
          <button onClick={openCreateForm} className="btn-primary flex items-center gap-2">
            <Plus size={18} /> Add Client
          </button>
        </div>
      </div>

      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text" placeholder="Search by name, phone, email, area..."
            value={search} onChange={(e) => setSearch(e.target.value)}
            onBlur={() => { setPage(1); loadClients() }}
            onKeyDown={(e) => e.key === 'Enter' && (setPage(1), loadClients())}
            className="input-field flex-1 min-w-[200px]"
          />
          <EnumSelect options={RISK_PROFILE_OPTIONS} value={riskFilter} onChange={(v) => { setRiskFilter(v); setPage(1) }} allowEmpty emptyLabel="All Risk Profiles" className="w-52" />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={clients}
        total={total}
        page={page}
        limit={20}
        totalPages={totalPages}
        onPageChange={setPage}
        onSort={(key, order) => { setSortBy(key); setSortOrder(order) }}
        sortBy={sortBy}
        sortOrder={sortOrder}
        loading={loading}
        onRowClick={(c) => navigate(`/clients/${c.id}`)}
        emptyMessage="No clients found"
        actions={(client) => (
          <div className="flex items-center gap-1">
            <button onClick={() => navigate(`/clients/${client.id}`)} className="p-1 rounded hover:bg-gray-100" title="View">
              <Eye size={16} className="text-gray-500" />
            </button>
            <button onClick={() => openEditForm(client)} className="p-1 rounded hover:bg-gray-100" title="Edit">
              <Edit size={16} className="text-gray-500" />
            </button>
            <button onClick={() => setDeletingClient(client)} className="p-1 rounded hover:bg-gray-100" title="Delete">
              <Trash2 size={16} className="text-red-500" />
            </button>
          </div>
        )}
      />

      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingClient ? 'Edit Client' : 'Add Client'} size="xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
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
              <label className="block text-sm font-medium mb-1">Gender *</label>
              <EnumSelect options={GENDER_OPTIONS} value={form.gender} onChange={(v) => setForm({ ...form, gender: v })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Source *</label>
              <EnumSelect options={SOURCE_OPTIONS} value={form.source} onChange={(v) => setForm({ ...form, source: v })} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Birthdate</label>
              <input type="date" value={form.birthdate || ''} onChange={(e) => setForm({ ...form, birthdate: e.target.value || null })} className="input-field" />
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
              <label className="block text-sm font-medium mb-1">Risk Profile</label>
              <EnumSelect options={RISK_PROFILE_OPTIONS} value={form.risk_profile || ''} onChange={(v) => setForm({ ...form, risk_profile: v || null })} allowEmpty emptyLabel="Select..." />
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
              <label className="block text-sm font-medium mb-1">AUM</label>
              <input type="number" value={form.aum || ''} onChange={(e) => setForm({ ...form, aum: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">SIP Amount</label>
              <input type="number" value={form.sip_amount || ''} onChange={(e) => setForm({ ...form, sip_amount: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Term Insurance</label>
              <input type="number" value={form.term_insurance || ''} onChange={(e) => setForm({ ...form, term_insurance: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Health Insurance</label>
              <input type="number" value={form.health_insurance || ''} onChange={(e) => setForm({ ...form, health_insurance: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Address</label>
              <input type="text" value={form.address || ''} onChange={(e) => setForm({ ...form, address: e.target.value || null })} className="input-field" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Notes</label>
            <textarea value={form.notes || ''} onChange={(e) => setForm({ ...form, notes: e.target.value || null })} className="input-field" rows={2} />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingClient ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingClient} onClose={() => setDeletingClient(null)} onConfirm={handleDelete} title="Delete Client" message={`Are you sure you want to delete "${deletingClient?.name}"?`} />

      {/* Convert Lead to Client Modal */}
      <FormModal open={showConvertModal} onClose={() => { setShowConvertModal(false); setSelectedLead(null) }} title="Convert Lead to Client" size="lg">
        {!selectedLead ? (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Select a lead to convert to client:</p>
            {loadingLeads && <p className="text-sm text-gray-400 text-center py-4">Loading leads...</p>}
            {!loadingLeads && unconvertedLeads.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">No unconverted leads found</p>
            )}
            <div className="max-h-80 overflow-y-auto divide-y divide-gray-100">
              {unconvertedLeads.map((lead) => (
                <button
                  key={lead.id}
                  onClick={() => selectLeadForConversion(lead)}
                  className="w-full text-left p-3 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-sm">{lead.name}</p>
                    <p className="text-xs text-gray-500">{formatPhone(lead.phone)} {lead.area ? `· ${lead.area}` : ''}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={lead.status} />
                    <ArrowRight size={16} className="text-gray-400" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <form onSubmit={handleConvert} className="space-y-4">
            <div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-700">
              Converting <strong>{selectedLead.name}</strong> ({formatPhone(selectedLead.phone)}) — lead details will be carried over.
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
            <div className="flex justify-between pt-4 border-t">
              <button type="button" onClick={() => setSelectedLead(null)} className="text-sm text-gray-500 hover:text-gray-700">← Back to lead list</button>
              <div className="flex gap-3">
                <button type="button" onClick={() => { setShowConvertModal(false); setSelectedLead(null) }} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Convert to Client</button>
              </div>
            </div>
          </form>
        )}
      </FormModal>
    </div>
  )
}
