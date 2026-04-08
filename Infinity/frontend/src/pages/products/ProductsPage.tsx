import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Search } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import StatusBadge from '@/components/shared/StatusBadge'
import EnumSelect from '@/components/shared/EnumSelect'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EntitySearch from '@/components/shared/EntitySearch'
import { PRODUCT_CATEGORIES, PRODUCT_STATUS, INVESTMENT_TYPES, PREMIUM_FREQUENCY } from '@/lib/constants'
import { formatCurrency, formatDate, getErrorMessage, enumToLabel } from '@/lib/utils'
import type { ClientProduct, ClientProductCreate, PortfolioSummary } from '@/types'
import { toast } from 'sonner'

export default function ProductsPage() {
  const [view, setView] = useState<'search' | 'client'>('client')
  const [clientId, setClientId] = useState<string | null>(null)
  const [clientName, setClientName] = useState<string | null>(null)
  const [products, setProducts] = useState<ClientProduct[]>([])
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [totalInvested, setTotalInvested] = useState(0)
  const [totalCurrent, setTotalCurrent] = useState(0)
  const [loading, setLoading] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingProduct, setEditingProduct] = useState<ClientProduct | null>(null)
  const [deletingProduct, setDeletingProduct] = useState<ClientProduct | null>(null)
  const [form, setForm] = useState<ClientProductCreate>({ client_id: '', product_name: '', category: 'mutual_fund' })

  const loadProducts = async (cId: string) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = {}
      if (categoryFilter) params.category = categoryFilter
      const { data } = await apiClient.get(`/client-products/client/${cId}`, { params })
      setProducts(data.products)
      setTotalInvested(data.total_invested)
      setTotalCurrent(data.total_current_value)
    } catch { toast.error('Failed to load products') }
    finally { setLoading(false) }
  }

  const loadPortfolio = async (cId: string) => {
    try {
      const { data } = await apiClient.get(`/client-products/client/${cId}/portfolio`)
      setPortfolio(data)
    } catch { /* silently fail */ }
  }

  useEffect(() => {
    if (clientId) { loadProducts(clientId); loadPortfolio(clientId) }
  }, [clientId, categoryFilter])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingProduct) { await apiClient.put(`/client-products/${editingProduct.id}`, form); toast.success('Updated') }
      else { await apiClient.post('/client-products', form); toast.success('Added') }
      setShowForm(false)
      if (clientId) loadProducts(clientId)
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingProduct) return
    try { await apiClient.delete(`/client-products/${deletingProduct.id}`); toast.success('Deleted'); setDeletingProduct(null); if (clientId) loadProducts(clientId) }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const columns: Column<ClientProduct>[] = [
    { key: 'product_name', label: 'Product', render: (p) => <span className="font-medium">{p.product_name}</span> },
    { key: 'category', label: 'Category', render: (p) => enumToLabel(p.category) },
    { key: 'provider_name', label: 'Provider', render: (p) => p.provider_name || '-' },
    { key: 'investment_type', label: 'Type', render: (p) => p.investment_type.toUpperCase() },
    { key: 'invested_amount', label: 'Invested', render: (p) => formatCurrency(p.invested_amount) },
    { key: 'current_value', label: 'Current', render: (p) => formatCurrency(p.current_value) },
    { key: 'gain_loss', label: 'Gain/Loss', render: (p) => (
      <span className={p.gain_loss && p.gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
        {formatCurrency(p.gain_loss)} ({p.gain_loss_percent?.toFixed(1)}%)
      </span>
    )},
    { key: 'status', label: 'Status', render: (p) => <StatusBadge status={p.status} /> },
  ]

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Client Products & Portfolio</h1>

      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Select Client</label>
            <EntitySearch entityType="clients" value={clientId} selectedName={clientName} onChange={(id, n) => { setClientId(id); setClientName(n) }} placeholder="Search client..." />
          </div>
          {clientId && (
            <>
              <EnumSelect options={PRODUCT_CATEGORIES} value={categoryFilter} onChange={setCategoryFilter} allowEmpty emptyLabel="All Categories" className="w-48" />
              <button onClick={() => { setEditingProduct(null); setForm({ client_id: clientId, product_name: '', category: 'mutual_fund' }); setShowForm(true) }} className="btn-primary flex items-center gap-2 mt-5"><Plus size={18} /> Add Product</button>
            </>
          )}
        </div>
      </div>

      {/* Portfolio Summary */}
      {portfolio && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4"><p className="text-sm text-gray-500">Total AUM</p><p className="text-xl font-bold">{formatCurrency(portfolio.total_aum)}</p></div>
          <div className="card p-4"><p className="text-sm text-gray-500">Total Invested</p><p className="text-xl font-bold">{formatCurrency(portfolio.total_invested)}</p></div>
          <div className="card p-4"><p className="text-sm text-gray-500">Gain/Loss</p><p className={`text-xl font-bold ${portfolio.total_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>{formatCurrency(portfolio.total_gain_loss)} ({portfolio.total_gain_loss_percent.toFixed(1)}%)</p></div>
          <div className="card p-4"><p className="text-sm text-gray-500">Total SIP</p><p className="text-xl font-bold">{formatCurrency(portfolio.total_sip)}</p></div>
        </div>
      )}

      {clientId ? (
        <DataTable columns={columns} data={products} total={products.length} page={1} limit={100} totalPages={1} onPageChange={() => {}} loading={loading} emptyMessage="No products found"
          actions={(p) => (
            <div className="flex items-center gap-1">
              <button onClick={() => { setEditingProduct(p); setForm({ ...p }); setShowForm(true) }} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>
              <button onClick={() => setDeletingProduct(p)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>
            </div>
          )}
        />
      ) : (
        <div className="card p-12 text-center text-gray-500">Select a client to view their portfolio</div>
      )}

      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingProduct ? 'Edit Product' : 'Add Product'} size="xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div><label className="block text-sm font-medium mb-1">Product Name *</label><input type="text" value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} className="input-field" required /></div>
            <div><label className="block text-sm font-medium mb-1">Category *</label><EnumSelect options={PRODUCT_CATEGORIES} value={form.category} onChange={(v) => setForm({ ...form, category: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Provider</label><input type="text" value={form.provider_name || ''} onChange={(e) => setForm({ ...form, provider_name: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Investment Type</label><EnumSelect options={INVESTMENT_TYPES} value={form.investment_type || 'lumpsum'} onChange={(v) => setForm({ ...form, investment_type: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Invested Amount</label><input type="number" value={form.invested_amount || ''} onChange={(e) => setForm({ ...form, invested_amount: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">Current Value</label><input type="number" value={form.current_value || ''} onChange={(e) => setForm({ ...form, current_value: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">SIP Amount</label><input type="number" value={form.sip_amount || ''} onChange={(e) => setForm({ ...form, sip_amount: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">Units</label><input type="number" value={form.units || ''} onChange={(e) => setForm({ ...form, units: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} step={0.001} /></div>
            <div><label className="block text-sm font-medium mb-1">NAV</label><input type="number" value={form.nav || ''} onChange={(e) => setForm({ ...form, nav: e.target.value ? Number(e.target.value) : null })} className="input-field" min={0} step={0.01} /></div>
            <div><label className="block text-sm font-medium mb-1">Start Date</label><input type="date" value={form.start_date || ''} onChange={(e) => setForm({ ...form, start_date: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Maturity Date</label><input type="date" value={form.maturity_date || ''} onChange={(e) => setForm({ ...form, maturity_date: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Folio/Policy No.</label><input type="text" value={form.folio_number || form.policy_number || ''} onChange={(e) => setForm({ ...form, folio_number: e.target.value || null })} className="input-field" /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Notes</label><textarea value={form.notes || ''} onChange={(e) => setForm({ ...form, notes: e.target.value || null })} className="input-field" rows={2} /></div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingProduct ? 'Update' : 'Add'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingProduct} onClose={() => setDeletingProduct(null)} onConfirm={handleDelete} title="Delete Product" message={`Delete "${deletingProduct?.product_name}"?`} />
    </div>
  )
}
