import { useState, useRef, useEffect, useCallback } from 'react'
import { Mic, MicOff, Camera, Upload, Check, X, Loader2, AlertTriangle } from 'lucide-react'
import { supabase } from '@/lib/supabase'
import apiClient from '@/lib/api-client'
import { useAuth } from '@/contexts/auth-context'
import { cn, getErrorMessage } from '@/lib/utils'
import { toast } from 'sonner'

// ─── Types ────────────────────────────────────────────────────
interface ExtractedAction {
  intent: string
  confidence: number
  display_summary: string
  entities: Record<string, unknown>
  warnings: string[]
}

interface ProcessingResult {
  id: string
  status: string
  transcript?: string
  parsed_data?: {
    actions: ExtractedAction[]
    confirmed_actions?: Record<string, unknown>
  }
  error_message?: string
}

type Tab = 'voice' | 'ocr'

// ─── Main Page ────────────────────────────────────────────────
export default function VoiceOCRPage() {
  const [activeTab, setActiveTab] = useState<Tab>('voice')

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Voice & OCR Input</h1>

      {/* Tab Switcher */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('voice')}
          className={cn(
            'px-4 py-2 rounded-md text-sm font-medium transition-colors',
            activeTab === 'voice' ? 'bg-white shadow text-primary-700' : 'text-gray-500 hover:text-gray-700'
          )}
        >
          <Mic size={16} className="inline mr-2" />Voice Note
        </button>
        <button
          onClick={() => setActiveTab('ocr')}
          className={cn(
            'px-4 py-2 rounded-md text-sm font-medium transition-colors',
            activeTab === 'ocr' ? 'bg-white shadow text-primary-700' : 'text-gray-500 hover:text-gray-700'
          )}
        >
          <Camera size={16} className="inline mr-2" />Diary Scan
        </button>
      </div>

      {activeTab === 'voice' ? <VoiceSection /> : <OCRSection />}
    </div>
  )
}

