import { useState, useEffect } from 'react'
import { Upload, Trash2, Share2, FileText, ExternalLink } from 'lucide-react'
import apiClient from '@/lib/api-client'
import EntitySearch from '@/components/shared/EntitySearch'
import ConfirmDialog from '@/components/shared/ConfirmDialog'
import { formatDate, getErrorMessage } from '@/lib/utils'
import type { Document } from '@/types'
import { toast } from 'sonner'

export default function DocumentsPage() {
  const [clientId, setClientId] = useState<string | null>(null)
  const [clientName, setClientName] = useState<string | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [deletingDoc, setDeletingDoc] = useState<Document | null>(null)

  useEffect(() => {
    if (clientId) loadDocuments()
  }, [clientId])

  const loadDocuments = async () => {
    if (!clientId) return
    setLoading(true)
    try {
      const { data } = await apiClient.get('/documents', { params: { client_id: clientId } })
      setDocuments(data.documents)
    } catch { toast.error('Failed to load documents') }
    finally { setLoading(false) }
  }

  const handleUpload = async (file: File) => {
    if (!clientId) return
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('client_id', clientId)
    formData.append('name', file.name)
    try {
      await apiClient.post('/documents', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      toast.success('Document uploaded')
      loadDocuments()
    } catch (err) { toast.error(getErrorMessage(err)) }
    finally { setUploading(false) }
  }

  const handleShare = async (doc: Document, via: string) => {
    try {
      await apiClient.post(`/documents/${doc.id}/share`, { document_id: doc.id, share_via: via })
      toast.success(`Shared via ${via}`)
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const handleDelete = async () => {
    if (!deletingDoc) return
    try { await apiClient.delete(`/documents/${deletingDoc.id}`); toast.success('Deleted'); setDeletingDoc(null); loadDocuments() }
    catch (err) { toast.error(getErrorMessage(err)) }
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Documents</h1>

      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Select Client</label>
            <EntitySearch entityType="clients" value={clientId} selectedName={clientName} onChange={(id, n) => { setClientId(id); setClientName(n) }} />
          </div>
          {clientId && (
            <label className="btn-primary flex items-center gap-2 mt-5 cursor-pointer">
              <Upload size={18} /> {uploading ? 'Uploading...' : 'Upload'}
              <input type="file" onChange={(e) => { if (e.target.files?.[0]) handleUpload(e.target.files[0]); e.target.value = '' }} className="hidden" disabled={uploading} />
            </label>
          )}
        </div>
      </div>

      {clientId ? (
        <div className="card">
          {loading ? (
            <div className="p-8 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
          ) : documents.length === 0 ? (
            <p className="p-12 text-center text-gray-500">No documents found</p>
          ) : (
            <div className="divide-y divide-gray-100">
              {documents.map((doc) => (
                <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <FileText size={24} className="text-gray-400" />
                    <div>
                      <p className="font-medium text-sm">{doc.name}</p>
                      <p className="text-xs text-gray-500">{doc.document_type || 'Document'} | {formatFileSize(doc.file_size)} | {formatDate(doc.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {doc.file_url && <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="p-1 rounded hover:bg-gray-100"><ExternalLink size={16} className="text-gray-500" /></a>}
                    <button onClick={() => handleShare(doc, 'whatsapp')} className="p-1 rounded hover:bg-gray-100" title="Share via WhatsApp"><Share2 size={16} className="text-green-500" /></button>
                    <button onClick={() => setDeletingDoc(doc)} className="p-1 rounded hover:bg-gray-100"><Trash2 size={16} className="text-red-500" /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="card p-12 text-center text-gray-500">Select a client to view documents</div>
      )}

      <ConfirmDialog open={!!deletingDoc} onClose={() => setDeletingDoc(null)} onConfirm={handleDelete} title="Delete Document" message={`Delete "${deletingDoc?.name}"?`} />
    </div>
  )
}
