import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon,
  CheckSquare, Phone, UserPlus, Briefcase, MapPin, Clock
} from 'lucide-react'
import {
  format, addDays, subDays, addWeeks, subWeeks, addMonths, subMonths,
  startOfWeek, endOfWeek, startOfMonth, endOfMonth, eachDayOfInterval,
  isSameDay, isSameMonth, isToday, parseISO
} from 'date-fns'
import apiClient from '@/lib/api-client'
import { cn } from '@/lib/utils'
import LoadingSpinner from '@/components/shared/LoadingSpinner'
import { toast } from 'sonner'

interface CalendarEvent {
  id: string
  title: string
  date: string
  time: string | null
  type: 'task' | 'touchpoint' | 'lead' | 'opportunity'
  status: string
  priority?: string
  all_day?: boolean
  client_name?: string | null
  lead_name?: string | null
  location?: string | null
  agenda?: string | null
  interaction_type?: string | null
  expected_amount?: number | null
}

type ViewMode = 'week' | 'month'

const EVENT_COLORS: Record<string, { bg: string; border: string; dot: string; text: string }> = {
  task: { bg: 'bg-blue-50', border: 'border-blue-300', dot: 'bg-blue-500', text: 'text-blue-800' },
  touchpoint: { bg: 'bg-red-50', border: 'border-red-300', dot: 'bg-red-500', text: 'text-red-800' },
  lead: { bg: 'bg-indigo-50', border: 'border-indigo-300', dot: 'bg-indigo-500', text: 'text-indigo-800' },
  opportunity: { bg: 'bg-green-50', border: 'border-green-300', dot: 'bg-green-500', text: 'text-green-800' },
}

const EVENT_ICONS: Record<string, typeof CheckSquare> = {
  task: CheckSquare,
  touchpoint: Phone,
  lead: UserPlus,
  opportunity: Briefcase,
}

const HOURS = Array.from({ length: 14 }, (_, i) => i + 8) // 8 AM to 9 PM

function parseTime(time: string | null): number | null {
  if (!time) return null
  const parts = time.split(':')
  return parseInt(parts[0], 10) + parseInt(parts[1] || '0', 10) / 60
}

function formatTimeShort(time: string | null): string {
  if (!time) return ''
  const [h, m] = time.split(':')
  const hour = parseInt(h, 10)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour
  return `${displayHour}:${m} ${ampm}`
}

