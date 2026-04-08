import { useState, useEffect } from 'react'
import { RefreshCw, Download, Upload, Clock, CheckCircle, XCircle } from 'lucide-react'
import apiClient from '@/lib/api-client'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { formatDateTime, getErrorMessage } from '@/lib/utils'
import type { SyncStatus, SyncHistory } from '@/types'
import { toast } from 'sonner'

export default function SheetsSyncPage() {
  const [status, setStatus] = useState<SyncStatus | null>(null)
  const [history, setHistory] = useState<SyncHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [importing, setImporting] = useState(false)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [statusRes, historyRes] = await Promise.all([
        apiClient.get('/sheets/status'),
        apiClient.get('/sheets/history', { params: { limit: 20 } }),
      ])
      setStatus(statusRes.data)
      setHistory(Array.isArray(historyRes.data?.history) ? historyRes.data.history : Array.isArray(historyRes.data) ? historyRes.data : [])
    } catch { toast.error('Failed to load sync status') }
    finally { setLoading(false) }
  }

  const triggerSync = async () => {
    setSyncing(true)
    try {
      await apiClient.post('/sheets/sync')
      toast.success('Sync started')
      setTimeout(loadData, 2000)
    } catch (err) { toast.error(getErrorMessage(err)) }
    finally { setSyncing(false) }
  }

  const connectGoogle = async () => {
    try {
      // OAuth start is handled by Supabase Edge Function
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
      // Get the current user's JWT to pass to the edge function
      const token = apiClient.defaults.headers.common['Authorization'] as string
      const url = `${supabaseUrl}/functions/v1/google-oauth-start`
      const res = await fetch(url, { headers: { Authorization: token || '' } })
      const data = await res.json()
      if (data.url || data.auth_url) {
        window.location.href = data.url || data.auth_url
      } else {
        toast.error('Failed to get Google OAuth URL. Make sure Google credentials are configured.')
      }
    } catch (err) { toast.error(getErrorMessage(err)) }
  }

  const triggerImport = async () => {
    setImporting(true)
    try {
      await apiClient.post('/sheets/import')
      toast.success('Import started')
      setTimeout(loadData, 2000)
    } catch (err) { toast.error(getErrorMessage(err)) }
    finally { setImporting(false) }
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Google Sheets Sync</h1>

      {/* Connect Google Account */}
      {!status?.google_connected && (
        <div className="card p-6 border-2 border-dashed border-orange-300 bg-orange-50">
          <div className="text-center space-y-3">
            <h3 className="font-semibold text-lg">Connect Your Google Account</h3>
            <p className="text-sm text-gray-600">
              Link your Google account to sync leads, clients, tasks, and more with Google Sheets automatically.
            </p>
            <button onClick={connectGoogle} className="btn-primary inline-flex items-center gap-2 px-6 py-2.5">
              <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Connect Google Account
            </button>
          </div>
        </div>
      )}

      {/* Status */}
      <div className="card p-6">
        <h3 className="font-semibold mb-4">Sync Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500">Google Account</p>
            <p className="font-medium">{status?.google_connected ? `Connected (${status?.google_email || ''})` : 'Not connected'}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500">Status</p>
            <p className="font-medium">{status?.is_syncing ? 'Syncing...' : 'Idle'}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500">Last Sync</p>
            <p className="font-medium text-sm">{formatDateTime(status?.last_sync_at)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-500">Sheet</p>
            <p className="font-medium text-sm truncate">{status?.sheet_id ? 'Connected' : 'Not connected'}</p>
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={triggerSync} disabled={syncing || !status?.google_connected} className="btn-primary flex items-center gap-2">
            <Upload size={16} /> {syncing ? 'Syncing...' : 'Sync to Sheet'}
          </button>
          <button onClick={triggerImport} disabled={importing || !status?.google_connected} className="btn-secondary flex items-center gap-2">
            <Download size={16} /> {importing ? 'Importing...' : 'Import from Sheet'}
          </button>
          <button onClick={loadData} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      {/* History */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold flex items-center gap-2"><Clock size={18} /> Sync History</h3>
        </div>
        <div className="divide-y divide-gray-100">
          {history.length === 0 ? (
            <p className="p-6 text-center text-gray-500">No sync history</p>
          ) : (
            history.map((h) => (
              <div key={h.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  {h.status === 'success' ? <CheckCircle size={18} className="text-green-500" /> : <XCircle size={18} className="text-red-500" />}
                  <div>
                    <p className="text-sm font-medium">{h.sync_type}</p>
                    <p className="text-xs text-gray-500">{formatDateTime(h.created_at)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm">{h.records_synced} records</p>
                  {h.error_message && <p className="text-xs text-red-500 max-w-xs truncate">{h.error_message}</p>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
