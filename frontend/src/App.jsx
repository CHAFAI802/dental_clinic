import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Footer from './components/Footer.jsx'
import NavBar from './components/NavBar.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import ProtectedRoute from './routes/ProtectedRoute.jsx'

import AppShell from './pages/AppShell.jsx'
import Contact from './pages/Contact.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import NotFound from './pages/NotFound.jsx'
import Profile from './pages/Profile.jsx'
import Services from './pages/Services.jsx'
import Team from './pages/Team.jsx'

import AuditLogsPage from './pages/dashboard/AuditLogsPage.jsx'
import DashboardHome from './pages/dashboard/DashboardHome.jsx'
import ModulePage from './pages/dashboard/ModulePage.jsx'
import UserCreatePage from './pages/dashboard/users/UserCreatePage.jsx'
import UserEditPage from './pages/dashboard/users/UserEditPage.jsx'
import UsersListPage from './pages/dashboard/users/UsersListPage.jsx'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app-layout">
          <NavBar />
          <main className="app-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/services" element={<Services />} />
              <Route path="/team" element={<Team />} />
              <Route path="/team/profile" element={<Profile />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/login" element={<Login />} />

              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<Dashboard />}>
                  <Route index element={<DashboardHome />} />
                  <Route path="users" element={<UsersListPage />} />
                  <Route path="users/new" element={<UserCreatePage />} />
                  <Route path="users/:userId" element={<UserEditPage />} />
                  <Route path="audit-logs" element={<AuditLogsPage />} />
                  <Route path="modules/:moduleId" element={<ModulePage />} />
                </Route>
              </Route>

              <Route path="/app/*" element={<AppShell />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
