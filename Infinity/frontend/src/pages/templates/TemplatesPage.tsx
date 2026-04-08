import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Eye } from 'lucide-react'
import apiClient from '@/lib/api-client'
import DataTable, { type Column } from '@/components/shared/DataTable'
import FormModal from '@/components/shared/FormModal'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import EnumSelect from '@/components/shared/EnumSelect'
import { CHANNEL_OPTIONS } from '@/lib/constants'
import { formatDate, getErrorMessage } from '@/lib/utils'
import type { MessageTemplate, MessageTemplateCreate } from '@/types'
import { toast } from 'sonner'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<MessageTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<MessageTemplate | null>(null)
  const [deletingTemplate, setDeletingTemplate] = useState<MessageTemplate | null>(null)
  const [previewContent, setPreviewContent] = useState<string | null>(null)
  const [form, setForm] = useState<MessageTemplateCreate>({ template_type: 'custom', channel: 'whatsapp', name: '', content: '' })

  useEffect(() => { loadTemplates() }, [])

  const loadTemplates = async () => {
    setLoading(true)
    try {
      const { data } = await apiClient.get('/templates')
      setTemplates(data.templates)
    } catch { toast.error('Failed to load templates') }
    finally { setLoading(false) }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingTemplate) { await apiClient.put(`/templates/${editingTemplate.id}`, form); toast.success('Updated') }
      else { await apiClient.post('/templates', form); toast.success('Created') }
      setShowForm(false); loadTemplates()
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingTemplate) return
    try { await apiClient.delete(`/templates/${deletingTemplate.id}`); toast.success('Deleted'); setDeletingTemplate(null); loadTemplates() }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handlePreview = async (template: MessageTemplate) => {
    try {
      const { data } = await apiClient.post('/templates/render', { template_id: template.id, variables: { name: 'John Doe', phone: '+919876543210' } })
      setPreviewContent(data.rendered_content)
    } catch { setPreviewContent(template.content) }
  }

  const columns: Column<MessageTemplate>[] = [
    { key: 'name', label: 'Name', render: (t) => <span className="font-medium">{t.name}</span> },
    { key: 'template_type', label: 'Type', render: (t) => t.template_type },
    { key: 'channel', label: 'Channel', render: (t) => t.channel },
    { key: 'is_system', label: 'System', render: (t) => t.is_system ? <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">System</span> : <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">Custom</span> },
    { key: 'is_active', label: 'Active', render: (t) => t.is_active ? <span className="text-green-500">Yes</span> : <span className="text-red-500">No</span> },
    { key: 'updated_at', label: 'Updated', render: (t) => formatDate(t.updated_at) },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Message Templates</h1>
        <button onClick={() => { setEditingTemplate(null); setForm({ template_type: 'custom', channel: 'whatsapp', name: '', content: '' }); setShowForm(true) }} className="btn-primary flex items-center gap-2"><Plus size={18} /> New Template</button>
      </div>

      <DataTable columns={columns} data={templates} total={templates.length} page={1} limit={100} totalPages={1} onPageChange={() => {}} loading={loading} emptyMessage="No templates"
        actions={(t) => (
          <div className="flex items-center gap-1">
            <button onClick={() => handlePreview(t)} className="p-1 rounded hover:bg-gray-100"><Eye size={16} className="text-gray-500" /></button>
            {!t.is_system && <button onClick={() => { setEditingTemplate(t); setForm({ template_type: t.template_type, channel: t.channel, name: t.name, subject: t.subject, content: t.content }); setShowForm(true) }} className="p-1 rounded hover:bg-gray-100"><Edit size={16} className="text-gray-500" /></button>}
            {!t.is_system && <button onClick={() => setDeletingTemplate(t)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>}
          </div>
        )}
      />

      {previewContent && (
        <FormModal open={true} onClose={() => setPreviewContent(null)} title="Template Preview">
          <div className="p-4 bg-gray-50 rounded-lg whitespace-pre-wrap text-sm">{previewContent}</div>
        </FormModal>
      )}

      <FormModal open={showForm} onClose={() => setShowForm(false)} title={editingTemplate ? 'Edit Template' : 'New Template'} size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Name *</label><input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" required /></div>
            <div><label className="block text-sm font-medium mb-1">Channel *</label><EnumSelect options={CHANNEL_OPTIONS} value={form.channel} onChange={(v) => setForm({ ...form, channel: v })} /></div>
            <div><label className="block text-sm font-medium mb-1">Type</label><input type="text" value={form.template_type} onChange={(e) => setForm({ ...form, template_type: e.target.value })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Subject</label><input type="text" value={form.subject || ''} onChange={(e) => setForm({ ...form, subject: e.target.value || null })} className="input-field" /></div>
          </div>
          <div><label className="block text-sm font-medium mb-1">Content *</label><textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} className="input-field font-mono text-sm" rows={8} required placeholder="Use {{name}}, {{phone}}, {{email}} for variables" /></div>
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary">{editingTemplate ? 'Update' : 'Create'}</button>
          </div>
        </form>
      </FormModal>

      <ConfirmDialog open={!!deletingTemplate} onClose={() => setDeletingTemplate(null)} onConfirm={handleDelete} title="Delete Template" message={`Delete "${deletingTemplate?.name}"?`} />
    </div>
  )
}
