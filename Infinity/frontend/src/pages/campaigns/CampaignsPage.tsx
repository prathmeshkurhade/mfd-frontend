import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Play, Eye } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EnumSelect from '@/components/shared/EnumSelect'
import { CHANNEL_OPTIONS } from '@/lib/constants'
import { formatDate, getErrorMessage } from '@/lib/utils'
import type { Campaign, CampaignCreate } from '@/types'
import { toast } from 'sonner'

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null)
  const [deletingCampaign, setDeletingCampaign] = useState<Campaign | null>(null)
  const [executingId, setExecutingId] = useState<string | null>(null)
  const [form, setForm] = useState<CampaignCreate>({ name: '' })

  useEffect(() => { loadCampaigns() }, [page])

  const loadCampaigns = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/campaigns', { params: { page, limit: 20 } })
      setCampaigns(data.campaigns)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch { toast.error('Failed to load campaigns') }
    finally { setLoading(false) }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingCampaign) { await apiClient.put(`/campaigns/${editingCampaign.id}`, form); toast.success('Updated') }
      else { await apiClient.post('/campaigns', form); toast.success('Created') }
      setShowForm(false); loadCampaigns()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleExecute = async (id: string) => {
    setExecutingId(id)
    try {
      const { data } = await apiClient.post(`/campaigns/${id}/execute`)
      toast.success(`Sent to ${data.successful} recipients`)
      loadCampaigns()
    } catch (err) { toast.error(getErrorMessage(err)) }
    finally { setExecutingId(null) }
  }

  const handleDelete = async () => {
    if (!deletingCampaign) return
    try { await apiClient.delete(`/campaigns/${deletingCampaign.id}`); toast.success('Deleted'); setDeletingCampaign(null); loadCampaigns() }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const columns: Column<Campaign>[] = [
    { key: 'name', label: 'Name', render: (c) => <span className="font-medium">{c.name}</span> },
    { key: 'channel', label: 'Channel', render: (c) => c.channel || '-' },
    { key: 'is_executed', label: 'Status', render: (c) => (
      <span className={`text-xs px-2 py-1 rounded-full ${c.is_executed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
        {c.is_executed ? 'Executed' : 'Draft'}
      </span>
    )},
    { key: 'total_recipients', label: 'Recipients', render: (c) => c.total_recipients },
    { key: 'successful_sends', label: 'Success/Fail', render: (c) => c.is_executed ? `${c.successful_sends}/${c.failed_sends}` : '-' },
    { key: 'created_at', label: 'Created', render: (c) => formatDate(c.created_at) },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Campaigns</h1>
        <button onClick={() => { setEditingCampaign(null); setForm({ name: '' }); setShowForm(true) }} className="btn-primary flex items-center gap-2"><Plus size={18} /> New Campaign</button>
      </div>

      <DataTable columns={columns} data={campaigns} total={total} page={page} limit={20} totalPages={totalPages} onPageChange={setPage} loading={loading} emptyMessage="No campaigns"
        actions={(c) => (
          <div className="flex items-center gap-1">
            {!c.is_executed && <button onClick={() => handleExecute(c.id)} disabled={executingId === c.id} className="p-1 rounded hover:bg-gray-100" title="Execute"><Play size={16} className="text-green-500" /></button>}
            {!c.is_executed && <button onClick={() => { setEditingCampaign(c); setForm({ name: c.name, description: c.description, campaign_type: c.campaign_type, message_template: c.message_template, channel: c.channel, scheduled_date: c.scheduled_date }); setShowForm(true) }} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>}
            {!c.is_executed && <button onClick={() => setDeletingCampaign(c)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>}
          </div>
        )}
      />

      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingCampaign ? 'Edit Campaign' : 'New Campaign'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2"><label className="block text-sm font-medium mb-1">Name *</label><input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" required /></div>
            <div><label className="block text-sm font-medium mb-1">Channel</label><EnumSelect options={CHANNEL_OPTIONS} value={form.channel || ''} onChange={(v) => setForm({ ...form, channel: v || null })} allowEmpty emptyLabel="Select..." /></div>
            <div><label className="block text-sm font-medium mb-1">Scheduled Date</label><input type="date" value={form.scheduled_date || ''} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value || null })} className="input-field" /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Description</label><textarea value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value || null })} className="input-field" rows={2} /></div>
          <div><label className="block text-sm font-medium mb-1">Message Template</label><textarea value={form.message_template || ''} onChange={(e) => setForm({ ...form, message_template: e.target.value || null })} className="input-field" rows={4} placeholder="Use {{name}}, {{phone}}, etc. for variables" /></div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingCampaign ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingCampaign} onClose={() => setDeletingCampaign(null)} onConfirm={handleDelete} title="Delete Campaign" message={`Delete "${deletingCampaign?.name}"?`} />
    </div>
  )
}
