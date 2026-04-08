import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Bell, LogOut, User } from 'lucide-react'
import { useAuth } from '@/contexts/auth-context'
import { useDebounce } from '@/hooks/useDebounce'
import apiClient from '@/lib/api-client'
import type { SearchResults } from '@/types'

export default function Header() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null)
  const [showResults, setShowResults] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const debouncedQuery = useDebounce(searchQuery, 300)

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    if (query.length < 2) {
      setSearchResults(null)
      setShowResults(false)
      return
    }
    try {
      const { data } = await apiClient.get('/search', { params: { q: query, limit: 20 } })
      setSearchResults(data)
      setShowResults(true)
    } catch {
      // silently fail search
    }
  }

  const handleResultClick = (type: string, id: string) => {
    setShowResults(false)
    setSearchQuery('')
    switch (type) {
      case 'client': navigate(`/clients/${id}`); break
      case 'lead': navigate(`/leads`); break
      case 'task': navigate(`/tasks`); break
      case 'touchpoint': navigate(`/touchpoints`); break
      case 'goal': navigate(`/goals`); break
      default: break
    }
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-30">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <input
          type="text"
          placeholder="Search clients, leads, tasks..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => searchResults && setShowResults(true)}
          onBlur={() => setTimeout(() => setShowResults(false), 200)}
          className="input-field pl-10"
        />
        {showResults && searchResults && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 max-h-96 overflow-y-auto z-50">
            {searchResults.total === 0 ? (
              <p className="p-4 text-sm text-gray-500">No results found</p>
            ) : (
              <>
                {(['clients', 'leads', 'tasks', 'touchpoints', 'goals'] as const).map((key) => {
                  const items = searchResults[key]
                  if (!items?.length) return null
                  return (
                    <div key={key}>
                      <p className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase bg-gray-50">
                        {key}
                      </p>
                      {items.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => handleResultClick(item.entity_type, item.id)}
                          className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2"
                        >
                          <span className="text-sm font-medium">{item.name}</span>
                          {item.subtitle && (
                            <span className="text-xs text-gray-400">{item.subtitle}</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )
                })}
              </>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 ml-4">
        <button
          onClick={() => navigate('/notifications')}
          className="p-2 rounded-lg hover:bg-gray-100 relative"
        >
          <Bell size={20} className="text-gray-600" />
        </button>

        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100"
          >
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <User size={16} className="text-primary-700" />
            </div>
            <span className="text-sm font-medium text-gray-700 hidden sm:block">
              {user?.email?.split('@')[0] || 'User'}
            </span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
              <div className="p-3 border-b border-gray-100">
                <p className="text-sm font-medium">{user?.email}</p>
              </div>
              <button
                onClick={() => { navigate('/profile'); setShowUserMenu(false) }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
              >
                <User size={16} /> Profile
              </button>
              <button
                onClick={() => { signOut(); setShowUserMenu(false) }}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
              >
                <LogOut size={16} /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
