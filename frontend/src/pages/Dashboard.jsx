import { Outlet } from 'react-router-dom'

import DashboardHeader from '../components/dashboard/DashboardHeader.jsx'
import DashboardSidebar from '../components/dashboard/DashboardSidebar.jsx'
import { useAuth } from '../context/AuthContext.jsx'

function Dashboard() {
  const { accessibleModules } = useAuth()

  return (
    <section className="dashboard-shell">
      <DashboardHeader />

      <div className="dashboard-layout">
        <DashboardSidebar modules={accessibleModules} />
        <div className="dashboard-main">
          <Outlet />
        </div>
      </div>
    </section>
  )
}

export default Dashboard
