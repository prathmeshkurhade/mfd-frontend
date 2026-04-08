import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserPlus, CheckSquare, Calendar, Briefcase,
  Target, Calculator, Package, User, Bell, Megaphone, FileText,
  Upload, FolderOpen, Clock, Sheet, ChevronLeft, ChevronRight, Mic
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/calendar', icon: Calendar, label: 'Activity Calendar' },
  { to: '/leads', icon: UserPlus, label: 'Leads' },
  { to: '/clients', icon: Users, label: 'Clients' },
  { to: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { to: '/touchpoints', icon: Calendar, label: 'Touchpoints' },
  { to: '/opportunities', icon: Briefcase, label: 'Opportunities' },
  { to: '/goals', icon: Target, label: 'Goals' },
  { to: '/calculators', icon: Calculator, label: 'Calculators' },
  { to: '/products', icon: Package, label: 'Products' },
  { to: '/campaigns', icon: Megaphone, label: 'Campaigns' },
  { to: '/templates', icon: FileText, label: 'Templates' },
  { to: '/data-io', icon: Upload, label: 'Import/Export' },
  { to: '/documents', icon: FolderOpen, label: 'Documents' },
  { to: '/scheduler', icon: Clock, label: 'Scheduler' },
  { to: '/sheets-sync', icon: Sheet, label: 'Sheets Sync' },
  { to: '/voice-ocr', icon: Mic, label: 'Voice & OCR' },
  { to: '/notifications', icon: Bell, label: 'Notifications' },
  { to: '/profile', icon: User, label: 'Profile' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside className={cn(
      'h-screen bg-sidebar text-white flex flex-col transition-all duration-300 sticky top-0',
      collapsed ? 'w-16' : 'w-60'
    )}>
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        {!collapsed && (
          <h1 className="text-lg font-bold text-primary-400">Infinity</h1>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded hover:bg-sidebar-hover text-gray-400"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-2 scrollbar-thin">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => cn(
              'flex items-center gap-3 px-4 py-2.5 mx-2 rounded-lg text-sm transition-colors',
              isActive
                ? 'bg-primary-600/20 text-primary-400 font-medium'
                : 'text-gray-400 hover:bg-sidebar-hover hover:text-white'
            )}
          >
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