// ─── Voice Section ────────────────────────────────────────────
function VoiceSection() {
  const { user } = useAuth()
  const [recording, setRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [inputMode, setInputMode] = useState<'quick' | 'eod'>('quick')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const startTimeRef = useRef<number>(0)

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []
      startTimeRef.current = Date.now()

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
        stream.getTracks().forEach(t => t.stop())
      }

      mediaRecorder.start(250) // collect chunks every 250ms
      setRecording(true)
    } catch {
      toast.error('Could not access microphone. Please allow microphone permission.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setRecording(false)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('audio/')) {
      toast.error('Please upload an audio file')
      return
    }
    setAudioBlob(file)
    setAudioUrl(URL.createObjectURL(file))
  }

  const processVoice = async () => {
    if (!audioBlob || !user) return
    setProcessing(true)
    setResult(null)

    try {
      const voiceInputId = crypto.randomUUID()
      const fileName = `${user.id}/${voiceInputId}.webm`
      const duration = (Date.now() - (startTimeRef.current || Date.now())) / 1000

      // 1. Upload to Supabase Storage
      const { error: uploadError } = await supabase.storage
        .from('voice-notes')
        .upload(fileName, audioBlob, { contentType: audioBlob.type })

      if (uploadError) throw new Error(`Upload failed: ${uploadError.message}`)

      const { data: urlData } = supabase.storage.from('voice-notes').getPublicUrl(fileName)
      const publicUrl = urlData.publicUrl

      // 2. Insert row into voice_inputs table
      const { error: insertError } = await supabase.from('voice_inputs').insert({
        id: voiceInputId,
        user_id: user.id,
        audio_url: publicUrl,
        audio_duration_seconds: duration > 0 ? Math.round(duration) : null,
        audio_size_bytes: audioBlob.size,
        input_mode: inputMode,
        status: 'pending',
      })

      if (insertError) throw new Error(`DB insert failed: ${insertError.message}`)

      // 3. Call enqueue endpoint
      await apiClient.post('/voice/enqueue', {
        user_id: user.id,
        audio_url: publicUrl,
        voice_input_id: voiceInputId,
        input_mode: inputMode,
        audio_size_bytes: audioBlob.size,
        audio_duration_seconds: duration > 0 ? Math.round(duration) : null,
        audio_mime_type: audioBlob.type,
        idempotency_key: voiceInputId,
      })

      toast.success('Voice note submitted! Processing...')

      // 4. Poll for results
      pollStatus('voice', voiceInputId, user.id)
    } catch (err) {
      toast.error(getErrorMessage(err))
      setProcessing(false)
    }
  }

  const pollStatus = useCallback(async (type: 'voice' | 'ocr', id: string, userId: string) => {
    const endpoint = type === 'voice' ? '/voice/status' : '/ocr/status'
    let attempts = 0
    const maxAttempts = 60 // 2 minutes max

    const poll = async () => {
      try {
        const { data } = await apiClient.get(`${endpoint}/${id}`, { params: { user_id: userId } })
        const status = data.status

        if (status === 'needs_confirmation' || status === 'done' || status === 'failed') {
          setResult(data)
          setProcessing(false)
          if (status === 'failed') {
            toast.error(data.error_message || 'Processing failed')
          } else if (status === 'needs_confirmation') {
            toast.success('Actions extracted! Please review below.')
          }
          return
        }

        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000) // poll every 2s
        } else {
          toast.error('Processing timed out. Please try again.')
          setProcessing(false)
        }
      } catch {
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 3000)
        } else {
          setProcessing(false)
        }
      }
    }

    poll()
  }, [])

  const reset = () => {
    setAudioBlob(null)
    setAudioUrl(null)
    setResult(null)
    setProcessing(false)
  }

  return (
    <div className="space-y-4">
      {/* Mode Selection */}
      <div className="card p-4">
        <label className="block text-sm font-medium mb-2">Input Mode</label>
        <div className="flex gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="quick" checked={inputMode === 'quick'} onChange={() => setInputMode('quick')} className="text-primary-600" />
            <span className="text-sm">Quick (single action)</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="eod" checked={inputMode === 'eod'} onChange={() => setInputMode('eod')} className="text-primary-600" />
            <span className="text-sm">EOD (multiple actions)</span>
          </label>
        </div>
      </div>

      {/* Recording Controls */}
      <div className="card p-6 text-center space-y-4">
        {!audioBlob && !processing && (
          <>
            <button
              onClick={recording ? stopRecording : startRecording}
              className={cn(
                'w-20 h-20 rounded-full flex items-center justify-center mx-auto transition-all',
                recording
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                  : 'bg-primary-600 hover:bg-primary-700'
              )}
            >
              {recording ? <MicOff size={32} className="text-white" /> : <Mic size={32} className="text-white" />}
            </button>
            <p className="text-sm text-gray-500">
              {recording ? 'Recording... Tap to stop' : 'Tap to record voice note'}
            </p>

            <div className="relative">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
              <div className="relative flex justify-center text-xs"><span className="bg-white px-2 text-gray-400">or</span></div>
            </div>

            <label className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 cursor-pointer">
              <Upload size={16} /> Upload Audio File
              <input type="file" accept="audio/*" onChange={handleFileUpload} className="hidden" />
            </label>
          </>
        )}

        {audioBlob && !processing && !result && (
          <div className="space-y-4">
            {audioUrl && <audio controls src={audioUrl} className="mx-auto" />}
            <div className="flex justify-center gap-3">
              <button onClick={reset} className="btn-secondary">Discard</button>
              <button onClick={processVoice} className="btn-primary">Process Voice Note</button>
            </div>
          </div>
        )}

        {processing && (
          <div className="py-8 space-y-3">
            <Loader2 size={40} className="animate-spin text-primary-600 mx-auto" />
            <p className="text-sm text-gray-500">Processing your voice note with AI...</p>
            <p className="text-xs text-gray-400">This may take 10-30 seconds</p>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <ActionResults
          result={result}
          type="voice"
          userId={user?.id || ''}
          onDone={reset}
        />
      )}
    </div>
  )
}

