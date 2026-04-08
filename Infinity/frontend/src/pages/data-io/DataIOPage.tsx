import { useState } from 'react'
import { Upload, Download, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react'
import apiClient from '@/lib/api-client'
import { getErrorMessage } from '@/lib/utils'
import { toast } from 'sonner'

const exportEntities = [
  { key: 'clients', label: 'Clients' },
  { key: 'leads', label: 'Leads' },
  { key: 'tasks', label: 'Tasks' },
  { key: 'touchpoints', label: 'Touchpoints' },
  { key: 'goals', label: 'Goals' },
  { key: 'opportunities', label: 'Opportunities' },
  { key: 'all', label: 'All Data (Multi-sheet)' },
]

export default function DataIOPage() {
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string; details?: unknown } | null>(null)
  const [exporting, setExporting] = useState<string | null>(null)

  const handleImport = async (entityType: 'clients' | 'leads', file: File) => {
    setUploading(true)
    setUploadResult(null)
    const formData = new FormData()
    formData.append('file', file)
    try {
      // First validate
      const validateForm = new FormData()
      validateForm.append('file', file)
      const { data: validation } = await apiClient.post(`/data/import/validate?entity_type=${entityType}`, validateForm, { headers: { 'Content-Type': 'multipart/form-data' } })

      if (validation.errors?.length > 0) {
        setUploadResult({ success: false, message: `Validation errors found: ${validation.errors.length} issues`, details: validation.errors })
        setUploading(false)
        return
      }

      // Then import
      const { data } = await apiClient.post(`/data/import/${entityType}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setUploadResult({ success: true, message: `Imported ${data.imported_count || data.total || 0} ${entityType} successfully` })
      toast.success('Import complete')
    } catch (err) {
      setUploadResult({ success: false, message: getErrorMessage(err) })
      toast.error('Import failed')
    } finally {
      setUploading(false)
    }
  }

  const handleExport = async (entity: string) => {
    setExporting(entity)
    try {
      const { data, headers } = await apiClient.get(`/data/export/${entity}`, { responseType: 'blob' })
      const blob = new Blob([data], { type: headers['content-type'] || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${entity}_export.xlsx`
      a.click()
      URL.revokeObjectURL(url)
      toast.success(`${entity} exported`)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setExporting(null)
    }
  }

  const handleDownloadTemplate = async (entityType: string) => {
    try {
      const { data, headers } = await apiClient.get(`/data/import/template/${entityType}`, { responseType: 'blob' })
      const blob = new Blob([data], { type: headers['content-type'] })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${entityType}_template.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Data Import / Export</h1>

      {/* Import Section */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Upload size={20} /> Import Data</h2>
        <div className="grid grid-cols-2 gap-6">
          {(['clients', 'leads'] as const).map((entity) => (
            <div key={entity} className="border border-dashed border-gray-300 rounded-lg p-6 text-center">
              <FileSpreadsheet size={32} className="text-gray-400 mx-auto mb-2" />
              <h3 className="font-medium capitalize mb-2">Import {entity}</h3>
              <p className="text-sm text-gray-500 mb-3">Upload Excel (.xlsx) or CSV file</p>
              <div className="flex justify-center gap-2">
                <label className="btn-primary text-sm cursor-pointer">
                  {uploading ? 'Uploading...' : 'Upload File'}
                  <input type="file" accept=".xlsx,.xls,.csv" onChange={(e) => { if (e.target.files?.[0]) handleImport(entity, e.target.files[0]); e.target.value = '' }} className="hidden" disabled={uploading} />
                </label>
                <button onClick={() => handleDownloadTemplate(entity)} className="btn-secondary text-sm">Download Template</button>
              </div>
            </div>
          ))}
        </div>

        {uploadResult && (
          <div className={`mt-4 p-4 rounded-lg flex items-start gap-2 ${uploadResult.success ? 'bg-green-50' : 'bg-red-50'}`}>
            {uploadResult.success ? <CheckCircle size={20} className="text-green-600 shrink-0 mt-0.5" /> : <AlertCircle size={20} className="text-red-600 shrink-0 mt-0.5" />}
            <div>
              <p className={`text-sm font-medium ${uploadResult.success ? 'text-green-700' : 'text-red-700'}`}>{uploadResult.message}</p>
              {uploadResult.details && (
                <pre className="text-xs mt-2 text-gray-600 overflow-x-auto">{JSON.stringify(uploadResult.details, null, 2)}</pre>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Export Section */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Download size={20} /> Export Data</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {exportEntities.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => handleExport(key)}
              disabled={exporting === key}
              className="btn-secondary flex items-center justify-center gap-2 py-3"
            >
              <Download size={16} />
              {exporting === key ? 'Exporting...' : label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
