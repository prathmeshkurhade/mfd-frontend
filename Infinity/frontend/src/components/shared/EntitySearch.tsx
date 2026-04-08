import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { useDebounce } from '@/hooks/useDebounce'
import apiClient from '@/lib/api-client'

interface EntitySearchProps {
  entityType: 'clients' | 'leads'
  value: string | null
  onChange: (id: string | null, name: string | null) => void
  placeholder?: string
  selectedName?: string | null
}

export default function EntitySearch({ entityType, value, onChange, placeholder, selectedName }: EntitySearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Array<{ id: string; name: string; phone?: string }>>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [displayValue, setDisplayValue] = useState(selectedName || '')
  const debouncedQuery = useDebounce(query, 300)

  useEffect(() => {
    if (selectedName) setDisplayValue(selectedName)
  }, [selectedName])

  useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([])
      return
    }
    apiClient.get(`/search/${entityType}`, { params: { q: debouncedQuery, limit: 10 } })
      .then(({ data }) => setResults(data))
      .catch(() => setResults([]))
  }, [debouncedQuery, entityType])

  const handleSelect = (item: { id: string; name: string }) => {
    onChange(item.id, item.name)
    setDisplayValue(item.name)
    setQuery('')
    setShowDropdown(false)
  }

  const handleClear = () => {
    onChange(null, null)
    setDisplayValue('')
    setQuery('')
  }

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
        <input
          type="text"
          value={showDropdown ? query : displayValue}
          onChange={(e) => { setQuery(e.target.value); setShowDropdown(true) }}
          onFocus={() => setShowDropdown(true)}
          onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
          placeholder={placeholder || `Search ${entityType}...`}
          className="input-field pl-9 pr-8"
        />
        {value && (
          <button onClick={handleClear} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-sm">
            x
          </button>
        )}
      </div>
      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {results.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSelect(item)}
              className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm"
            >
              <span className="font-medium">{item.name}</span>
              {item.phone && <span className="text-gray-400 ml-2">{item.phone}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
