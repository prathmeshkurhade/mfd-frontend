import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/contexts/auth-context'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import AppLayout from '@/components/layout/AppLayout'

// Pages
import LoginPage from '@/pages/login/LoginPage'
import SignupPage from '@/pages/signup/SignupPage'
import DashboardPage from '@/pages/dashboard/DashboardPage'
import LeadsPage from '@/pages/leads/LeadsPage'
import ClientsPage from '@/pages/clients/ClientsPage'
import ClientOverviewPage from '@/pages/clients/ClientOverviewPage'
import TasksPage from '@/pages/tasks/TasksPage'
import TouchpointsPage from '@/pages/touchpoints/TouchpointsPage'
import OpportunitiesPage from '@/pages/opportunities/OpportunitiesPage'
import GoalsPage from '@/pages/goals/GoalsPage'
import CalculatorsPage from '@/pages/calculators/CalculatorsPage'
import ProductsPage from '@/pages/products/ProductsPage'
import ProfilePage from '@/pages/profile/ProfilePage'
import NotificationsPage from '@/pages/notifications/NotificationsPage'
import CampaignsPage from '@/pages/campaigns/CampaignsPage'
import TemplatesPage from '@/pages/templates/TemplatesPage'
import DataIOPage from '@/pages/data-io/DataIOPage'
import DocumentsPage from '@/pages/documents/DocumentsPage'
import SchedulerPage from '@/pages/scheduler/SchedulerPage'
import SheetsSyncPage from '@/pages/sheets-sync/SheetsSyncPage'
import VoiceOCRPage from '@/pages/voice-ocr/VoiceOCRPage'
import CalendarPage from '@/pages/calendar/CalendarPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* Protected routes */}
            <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
              <Route index element={<DashboardPage />} />
              <Route path="leads" element={<LeadsPage />} />
              <Route path="clients" element={<ClientsPage />} />
              <Route path="clients/:id" element={<ClientOverviewPage />} />
              <Route path="tasks" element={<TasksPage />} />
              <Route path="touchpoints" element={<TouchpointsPage />} />
              <Route path="opportunities" element={<OpportunitiesPage />} />
              <Route path="goals" element={<GoalsPage />} />
              <Route path="calculators" element={<CalculatorsPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="campaigns" element={<CampaignsPage />} />
              <Route path="templates" element={<TemplatesPage />} />
              <Route path="data-io" element={<DataIOPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="scheduler" element={<SchedulerPage />} />
              <Route path="sheets-sync" element={<SheetsSyncPage />} />
              <Route path="voice-ocr" element={<VoiceOCRPage />} />
              <Route path="calendar" element={<CalendarPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </QueryClientProvider>
  )
}
