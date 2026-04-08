import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, ArrowRight } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EntitySearch from '@/components/shared/EntitySearch'
import { OPPORTUNITY_TYPES, OPPORTUNITY_STAGES, BO_OUTCOMES, OPPORTUNITY_SOURCE_OPTIONS } from '@/lib/constants'
import { formatDate, formatCurrency, getErrorMessage, cn } from '@/lib/utils'
import type { BusinessOpportunity, BOCreate, BOPipelineResponse, BOOutcomeUpdate } from '@/types'
import { toast } from 'sonner'

export default function OpportunitiesPage() {
  const [view, setView] = useState<'table' | 'pipeline'>('table')
  const [opportunities, setOpportunities] = useState<BusinessOpportunity[]>([])
  const [pipeline, setPipeline] = useState<BOPipelineResponse | null>(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [stageFilter, setStageFilter] = useState('')
  const [outcomeFilter, setOutcomeFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showForm, setShowForm] = useState(false)
  const [showOutcomeForm, setShowOutcomeForm] = useState(false)
  const [editingBo, setEditingBo] = useState<BusinessOpportunity | null>(null)
  const [outcomeBo, setOutcomeBo] = useState<BusinessOpportunity | null>(null)
  const [deletingBo, setDeletingBo] = useState<BusinessOpportunity | null>(null)
  const [form, setForm] = useState<BOCreate>({ opportunity_type: 'sip', expected_amount: 0 })
  const [outcomeForm, setOutcomeForm] = useState<BOOutcomeUpdate>({ outcome: 'won', outcome_date: new Date().toISOString().split('T')[0] })
  const [clientName, setClientName] = useState<string | null>(null)
  const [leadName, setLeadName] = useState<string | null>(null)

  useEffect(() => {
    if (view === 'table') loadData()
    else loadPipeline()
  }, [view, page, stageFilter, outcomeFilter, sortBy, sortOrder])

  const loadData = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, limit: 20, sort_by: sortBy, sort_order: sortOrder }
      if (stageFilter) params.stage = stageFilter
      if (outcomeFilter) params.outcome = outcomeFilter
      const { data } = await apiClient.get('/business-opportunities', { params })
      setOpportunities(data.opportunities)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch { toast.error('Failed to load opportunities') }
    finally { setLoading(false) }
  }

  const loadPipeline = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/business-opportunities/pipeline')
      setPipeline(data)
    } catch { toast.error('Failed to load pipeline') }
    finally { setLoading(false) }
  }

  const reload = () => view === 'table' ? loadData() : loadPipeline()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingBo) { await apiClient.put(`/business-opportunities/${editingBo.id}`, form); toast.success('Updated') }
      else { await apiClient.post('/business-opportunities', form); toast.success('Created') }
      setShowForm(false); reload()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleOutcome = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!outcomeBo) return
    try {
      await apiClient.patch(`/business-opportunities/${outcomeBo.id}/outcome`, outcomeForm)
      toast.success('Outcome updated')
      setShowOutcomeForm(false); reload()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingBo) return
    try { await apiClient.delete(`/business-opportunities/${deletingBo.id}`); toast.success('Deleted'); setDeletingBo(null); reload() }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const openCreateForm = () => {
    setEditingBo(null)
    setForm({ opportunity_type: 'sip', expected_amount: 0 })
    setClientName(null); setLeadName(null)
    setShowForm(true)
  }

  const columns: Column<BusinessOpportunity>[] = [
    { key: 'client_name', label: 'Client/Lead', render: (b) => <span className="font-medium">{b.client_name || b.lead_name || '-'}</span> },
    { key: 'opportunity_type', label: 'Type', render: (b) => b.opportunity_type.toUpperCase() },
    { key: 'opportunity_stage', label: 'Stage', render: (b) => <StatusBadge status={b.opportunity_stage} /> },
    { key: 'expected_amount', label: 'Amount', sortable: true, render: (b) => formatCurrency(b.expected_amount) },
    { key: 'outcome', label: 'Outcome', render: (b) => <StatusBadge status={b.outcome || 'open'} /> },
    { key: 'due_date', label: 'Due Date', sortable: true, render: (b) => formatDate(b.due_date) },
    { key: 'created_at', label: 'Created', sortable: true, render: (b) => formatDate(b.created_at) },
  ]

  const stageColors: Record<string, string> = { identified: 'border-gray-300', inbound: 'border-blue-300', proposed: 'border-purple-300' }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Business Opportunities</h1>
          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button onClick={() => setView('table')} className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === 'table' ? 'bg-white shadow font-medium' : 'text-gray-600'}`}>Table</button>
            <button onClick={() => setView('pipeline')} className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === 'pipeline' ? 'bg-white shadow font-medium' : 'text-gray-600'}`}>Pipeline</button>
          </div>
        </div>
        <button onClick={openCreateForm} className="btn-primary flex items-center gap-2"><Plus size={18} /> Add Opportunity</button>
      </div>

      {/* Pipeline Stats */}
      {pipeline && view === 'pipeline' && (
        <div className="grid grid-cols-4 gap-4">
          <div className="card p-4"><p className="text-sm text-gray-500">Total Open</p><p className="text-xl font-bold">{pipeline.total_open}</p><p className="text-sm text-gray-400">{formatCurrency(pipeline.total_open_amount)}</p></div>
          <div className="card p-4"><p className="text-sm text-gray-500">Won</p><p className="text-xl font-bold text-green-600">{pipeline.total_won}</p><p className="text-sm text-green-500">{formatCurrency(pipeline.total_won_amount)}</p></div>
          <div className="card p-4"><p className="text-sm text-gray-500">Lost</p><p className="text-xl font-bold text-red-600">{pipeline.total_lost}</p></div>
        </div>
      )}

      {view === 'pipeline' ? (
        <div className="grid grid-cols-3 gap-4">
          {['identified', 'inbound', 'proposed'].map((stage) => {
            const stageData = pipeline?.stages.find((s) => s.stage === stage)
            return (
              <div key={stage} className={cn('card border-t-4', stageColors[stage])}>
                <div className="p-3 border-b bg-gray-50">
                  <h3 className="font-semibold capitalize">{stage}</h3>
                  <p className="text-sm text-gray-500">{stageData?.count || 0} | {formatCurrency(stageData?.total_amount || 0)}</p>
                </div>
                <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                  {stageData?.opportunities.map((bo) => (
                    <div key={bo.id} className="p-3 hover:bg-gray-50">
                      <p className="text-sm font-medium">{bo.client_name || bo.lead_name}</p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-500">{bo.opportunity_type.toUpperCase()}</span>
                        <span className="text-sm font-medium">{formatCurrency(bo.expected_amount)}</span>
                      </div>
                      <div className="flex items-center gap-1 mt-2">
                        <button onClick={() => { setOutcomeBo(bo); setOutcomeForm({ outcome: 'won', outcome_date: new Date().toISOString().split('T')[0] }); setShowOutcomeForm(true) }} className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Won</button>
                        <button onClick={() => { setOutcomeBo(bo); setOutcomeForm({ outcome: 'lost', outcome_date: new Date().toISOString().split('T')[0] }); setShowOutcomeForm(true) }} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">Lost</button>
                      </div>
                    </div>
                  ))}
                  {(!stageData || stageData.opportunities.length === 0) && <p className="p-4 text-center text-sm text-gray-400">Empty</p>}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <>
          <div className="card p-4">
            <div className="flex flex-wrap items-center gap-3">
              <EnumSelect options={OPPORTUNITY_STAGES} value={stageFilter} onChange={(v) => { setStageFilter(v); setPage(1) }} allowEmpty emptyLabel="All Stages" className="w-40" />
              <EnumSelect options={BO_OUTCOMES} value={outcomeFilter} onChange={(v) => { setOutcomeFilter(v); setPage(1) }} allowEmpty emptyLabel="All Outcomes" className="w-40" />
            </div>
          </div>
          <DataTable columns={columns} data={opportunities} total={total} page={page} limit={20} totalPages={totalPages} onPageChange={setPage}
            onSort={(k, o) => { setSortBy(k); setSortOrder(o) }} sortBy={sortBy} sortOrder={sortOrder} loading={loading} emptyMessage="No opportunities found"
            actions={(bo) => (
              <div className="flex items-center gap-1">
                {bo.outcome === 'open' && <button onClick={() => { setOutcomeBo(bo); setOutcomeForm({ outcome: 'won', outcome_date: new Date().toISOString().split('T')[0] }); setShowOutcomeForm(true) }} className="p-1 rounded hover:bg-gray-100" title="Update Outcome"><ArrowRight size={16} className="text-primary-500" /></button>}
                <button onClick={() => { setEditingBo(bo); setForm({ client_id: bo.client_id, lead_id: bo.lead_id, opportunity_type: bo.opportunity_type, opportunity_stage: bo.opportunity_stage, opportunity_source: bo.opportunity_source, expected_amount: bo.expected_amount || 0, due_date: bo.due_date, notes: bo.notes }); setClientName(bo.client_name); setLeadName(bo.lead_name); setShowForm(true) }} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>
                <button onClick={() => setDeletingBo(bo)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>
              </div>
            )}
          />
        </>
      )}

      {/* Create/Edit Form */}
      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingBo ? 'Edit Opportunity' : 'Add Opportunity'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Client</label><EntitySearch entityType="clients" value={form.client_id || null} selectedName={clientName} onChange={(id, n) => { setForm({ ...form, client_id: id }); setClientName(n) }} /></div>
            <div><label className="block text-sm font-medium mb-1">Lead</label><EntitySearch entityType="leads" value={form.lead_id || null} selectedName={leadName} onChange={(id, n) => { setForm({ ...form, lead_id: id }); setLeadName(n) }} /></div>
            <div><label className="block text-sm font-medium mb-1">Type *</label><EnumSelect options={OPPORTUNITY_TYPES} value={form.opportunity_type} onChange={(v) => setForm({ ...form, opportunity_type: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Stage</label><EnumSelect options={OPPORTUNITY_STAGES} value={form.opportunity_stage || 'identified'} onChange={(v) => setForm({ ...form, opportunity_stage: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Source</label><EnumSelect options={OPPORTUNITY_SOURCE_OPTIONS} value={form.opportunity_source || ''} onChange={(v) => setForm({ ...form, opportunity_source: v || null })} allowEmpty emptyLabel="Select..." /></div>
            <div><label className="block text-sm font-medium mb-1">Expected Amount *</label><input type="number" value={form.expected_amount} onChange={(e) => setForm({ ...form, expected_amount: Number(e.target.value) })} className="input-field" min={0} required /></div>
            <div><label className="block text-sm font-medium mb-1">Due Date</label><input type="date" value={form.due_date || ''} onChange={(e) => setForm({ ...form, due_date: e.target.value || null })} className="input-field" /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Notes</label><textarea value={form.notes || ''} onChange={(e) => setForm({ ...form, notes: e.target.value || null })} className="input-field" rows={2} /></div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingBo ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      {/* Outcome Form */}
      <FormModal open={showOutcomeForm} onClose={() => setShowOutcomeForm(false)} title="Update Outcome">
        <form onSubmit={handleOutcome} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Outcome *</label><EnumSelect options={BO_OUTCOMES} value={outcomeForm.outcome} onChange={(v) => setOutcomeForm({ ...outcomeForm, outcome: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Date *</label><input type="date" value={outcomeForm.outcome_date} onChange={(e) => setOutcomeForm({ ...outcomeForm, outcome_date: e.target.value })} className="input-field" required /></div>
            <div><label className="block text-sm font-medium mb-1">Actual Amount</label><input type="number" value={outcomeForm.outcome_amount || ''} onChange={(e) => setOutcomeForm({ ...outcomeForm, outcome_amount: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Notes</label><textarea value={outcomeForm.notes || ''} onChange={(e) => setOutcomeForm({ ...outcomeForm, notes: e.target.value || null })} className="input-field" rows={2} /></div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowOutcomeForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">Save Outcome</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingBo} onClose={() => setDeletingBo(null)} onConfirm={handleDelete} title="Delete Opportunity" message="Delete this opportunity?" />
    </div>
  )
}