export default function CalendarPage() {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<ViewMode>('week')
  const [currentDate, setCurrentDate] = useState(new Date())
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)
  const [filters, setFilters] = useState({
    task: true,
    touchpoint: true,
    lead: true,
    opportunity: true,
  })

  const dateRange = useMemo(() => {
    if (viewMode === 'week') {
      const start = startOfWeek(currentDate, { weekStartsOn: 0 })
      const end = endOfWeek(currentDate, { weekStartsOn: 0 })
      return { start, end, days: eachDayOfInterval({ start, end }) }
    } else {
      const monthStart = startOfMonth(currentDate)
      const monthEnd = endOfMonth(currentDate)
      const start = startOfWeek(monthStart, { weekStartsOn: 0 })
      const end = endOfWeek(monthEnd, { weekStartsOn: 0 })
      return { start, end, days: eachDayOfInterval({ start, end }) }
    }
  }, [currentDate, viewMode])

  useEffect(() => {
    loadEvents()
  }, [dateRange])

  const loadEvents = async () => {
    try {
      setLoading(true)
      const { data } = await apiClient.get('/dashboard/calendar-events', {
        params: {
          date_from: format(dateRange.start, 'yyyy-MM-dd'),
          date_to: format(dateRange.end, 'yyyy-MM-dd'),
        },
      })
      setEvents(data)
    } catch {
      toast.error('Failed to load calendar events')
    } finally {
      setLoading(false)
    }
  }

  const filteredEvents = useMemo(() => {
    return events.filter((e) => filters[e.type])
  }, [events, filters])

  const getEventsForDay = (day: Date) => {
    const dayStr = format(day, 'yyyy-MM-dd')
    return filteredEvents.filter((e) => e.date === dayStr)
  }

  const getEventsForHour = (day: Date, hour: number) => {
    const dayEvents = getEventsForDay(day)
    return dayEvents.filter((e) => {
      const t = parseTime(e.time)
      if (t === null) return false
      return Math.floor(t) === hour
    })
  }

  const getAllDayEvents = (day: Date) => {
    const dayEvents = getEventsForDay(day)
    return dayEvents.filter((e) => !e.time || e.all_day)
  }

  const navigateDate = (direction: 'prev' | 'next') => {
    if (viewMode === 'week') {
      setCurrentDate(direction === 'next' ? addWeeks(currentDate, 1) : subWeeks(currentDate, 1))
    } else {
      setCurrentDate(direction === 'next' ? addMonths(currentDate, 1) : subMonths(currentDate, 1))
    }
  }

  const goToToday = () => setCurrentDate(new Date())

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(selectedEvent?.id === event.id ? null : event)
  }

  const navigateToEntity = (event: CalendarEvent) => {
    switch (event.type) {
      case 'task': navigate('/tasks'); break
      case 'touchpoint': navigate('/touchpoints'); break
      case 'lead': navigate('/leads'); break
      case 'opportunity': navigate('/opportunities'); break
    }
  }

  const headerText = viewMode === 'week'
    ? `${format(dateRange.start, 'MMM d')} - ${format(dateRange.end, 'MMM d, yyyy')}`
    : format(currentDate, 'MMMM yyyy')

  if (loading && events.length === 0) return <LoadingSpinner />

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Activity Calendar</h1>
        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('week')}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                viewMode === 'week' ? 'bg-white shadow text-primary-700' : 'text-gray-600 hover:text-gray-900'
              )}
            >
              Week
            </button>
            <button
              onClick={() => setViewMode('month')}
              className={cn(
                'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                viewMode === 'month' ? 'bg-white shadow text-primary-700' : 'text-gray-600 hover:text-gray-900'
              )}
            >
              Month
            </button>
          </div>
        </div>
      </div>

      {/* Navigation bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={goToToday}
            className="px-3 py-1.5 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Today
          </button>
          <div className="flex items-center gap-1">
            <button onClick={() => navigateDate('prev')} className="p-1.5 hover:bg-gray-100 rounded-lg">
              <ChevronLeft size={18} />
            </button>
            <button onClick={() => navigateDate('next')} className="p-1.5 hover:bg-gray-100 rounded-lg">
              <ChevronRight size={18} />
            </button>
          </div>
          <h2 className="text-lg font-semibold">{headerText}</h2>
        </div>

        {/* Legend / Filters */}
        <div className="flex items-center gap-3">
          {Object.entries(EVENT_COLORS).map(([type, colors]) => {
            const Icon = EVENT_ICONS[type]
            return (
              <button
                key={type}
                onClick={() => setFilters((f) => ({ ...f, [type]: !f[type as keyof typeof f] }))}
                className={cn(
                  'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-all',
                  filters[type as keyof typeof filters]
                    ? `${colors.bg} ${colors.text} border ${colors.border}`
                    : 'bg-gray-100 text-gray-400 border border-gray-200 line-through'
                )}
              >
                <span className={cn('w-2.5 h-2.5 rounded-full', filters[type as keyof typeof filters] ? colors.dot : 'bg-gray-300')} />
                {type.charAt(0).toUpperCase() + type.slice(1)}s
              </button>
            )
          })}
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="card flex-1 overflow-hidden flex flex-col">
        {viewMode === 'week' ? (
          <WeekView
            days={dateRange.days}
            getEventsForHour={getEventsForHour}
            getAllDayEvents={getAllDayEvents}
            onEventClick={handleEventClick}
            selectedEvent={selectedEvent}
          />
        ) : (
          <MonthView
            days={dateRange.days}
            currentDate={currentDate}
            getEventsForDay={getEventsForDay}
            onEventClick={handleEventClick}
            selectedEvent={selectedEvent}
            onDayClick={(day) => { setCurrentDate(day); setViewMode('week') }}
          />
        )}
      </div>

      {/* Event detail popup */}
      {selectedEvent && (
        <EventDetail
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onNavigate={() => navigateToEntity(selectedEvent)}
        />
      )}
    </div>
  )
}

