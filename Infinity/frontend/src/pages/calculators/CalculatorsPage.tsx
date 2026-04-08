import { useState } from 'react'
import { TrendingUp, Car, Plane, GraduationCap, Heart, Gem, Armchair, ArrowDownToLine, CreditCard, Wallet, ArrowLeft } from 'lucide-react'
import apiClient from '@/lib/api-client'
import { formatCurrency, getErrorMessage } from '@/lib/utils'
import { CALCULATOR_TYPES } from '@/lib/constants'
import { toast } from 'sonner'

const icons: Record<string, React.ElementType> = {
  TrendingUp, Car, Plane, GraduationCap, Heart, Gem, Armchair, ArrowDownToLine, CreditCard, Wallet,
}

export default function CalculatorsPage() {
  const [selectedCalc, setSelectedCalc] = useState<string | null>(null)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)

  // Generic form state for all calculators
  const [formData, setFormData] = useState<Record<string, unknown>>({})

  const updateField = (key: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCalc) return
    setLoading(true)
    setResult(null)
    try {
      const endpoint = `/calculators/${selectedCalc.replace(/_/g, '-')}`
      // Remove undefined/empty values and mode-irrelevant fields
      const payload = { ...formData }
      if (selectedCalc === 'sip_lumpsum_goal') {
        const mode = payload.mode as string
        if (mode === 'sip') { delete payload.lumpsum_amount; delete payload.target_amount }
        if (mode === 'lumpsum') { delete payload.monthly_sip; delete payload.target_amount }
        if (mode === 'goal_sip') { delete payload.lumpsum_amount }
        if (mode === 'goal_lumpsum') { delete payload.monthly_sip }
      }
      Object.keys(payload).forEach(k => { if (payload[k] === undefined || payload[k] === '') delete payload[k] })
      const { data } = await apiClient.post(endpoint, payload)
      setResult(data.data || data)
      toast.success('Calculation complete')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const selectCalculator = async (calcType: string) => {
    setSelectedCalc(calcType)
    setResult(null)
    // Set defaults based on calculator type
    const defaults: Record<string, Record<string, unknown>> = {
      sip_lumpsum_goal: { mode: 'sip', tenure_years: 15, expected_return: 12, monthly_sip: 10000, inflation_rate: 6, current_savings: 0, step_up_type: 'none', calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      vehicle: { vehicle: { vehicle_type: 'sedan', price: 1000000 }, years_to_purchase: 3, inflation_rate: 5, down_payment_percent: 20, loan_interest_rate: 9.5, loan_tenure_months: 60, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      vacation: { destination_id: 'goa', package_type: 'standard', travelers: 2, years_to_goal: 2, inflation_rate: 6, current_savings: 0, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      education: { children: [{ name: 'Child 1', current_age: 5, goals: [{ name: 'College', goal_age: 18, current_cost: 2000000, accumulated_amount: 0, accumulated_receive_immediately: true }], products: [{ product_code: 'mutual_fund', allocation: 100 }] }], education_inflation: 10, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      wedding: { wedding_type: 'traditional', package_tier: 'standard', years_to_goal: 5, inflation_rate: 6, accumulated_amount: 0, accumulated_receive_immediately: true, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      gold: { purpose: 'jewellery', purity: '22', quantity: 50, unit: 'grams', price_per_gram: 7500, years_to_goal: 4, inflation_rate: 8, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      retirement: { current_age: 35, retirement_age: 60, life_expectancy: 85, current_monthly_expense: 50000, current_investments: [], assumptions: { pre_retirement_inflation: 6, post_retirement_inflation: 6, return_on_kitty: 7, step_up_amount: 2500, step_up_percent: 10 }, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      swp: { principal: 5000000, monthly_withdrawal: 40000, accumulation_years: 5, withdrawal_years: 10, expected_return: 10, fund_type: 'equity', annual_withdrawal_increase: 0, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      prepayment: { loan_amount: 5000000, interest_rate: 8.5, tenure_months: 240, loan_type: 'home', prepayments: [], extra_emis_per_year: 0, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
      cash_surplus: { income: {}, insurance: {}, savings: {}, loans: {}, expenses: {}, current_investments: {}, calculation_mode: 'target_based', products: [{ product_code: 'mutual_fund', allocation: 100 }] },
    }
    setFormData(defaults[calcType] || {})

    // Fetch live gold price when gold calculator is selected
    if (calcType === 'gold') {
      try {
        const { data } = await apiClient.get('/calculators/gold-price')
        const livePrice = data?.prices?.['22k']
        if (livePrice) {
          setFormData(prev => ({ ...prev, price_per_gram: Math.round(livePrice) }))
        }
      } catch { /* use default 7500 */ }
    }
  }

  const renderForm = () => {
    if (!selectedCalc) return null

    const fields: Record<string, Array<{ key: string; label: string; type: string; min?: number; max?: number; step?: number; options?: Array<{ value: string; label: string }> }>> = {
      sip_lumpsum_goal: [
        { key: 'mode', label: 'Mode', type: 'select', options: [{ value: 'sip', label: 'SIP' }, { value: 'lumpsum', label: 'Lumpsum' }, { value: 'goal_sip', label: 'Goal (SIP)' }, { value: 'goal_lumpsum', label: 'Goal (Lumpsum)' }, { value: 'goal_both', label: 'Goal (Both)' }] },
        { key: 'tenure_years', label: 'Tenure (Years)', type: 'number', min: 1, max: 50 },
        { key: 'expected_return', label: 'Expected Return %', type: 'number', min: 1, max: 30, step: 0.5 },
        ...((formData.mode === 'sip' || formData.mode === 'goal_sip' || formData.mode === 'goal_both') ? [{ key: 'monthly_sip', label: 'Monthly SIP', type: 'number', min: 100 }] : []),
        ...((formData.mode === 'lumpsum' || formData.mode === 'goal_lumpsum' || formData.mode === 'goal_both') ? [{ key: 'lumpsum_amount', label: 'Lumpsum Amount', type: 'number', min: 1000 }] : []),
        ...((formData.mode === 'goal_sip' || formData.mode === 'goal_lumpsum' || formData.mode === 'goal_both') ? [{ key: 'target_amount', label: 'Target Amount', type: 'number', min: 1000 }] : []),
        { key: 'inflation_rate', label: 'Inflation %', type: 'number', min: 0, max: 20, step: 0.5 },
        { key: 'current_savings', label: 'Current Savings', type: 'number', min: 0 },
      ],
      vehicle: [
        { key: 'vehicle.price', label: 'Vehicle Price', type: 'number', min: 10000 },
        { key: 'years_to_purchase', label: 'Years to Purchase', type: 'number', min: 1, max: 15 },
        { key: 'inflation_rate', label: 'Inflation %', type: 'number', min: 0, max: 20, step: 0.5 },
        { key: 'down_payment_percent', label: 'Down Payment %', type: 'number', min: 0, max: 100 },
        { key: 'loan_interest_rate', label: 'Loan Interest %', type: 'number', min: 1, max: 25, step: 0.5 },
        { key: 'loan_tenure_months', label: 'Loan Tenure (Months)', type: 'number', min: 12, max: 84 },
      ],
      retirement: [
        { key: 'current_age', label: 'Current Age', type: 'number', min: 18, max: 100 },
        { key: 'retirement_age', label: 'Retirement Age', type: 'number', min: 30, max: 100 },
        { key: 'life_expectancy', label: 'Life Expectancy', type: 'number', min: 50, max: 120 },
        { key: 'current_monthly_expense', label: 'Monthly Expense', type: 'number', min: 0 },
      ],
      swp: [
        { key: 'principal', label: 'Principal', type: 'number', min: 100000 },
        { key: 'monthly_withdrawal', label: 'Monthly Withdrawal', type: 'number', min: 0 },
        { key: 'accumulation_years', label: 'Accumulation Years', type: 'number', min: 0, max: 30 },
        { key: 'withdrawal_years', label: 'Withdrawal Years', type: 'number', min: 1, max: 30 },
        { key: 'expected_return', label: 'Expected Return %', type: 'number', min: 1, max: 20, step: 0.5 },
      ],
      prepayment: [
        { key: 'loan_amount', label: 'Loan Amount', type: 'number', min: 10000 },
        { key: 'interest_rate', label: 'Interest Rate %', type: 'number', min: 1, max: 30, step: 0.1 },
        { key: 'tenure_months', label: 'Tenure (Months)', type: 'number', min: 12, max: 360 },
        { key: 'extra_emis_per_year', label: 'Extra EMIs/Year', type: 'number', min: 0, max: 4 },
      ],
      gold: [
        { key: 'purity', label: 'Purity', type: 'select', options: [{ value: '24', label: '24K' }, { value: '22', label: '22K' }, { value: '18', label: '18K' }] },
        { key: 'quantity', label: 'Quantity', type: 'number', min: 0.1, step: 0.1 },
        { key: 'unit', label: 'Unit', type: 'select', options: [{ value: 'grams', label: 'Grams' }, { value: 'kg', label: 'KG' }] },
        { key: 'price_per_gram', label: 'Price/Gram', type: 'number', min: 1000 },
        { key: 'years_to_goal', label: 'Years', type: 'number', min: 1, max: 30 },
        { key: 'inflation_rate', label: 'Inflation %', type: 'number', min: 0, max: 20, step: 0.5 },
      ],
      vacation: [
        { key: 'destination_id', label: 'Destination', type: 'text' },
        { key: 'package_type', label: 'Package', type: 'select', options: [{ value: 'standard', label: 'Standard' }, { value: 'premium', label: 'Premium' }, { value: 'business', label: 'Business' }] },
        { key: 'travelers', label: 'Travelers', type: 'number', min: 1, max: 20 },
        { key: 'years_to_goal', label: 'Years', type: 'number', min: 1, max: 15 },
        { key: 'inflation_rate', label: 'Inflation %', type: 'number', min: 0, max: 20, step: 0.5 },
      ],
      wedding: [
        { key: 'wedding_type', label: 'Type', type: 'select', options: [{ value: 'intimate', label: 'Intimate' }, { value: 'simple', label: 'Simple' }, { value: 'traditional', label: 'Traditional' }, { value: 'destination', label: 'Destination' }, { value: 'grand', label: 'Grand' }] },
        { key: 'package_tier', label: 'Package', type: 'select', options: [{ value: 'standard', label: 'Standard' }, { value: 'premium', label: 'Premium' }] },
        { key: 'custom_cost', label: 'Custom Cost', type: 'number', min: 0 },
        { key: 'years_to_goal', label: 'Years', type: 'number', min: 1, max: 15 },
        { key: 'inflation_rate', label: 'Inflation %', type: 'number', min: 0, max: 20, step: 0.5 },
      ],
      education: [
        { key: 'education_inflation', label: 'Education Inflation %', type: 'number', min: 0, max: 20, step: 0.5 },
      ],
      cash_surplus: [],
    }

    const calcFields = fields[selectedCalc] || []

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {calcFields.map((field) => (
            <div key={field.key}>
              <label className="block text-sm font-medium mb-1">{field.label}</label>
              {field.type === 'select' ? (
                <select
                  value={getNestedValue(formData, field.key) as string || ''}
                  onChange={(e) => setNestedValue(field.key, e.target.value)}
                  className="input-field"
                >
                  {field.options?.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              ) : field.type === 'text' ? (
                <input type="text" value={getNestedValue(formData, field.key) as string || ''} onChange={(e) => setNestedValue(field.key, e.target.value)} className="input-field" />
              ) : (
                <input
                  type="number"
                  value={getNestedValue(formData, field.key) as number || ''}
                  onChange={(e) => setNestedValue(field.key, e.target.value ? Number(e.target.value) : undefined)}
                  className="input-field"
                  min={field.min} max={field.max} step={field.step || 1}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex gap-3">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Calculating...' : 'Calculate'}
          </button>
          <button type="button" onClick={() => { setSelectedCalc(null); setResult(null) }} className="btn-secondary">Back</button>
        </div>
      </form>
    )
  }

  const getNestedValue = (obj: Record<string, unknown>, path: string): unknown => {
    return path.split('.').reduce((o: unknown, k) => (o as Record<string, unknown>)?.[k], obj)
  }

  const setNestedValue = (path: string, value: unknown) => {
    const keys = path.split('.')
    if (keys.length === 1) { updateField(keys[0], value); return }
    setFormData((prev) => {
      const newData = { ...prev }
      let curr: Record<string, unknown> = newData
      for (let i = 0; i < keys.length - 1; i++) {
        curr[keys[i]] = { ...(curr[keys[i]] as Record<string, unknown> || {}) }
        curr = curr[keys[i]] as Record<string, unknown>
      }
      curr[keys[keys.length - 1]] = value
      return newData
    })
  }

  const renderResult = () => {
    if (!result) return null
    return (
      <div className="card p-6 mt-4">
        <h3 className="text-lg font-semibold mb-4">Results</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(result).filter(([k, v]) => typeof v === 'number' && !k.includes('type') && !k.includes('mode')).map(([key, value]) => (
            <div key={key} className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
              <p className="text-lg font-bold">{typeof value === 'number' && value > 100 ? formatCurrency(value) : String(value)}</p>
            </div>
          ))}
        </div>
        {/* Show full JSON for debugging */}
        <details className="mt-4">
          <summary className="text-sm text-gray-500 cursor-pointer">Raw Response</summary>
          <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
        </details>
      </div>
    )
  }

  if (!selectedCalc) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Financial Calculators</h1>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {CALCULATOR_TYPES.map((calc) => {
            const Icon = icons[calc.icon] || TrendingUp
            return (
              <button
                key={calc.value}
                onClick={() => selectCalculator(calc.value)}
                className="card p-6 text-center hover:shadow-md hover:border-primary-300 transition-all group"
              >
                <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center mx-auto mb-3 group-hover:bg-primary-100 transition-colors">
                  <Icon size={24} className="text-primary-600" />
                </div>
                <p className="font-medium text-sm">{calc.label}</p>
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  const calcLabel = CALCULATOR_TYPES.find((c) => c.value === selectedCalc)?.label || selectedCalc

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => { setSelectedCalc(null); setResult(null) }} className="p-2 rounded-lg hover:bg-gray-100">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold">{calcLabel} Calculator</h1>
      </div>
      <div className="card p-6">{renderForm()}</div>
      {renderResult()}
    </div>
  )
}
