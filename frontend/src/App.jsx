import { BrowserRouter, Navigate, Outlet, Routes, Route } from 'react-router-dom'

import Footer from './components/Footer.jsx'
import NavBar from './components/NavBar.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import { SiteConfigProvider } from './context/SiteConfigContext.jsx'
import ProtectedRoute from './routes/ProtectedRoute.jsx'

import AppShell from './pages/AppShell.jsx'
import Contact from './pages/Contact.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import NotFound from './pages/NotFound.jsx'
import Profile from './pages/Profile.jsx'
import Services from './pages/Services.jsx'
import SiteSettings from './pages/SiteSettings.jsx'
import Team from './pages/Team.jsx'

import AuditLogsPage from './pages/dashboard/AuditLogsPage.jsx'
import BillingPage from './pages/dashboard/billing/BillingPage.jsx'
import DashboardHome from './pages/dashboard/DashboardHome.jsx'
import ModulePage from './pages/dashboard/ModulePage.jsx'
import PrestationCategoriesPage from './pages/dashboard/billing/PrestationCategoriesPage.jsx'
import PrestationTarifsPage from './pages/dashboard/billing/PrestationTarifsPage.jsx'
import PrestationsPage from './pages/dashboard/billing/PrestationsPage.jsx'
import SettingsOverview from './pages/dashboard/settings/SettingsOverview.jsx'
import SettingsPage from './pages/dashboard/settings/SettingsPage.jsx'
import UserCreatePage from './pages/dashboard/users/UserCreatePage.jsx'
import UserEditPage from './pages/dashboard/users/UserEditPage.jsx'
import UsersListPage from './pages/dashboard/users/UsersListPage.jsx'
import WorkingHoursPage from './pages/dashboard/working-hours/WorkingHoursPage.jsx'

function SiteSettingsAdminRoute() {
  const { user } = useAuth()
  const canManageSite = ['super_admin', 'administrator'].includes(user?.role)

  return canManageSite ? <Outlet /> : <Navigate to="/dashboard" replace />
}

function App() {
  return (
    <BrowserRouter>
      <SiteConfigProvider>
        <AuthProvider>
          <div className="app-layout">
            <NavBar />
            <main className="app-content">
              <Routes>
                {/* --- Site public --- */}
                <Route path="/" element={<Home />} />
                <Route path="/services" element={<Services />} />
                <Route path="/team" element={<Team />} />
                <Route path="/team/profile" element={<Profile />} />
                <Route path="/contact" element={<Contact />} />
                <Route path="/login" element={<Login />} />

                {/* --- Espace connecté (existant, protégé) --- */}
                <Route element={<ProtectedRoute />}>
                  <Route path="/dashboard" element={<Dashboard />}>
                    <Route index element={<DashboardHome />} />
                    <Route path="users" element={<UsersListPage />} />
                    <Route path="users/new" element={<UserCreatePage />} />
                    <Route path="users/:userId" element={<UserEditPage />} />
                    <Route path="audit-logs" element={<AuditLogsPage />} />
                    <Route path="working-hours" element={<WorkingHoursPage />} />
                    <Route path="modules/:moduleId" element={<ModulePage />} />

                    {/* --- Paramétrage (frontend uniquement, rôles admin) --- */}
                    <Route path="settings" element={<SettingsPage />}>
                      <Route index element={<SettingsOverview />} />
                      <Route path="prestation-categories" element={<PrestationCategoriesPage />} />
                      <Route path="prestations" element={<PrestationsPage />} />
                      <Route path="prestation-tarifs" element={<PrestationTarifsPage />} />
                    </Route>

                    {/* --- Module Billing (factures, paiements, catalogue) --- */}
                    <Route
                      path="billing"
                      element={<Navigate to="/dashboard/billing/invoices" replace />}
                    />
                    <Route path="billing/:section" element={<BillingPage />} />
                  </Route>

                  <Route element={<SiteSettingsAdminRoute />}>
                    <Route path="/settings/site" element={<SiteSettings />} />
                    <Route path="/site-settings" element={<SiteSettings />} />
                  </Route>
                </Route>

                <Route path="/app/*" element={<AppShell />} />

                <Route path="*" element={<NotFound />} />
              </Routes>
            </main>
            <Footer />
          </div>
        </AuthProvider>
      </SiteConfigProvider>
    </BrowserRouter>
  )
}

export default App
