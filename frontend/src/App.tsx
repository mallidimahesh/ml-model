import React from 'react'
import { AppProvider, useApp } from './context/AppContext'
import { Navbar } from './components/layout/Navbar'
import { Sidebar } from './components/layout/Sidebar'
import { GlobalOverviewView } from './components/views/GlobalOverviewView'
import { CountryExplorerView } from './components/views/CountryExplorerView'
import { DerivedIndicatorsView } from './components/views/DerivedIndicatorsView'
import { InflationForecastView } from './components/views/InflationForecastView'
import { PolicySimulatorView } from './components/views/PolicySimulatorView'

const MainContent: React.FC = () => {
  const { activeTab } = useApp()

  return (
    <main className="flex-1 overflow-y-auto bg-[#090e10] text-slate-100 min-h-[calc(100vh-4rem)]">
      {activeTab === 'global' && <GlobalOverviewView />}
      {activeTab === 'country' && <CountryExplorerView />}
      {activeTab === 'derived' && <DerivedIndicatorsView />}
      {activeTab === 'forecast' && <InflationForecastView />}
      {activeTab === 'simulator' && <PolicySimulatorView />}
    </main>
  )
}

export function App() {
  return (
    <AppProvider>
      <div className="min-h-screen bg-[#090e10] text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-white">
        <Navbar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <MainContent />
        </div>
      </div>
    </AppProvider>
  )
}

export default App