// ─── OCR Section ──────────────────────────────────────────────
function OCRSection() {
  const { user } = useAuth()
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file')
      return
    }
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const processImage = async () => {
    if (!imageFile || !user) return
    setProcessing(true)
    setResult(null)

    try {
      const ocrInputId = crypto.randomUUID()
      const ext = imageFile.name.split('.').pop() || 'jpg'
      const fileName = `${user.id}/${ocrInputId}.${ext}`

      // 1. Upload to Supabase Storage
      const { error: uploadError } = await supabase.storage
        .from('ocr-images')
        .upload(fileName, imageFile, { contentType: imageFile.type })

      if (uploadError) throw new Error(`Upload failed: ${uploadError.message}`)

      const { data: urlData } = supabase.storage.from('ocr-images').getPublicUrl(fileName)
      const publicUrl = urlData.publicUrl

      // 2. Insert row into ocr_inputs table
      const { error: insertError } = await supabase.from('ocr_inputs').insert({
        id: ocrInputId,
        user_id: user.id,
        image_url: publicUrl,
        image_size_bytes: imageFile.size,
        status: 'pending',
      })

      if (insertError) throw new Error(`DB insert failed: ${insertError.message}`)

      // 3. Call scan endpoint
      await apiClient.post('/ocr/scan', {
        user_id: user.id,
        image_url: publicUrl,
        ocr_input_id: ocrInputId,
        image_size_bytes: imageFile.size,
        image_mime_type: imageFile.type,
        idempotency_key: ocrInputId,
      })

      toast.success('Image submitted! Processing...')

      // 4. Poll for results
      pollStatus(ocrInputId, user.id)
    } catch (err) {
      toast.error(getErrorMessage(err))
      setProcessing(false)
    }
  }

  const pollStatus = useCallback(async (id: string, userId: string) => {
    let attempts = 0
    const maxAttempts = 60

    const poll = async () => {
      try {
        const { data } = await apiClient.get(`/ocr/status/${id}`, { params: { user_id: userId } })
        const status = data.status

        if (status === 'needs_confirmation' || status === 'done' || status === 'failed') {
          setResult(data)
          setProcessing(false)
          if (status === 'failed') {
            toast.error(data.error_message || 'OCR processing failed')
          } else if (status === 'needs_confirmation') {
            toast.success('Text extracted! Please review below.')
          }
          return
        }

        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000)
        } else {
          toast.error('Processing timed out. Please try again.')
          setProcessing(false)
        }
      } catch {
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 3000)
        } else {
          setProcessing(false)
        }
      }
    }

    poll()
  }, [])

  const reset = () => {
    setImageFile(null)
    setImagePreview(null)
    setResult(null)
    setProcessing(false)
  }

  return (
    <div className="space-y-4">
      {/* Upload Controls */}
      <div className="card p-6 text-center space-y-4">
        {!imageFile && !processing && (
          <>
            <p className="text-sm text-gray-500 mb-4">Scan your handwritten diary page to extract leads, tasks, touchpoints, and opportunities</p>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => cameraInputRef.current?.click()}
                className="flex flex-col items-center gap-2 p-6 border-2 border-dashed border-gray-300 rounded-xl hover:border-primary-400 hover:bg-primary-50 transition-colors"
              >
                <Camera size={32} className="text-primary-600" />
                <span className="text-sm font-medium">Take Photo</span>
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center gap-2 p-6 border-2 border-dashed border-gray-300 rounded-xl hover:border-primary-400 hover:bg-primary-50 transition-colors"
              >
                <Upload size={32} className="text-primary-600" />
                <span className="text-sm font-medium">Upload Image</span>
              </button>
            </div>
            <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" onChange={handleImageSelect} className="hidden" />
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageSelect} className="hidden" />
          </>
        )}

        {imageFile && !processing && !result && (
          <div className="space-y-4">
            {imagePreview && (
              <img src={imagePreview} alt="Diary page" className="max-h-64 mx-auto rounded-lg border" />
            )}
            <p className="text-sm text-gray-500">{imageFile.name} ({(imageFile.size / 1024).toFixed(0)} KB)</p>
            <div className="flex justify-center gap-3">
              <button onClick={reset} className="btn-secondary">Discard</button>
              <button onClick={processImage} className="btn-primary">Scan Diary Page</button>
            </div>
          </div>
        )}

        {processing && (
          <div className="py-8 space-y-3">
            <Loader2 size={40} className="animate-spin text-primary-600 mx-auto" />
            <p className="text-sm text-gray-500">Reading your diary page with AI...</p>
            <p className="text-xs text-gray-400">This may take 15-45 seconds for handwritten text</p>
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <ActionResults
          result={result}
          type="ocr"
          userId={user?.id || ''}
          onDone={reset}
        />
      )}
    </div>
  )
}