// ─── Week View ───────────────────────────────────────────────
function WeekView({
  days,
  getEventsForHour,
  getAllDayEvents,
  onEventClick,
  selectedEvent,
}: {
  days: Date[]
  getEventsForHour: (day: Date, hour: number) => CalendarEvent[]
  getAllDayEvents: (day: Date) => CalendarEvent[]
  onEventClick: (e: CalendarEvent) => void
  selectedEvent: CalendarEvent | null
}) {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Day headers */}
      <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-gray-200">
        <div className="p-2" />
        {days.map((day) => (
          <div
            key={day.toISOString()}
            className={cn(
              'p-2 text-center border-l border-gray-200',
              isToday(day) && 'bg-primary-50'
            )}
          >
            <div className="text-xs font-medium text-gray-500 uppercase">{format(day, 'EEE')}</div>
            <div className={cn(
              'text-lg font-bold mt-0.5 inline-flex items-center justify-center w-8 h-8 rounded-full',
              isToday(day) ? 'bg-primary-600 text-white' : 'text-gray-900'
            )}>
              {format(day, 'd')}
            </div>
          </div>
        ))}
      </div>

      {/* All-day events row */}
      <div className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-gray-200 min-h-[32px]">
        <div className="p-1 text-[10px] text-gray-400 flex items-center justify-end pr-2">ALL DAY</div>
        {days.map((day) => {
          const dayEvents = getAllDayEvents(day)
          return (
            <div key={day.toISOString()} className="border-l border-gray-200 p-0.5 flex flex-col gap-0.5">
              {dayEvents.slice(0, 3).map((event) => (
                <EventChip key={event.id} event={event} onClick={() => onEventClick(event)} selected={selectedEvent?.id === event.id} compact />
              ))}
              {dayEvents.length > 3 && (
                <span className="text-[10px] text-gray-500 pl-1">+{dayEvents.length - 3} more</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Time grid */}
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-[60px_repeat(7,1fr)]">
          {HOURS.map((hour) => (
            <div key={hour} className="contents">
              <div className="h-16 flex items-start justify-end pr-2 pt-0 text-xs text-gray-400 border-b border-gray-100">
                {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
              </div>
              {days.map((day) => {
                const hourEvents = getEventsForHour(day, hour)
                return (
                  <div
                    key={`${day.toISOString()}-${hour}`}
                    className={cn(
                      'h-16 border-l border-b border-gray-100 p-0.5 relative',
                      isToday(day) && 'bg-primary-50/30'
                    )}
                  >
                    {hourEvents.map((event) => (
                      <EventChip key={event.id} event={event} onClick={() => onEventClick(event)} selected={selectedEvent?.id === event.id} />
                    ))}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Month View ──────────────────────────────────────────────
function MonthView({
  days,
  currentDate,
  getEventsForDay,
  onEventClick,
  selectedEvent,
  onDayClick,
}: {
  days: Date[]
  currentDate: Date
  getEventsForDay: (day: Date) => CalendarEvent[]
  onEventClick: (e: CalendarEvent) => void
  selectedEvent: CalendarEvent | null
  onDayClick: (day: Date) => void
}) {
  const weeks: Date[][] = []
  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7))
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 border-b border-gray-200">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
          <div key={d} className="p-2 text-xs font-semibold text-gray-500 text-center uppercase">
            {d}
          </div>
        ))}
      </div>

      {/* Weeks */}
      <div className="flex-1 grid" style={{ gridTemplateRows: `repeat(${weeks.length}, 1fr)` }}>
        {weeks.map((week, wi) => (
          <div key={wi} className="grid grid-cols-7 border-b border-gray-200">
            {week.map((day) => {
              const dayEvents = getEventsForDay(day)
              const inMonth = isSameMonth(day, currentDate)
              return (
                <div
                  key={day.toISOString()}
                  className={cn(
                    'border-l border-gray-100 p-1 min-h-[100px] cursor-pointer hover:bg-gray-50 transition-colors',
                    !inMonth && 'bg-gray-50/50',
                    isToday(day) && 'bg-primary-50/50'
                  )}
                  onClick={() => onDayClick(day)}
                >
                  <div className={cn(
                    'text-sm font-medium mb-1 inline-flex items-center justify-center w-6 h-6 rounded-full',
                    isToday(day) ? 'bg-primary-600 text-white' : inMonth ? 'text-gray-900' : 'text-gray-400'
                  )}>
                    {format(day, 'd')}
                  </div>
                  <div className="space-y-0.5">
                    {dayEvents.slice(0, 4).map((event) => (
                      <EventChip
                        key={event.id}
                        event={event}
                        onClick={(e) => { e.stopPropagation(); onEventClick(event) }}
                        selected={selectedEvent?.id === event.id}
                        compact
                      />
                    ))}
                    {dayEvents.length > 4 && (
                      <div className="text-[10px] text-gray-500 pl-1 font-medium">+{dayEvents.length - 4} more</div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Event Chip ──────────────────────────────────────────────
function EventChip({
  event,
  onClick,
  selected,
  compact,
}: {
  event: CalendarEvent
  onClick: (e: React.MouseEvent) => void
  selected: boolean
  compact?: boolean
}) {
  const colors = EVENT_COLORS[event.type] || EVENT_COLORS.task

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left rounded px-1.5 py-0.5 text-[11px] font-medium truncate border transition-all',
        colors.bg, colors.border, colors.text,
        selected && 'ring-2 ring-primary-500 ring-offset-1',
        'hover:opacity-80'
      )}
    >
      <span className={cn('inline-block w-1.5 h-1.5 rounded-full mr-1', colors.dot)} />
      {!compact && event.time && <span className="font-normal">{formatTimeShort(event.time)} </span>}
      {event.title}
    </button>
  )
}

// ─── Event Detail Panel ──────────────────────────────────────
function EventDetail({
  event,
  onClose,
  onNavigate,
}: {
  event: CalendarEvent
  onClose: () => void
  onNavigate: () => void
}) {
  const colors = EVENT_COLORS[event.type] || EVENT_COLORS.task
  const Icon = EVENT_ICONS[event.type] || CalendarIcon

  return (
    <div className="fixed bottom-4 right-4 w-80 card shadow-xl border border-gray-200 z-50">
      <div className={cn('p-3 rounded-t-lg border-b flex items-center justify-between', colors.bg)}>
        <div className="flex items-center gap-2">
          <Icon size={16} className={colors.text} />
          <span className={cn('text-xs font-semibold uppercase', colors.text)}>
            {event.type}
          </span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">&times;</button>
      </div>
      <div className="p-3 space-y-2">
        <h3 className="font-semibold text-sm">{event.title}</h3>

        <div className="flex items-center gap-2 text-xs text-gray-600">
          <CalendarIcon size={13} />
          {format(parseISO(event.date), 'EEE, MMM d, yyyy')}
          {event.time && (
            <>
              <Clock size={13} className="ml-1" />
              {formatTimeShort(event.time)}
            </>
          )}
        </div>

        {event.location && (
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <MapPin size={13} />
            {event.location}
          </div>
        )}

        {event.agenda && (
          <p className="text-xs text-gray-600 bg-gray-50 rounded p-2">{event.agenda}</p>
        )}

        {(event.client_name || event.lead_name) && (
          <div className="text-xs text-gray-500">
            {event.client_name && <span>Client: <strong>{event.client_name}</strong></span>}
            {event.lead_name && <span>Lead: <strong>{event.lead_name}</strong></span>}
          </div>
        )}

        <div className="flex items-center justify-between pt-1">
          <span className={cn(
            'text-[10px] font-medium px-2 py-0.5 rounded-full',
            event.status === 'completed' ? 'bg-green-100 text-green-700' :
            event.status === 'pending' || event.status === 'scheduled' ? 'bg-yellow-100 text-yellow-700' :
            'bg-gray-100 text-gray-600'
          )}>
            {event.status.replace(/_/g, ' ').toUpperCase()}
          </span>
          <button onClick={onNavigate} className="text-xs text-primary-600 hover:underline font-medium">
            View in {event.type}s &rarr;
          </button>
        </div>
      </div>
    </div>
  )
}
