import { useState, useEffect } from 'react'
import apiClient from '@/lib/api-client'
import EnumSelect from '@/components/shared/EnumSelect'
import { GENDER_OPTIONS } from '@/lib/constants'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { getErrorMessage, normalizePhone } from '@/lib/utils'
import type { Profile, ProfileUpdate } from '@/types'
import { toast } from 'sonner'

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<ProfileUpdate>({})

  useEffect(() => { loadProfile() }, [])

  const loadProfile = async () => {
    try {
      const { data } = await apiClient.get('/profile')
      setProfile(data)
      setForm({
        name: data.name, phone: data.phone, age: data.age, gender: data.gender,
        area: data.area, num_employees: data.num_employees, employee_names: data.employee_names,
        eod_time: data.eod_time, notification_email: data.notification_email,
        notification_whatsapp: data.notification_whatsapp, notification_eod: data.notification_eod,
        morning_schedule_time: data.morning_schedule_time, afternoon_schedule_time: data.afternoon_schedule_time,
        eod_schedule_time: data.eod_schedule_time, whatsapp_number: data.whatsapp_number,
        email_daily_enabled: data.email_daily_enabled, whatsapp_daily_enabled: data.whatsapp_daily_enabled,
        whatsapp_greetings_enabled: data.whatsapp_greetings_enabled,
      })
    } catch { toast.error('Failed to load profile') }
    finally { setLoading(false) }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      // Clean up form: remove empty strings and null values to avoid 422 errors
      const cleanedForm: Record<string, unknown> = {}
      for (const [key, value] of Object.entries(form)) {
        if (value === '' || value === null || value === undefined) continue
        cleanedForm[key] = value
      }
      // Strip seconds from time fields (backend expects HH:MM)
      for (const key of ['eod_time', 'morning_schedule_time', 'afternoon_schedule_time', 'eod_schedule_time']) {
        if (cleanedForm[key] && typeof cleanedForm[key] === 'string') {
          cleanedForm[key] = (cleanedForm[key] as string).slice(0, 5)
        }
      }
      // Normalize phone to +91XXXXXXXXXX format
      if (cleanedForm.phone) {
        cleanedForm.phone = normalizePhone(cleanedForm.phone as string)
      }
      const { data } = await apiClient.put('/profile', cleanedForm)
      setProfile(data)
      toast.success('Profile updated')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: unknown } }
      console.error('Profile update error:', JSON.stringify(axiosErr?.response?.data))
      toast.error(getErrorMessage(err))
    }
    finally { setSaving(false) }
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Profile Settings</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card p-6">
          <h3 className="font-semibold mb-4">Personal Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm font-medium mb-1">Name</label><input type="text" value={form.name || ''} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Phone</label><input type="tel" value={form.phone || ''} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Age</label><input type="number" value={form.age || ''} onChange={(e) => setForm({ ...form, age: e.target.value ? Number(e.target.value) : null })} className="input-field" min={18} max={100} /></div>
            <div><label className="block text-sm font-medium mb-1">Gender</label><EnumSelect options={GENDER_OPTIONS} value={form.gender || ''} onChange={(v) => setForm({ ...form, gender: v || null })} allowEmpty emptyLabel="Select..." /></div>
            <div><label className="block text-sm font-medium mb-1">Area</label><input type="text" value={form.area || ''} onChange={(e) => setForm({ ...form, area: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">WhatsApp Number</label><input type="tel" value={form.whatsapp_number || ''} onChange={(e) => setForm({ ...form, whatsapp_number: e.target.value || null })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Employees</label><input type="number" value={form.num_employees || ''} onChange={(e) => setForm({ ...form, num_employees: Number(e.target.value) || 0 })} className="input-field" min={0} /></div>
            <div><label className="block text-sm font-medium mb-1">EOD Time</label><input type="time" value={form.eod_time || '18:00'} onChange={(e) => setForm({ ...form, eod_time: e.target.value })} className="input-field" /></div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-4">Notification Preferences</h3>
          <div className="space-y-3">
            {[
              { key: 'email_daily_enabled', label: 'Daily Email Summary' },
              { key: 'whatsapp_daily_enabled', label: 'Daily WhatsApp Summary' },
              { key: 'whatsapp_greetings_enabled', label: 'WhatsApp Greetings (GM/GE/GN)' },
              { key: 'notification_email', label: 'Email Notifications' },
              { key: 'notification_whatsapp', label: 'WhatsApp Notifications' },
              { key: 'notification_eod', label: 'EOD Summary' },
            ].map(({ key, label }) => (
              <label key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium">{label}</span>
                <input
                  type="checkbox"
                  checked={(form as Record<string, unknown>)[key] as boolean || false}
                  onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                  className="rounded text-primary-600 w-5 h-5"
                />
              </label>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-4 mt-4">
            <div><label className="block text-sm font-medium mb-1">Morning Schedule</label><input type="time" value={form.morning_schedule_time || '07:00'} onChange={(e) => setForm({ ...form, morning_schedule_time: e.target.value })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">Afternoon Update</label><input type="time" value={form.afternoon_schedule_time || '14:00'} onChange={(e) => setForm({ ...form, afternoon_schedule_time: e.target.value })} className="input-field" /></div>
            <div><label className="block text-sm font-medium mb-1">EOD Summary</label><input type="time" value={form.eod_schedule_time || '19:00'} onChange={(e) => setForm({ ...form, eod_schedule_time: e.target.value })} className="input-field" /></div>
          </div>
        </div>

        {profile?.google_connected && (
          <div className="card p-6">
            <h3 className="font-semibold mb-2">Google Integration</h3>
            <p className="text-sm text-green-600 mb-2">Connected: {profile.google_email}</p>
            <button type="button" onClick={async () => { try { await apiClient.post('/profile/google/disconnect'); toast.success('Disconnected'); loadProfile() } catch { toast.error('Failed') } }} className="btn-danger text-sm">Disconnect Google</button>
          </div>
        )}

        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save Changes'}</button>
      </form>
    </div>
  )
}