// ─── Shared Action Results Component ──────────────────────────
function ActionResults({
  result,
  type,
  userId,
  onDone,
}: {
  result: ProcessingResult
  type: 'voice' | 'ocr'
  userId: string
  onDone: () => void
}) {
  const [actionStates, setActionStates] = useState<Record<number, 'pending' | 'confirmed' | 'discarded' | 'loading'>>({})
  const actions = result.parsed_data?.actions || []
  const confirmedActions = result.parsed_data?.confirmed_actions || {}

  // Initialize states from existing confirmed_actions
  useEffect(() => {
    const states: Record<number, 'pending' | 'confirmed' | 'discarded' | 'loading'> = {}
    actions.forEach((_, i) => {
      const existing = confirmedActions[String(i)]
      if (existing === 'discarded') states[i] = 'discarded'
      else if (existing && typeof existing === 'object') states[i] = 'confirmed'
      else states[i] = 'pending'
    })
    setActionStates(states)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleConfirm = async (index: number, confirmed: boolean) => {
    setActionStates(prev => ({ ...prev, [index]: 'loading' }))

    const endpoint = type === 'voice' ? '/voice/confirm' : '/ocr/confirm'
    const idKey = type === 'voice' ? 'voice_input_id' : 'ocr_input_id'

    try {
      await apiClient.post(endpoint, {
        user_id: userId,
        [idKey]: result.id,
        action_index: index,
        confirmed,
        idempotency_key: `${result.id}-${index}-${confirmed ? 'c' : 'd'}`,
      })

      setActionStates(prev => ({
        ...prev,
        [index]: confirmed ? 'confirmed' : 'discarded',
      }))

      toast.success(confirmed ? 'Action confirmed!' : 'Action discarded')
    } catch (err) {
      toast.error(getErrorMessage(err))
      setActionStates(prev => ({ ...prev, [index]: 'pending' }))
    }
  }

  const allResolved = actions.length > 0 && actions.every((_, i) =>
    actionStates[i] === 'confirmed' || actionStates[i] === 'discarded'
  )

  const intentLabels: Record<string, string> = {
    schedule_touchpoint: 'Schedule Touchpoint',
    create_task: 'Create Task',
    create_business_opportunity: 'Business Opportunity',
    add_lead: 'Add Lead',
    unknown: 'Unknown',
  }

  const intentColors: Record<string, string> = {
    schedule_touchpoint: 'bg-blue-100 text-blue-700',
    create_task: 'bg-green-100 text-green-700',
    create_business_opportunity: 'bg-purple-100 text-purple-700',
    add_lead: 'bg-orange-100 text-orange-700',
    unknown: 'bg-gray-100 text-gray-700',
  }

  return (
    <div className="space-y-4">
      {/* Transcript */}
      {result.transcript && (
        <div className="card p-4">
          <h3 className="text-sm font-semibold mb-2 text-gray-600">
            {type === 'voice' ? 'Transcript' : 'Extracted Text'}
          </h3>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.transcript}</p>
        </div>
      )}

      {result.status === 'failed' && (
        <div className="card p-4 bg-red-50 border-red-200">
          <p className="text-sm text-red-700">{result.error_message || 'Processing failed. Please try again.'}</p>
        </div>
      )}

      {/* Actions */}
      {actions.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-600">
            Extracted Actions ({actions.length})
          </h3>

          {actions.map((action, index) => {
            const state = actionStates[index] || 'pending'

            return (
              <div
                key={index}
                className={cn(
                  'card p-4 transition-all',
                  state === 'confirmed' && 'bg-green-50 border-green-200',
                  state === 'discarded' && 'bg-gray-50 opacity-60',
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', intentColors[action.intent] || intentColors.unknown)}>
                        {intentLabels[action.intent] || action.intent}
                      </span>
                      <span className="text-xs text-gray-400">
                        {(action.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <p className="text-sm font-medium">{action.display_summary}</p>

                    {/* Entity details */}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(action.entities).map(([key, val]) => (
                        val && (
                          <span key={key} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {key.replace(/_/g, ' ')}: {String(val)}
                          </span>
                        )
                      ))}
                    </div>

                    {/* Warnings */}
                    {action.warnings.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {action.warnings.map((w, i) => (
                          <p key={i} className="text-xs text-amber-600 flex items-center gap-1">
                            <AlertTriangle size={12} /> {w}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="shrink-0">
                    {state === 'pending' && (
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleConfirm(index, true)}
                          className="p-2 rounded-lg bg-green-100 text-green-700 hover:bg-green-200"
                          title="Confirm"
                        >
                          <Check size={18} />
                        </button>
                        <button
                          onClick={() => handleConfirm(index, false)}
                          className="p-2 rounded-lg bg-red-100 text-red-700 hover:bg-red-200"
                          title="Discard"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    )}
                    {state === 'loading' && <Loader2 size={18} className="animate-spin text-gray-400" />}
                    {state === 'confirmed' && <Check size={18} className="text-green-600" />}
                    {state === 'discarded' && <X size={18} className="text-gray-400" />}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {actions.length === 0 && result.status !== 'failed' && (
        <div className="card p-4 text-center text-sm text-gray-500">
          No actions were extracted. Try again with clearer input.
        </div>
      )}

      {/* Done / New Input */}
      {(allResolved || result.status === 'failed' || actions.length === 0) && (
        <div className="flex justify-center">
          <button onClick={onDone} className="btn-primary">
            {type === 'voice' ? 'Record Another' : 'Scan Another'}
          </button>
        </div>
      )}
    </div>
  )
}
