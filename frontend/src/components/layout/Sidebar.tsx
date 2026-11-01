import React from 'react'
import {
  Globe2,
  Compass,
  Calculator,
  TrendingUp,
  Sliders,
} from 'lucide-react'
import { useApp, type NavTab } from '../../context/AppContext'

interface NavItem {
  id: NavTab
  label: string
  icon: React.ElementType
  badge?: string
  description: string
}

const navItems: NavItem[] = [
  {
    id: 'global',
    label: 'Global Overview',
    icon: Globe2,
    badge: '1W WLD',
    description: 'Worldwide macroeconomic KPIs & comparisons',
  },
  {
    id: 'country',
    label: 'Country Explorer',
    icon: Compass,
    description: 'In-depth economic profile & time series',
  },
  {
    id: 'derived',
    label: 'Derived Indicators',
    icon: Calculator,
    badge: 'Misery & Real Rate',
    description: 'Dynamic calculations for selected nation',
  },
  {
    id: 'forecast',
    label: 'Inflation Forecast',
    icon: TrendingUp,
    badge: 'Ridge ML',
    description: 'Phillips Curve + L2 Ridge next-quarter prediction',
  },
  {
    id: 'simulator',
    label: 'Policy Simulator',
    icon: Sliders,
    badge: 'Multiplier & IS-LM',
    description: 'Interactive Keynesian & IS-LM policy scenarios',
  },
]

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, isSidebarCollapsed } = useApp()

  return (
    <aside
      className={`relative flex flex-col border-r border-[#1b2f34] bg-[#0a1114] transition-all duration-300 z-20 ${
        isSidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Navigation Menu */}
      <div className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full group relative flex items-center rounded-xl px-3 py-3 text-xs font-medium transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-teal-950/90 to-teal-900/40 text-teal-300 border border-teal-600/40 shadow-sm'
                  : 'text-slate-400 hover:bg-[#111e21] hover:text-slate-200 border border-transparent'
              }`}
              title={isSidebarCollapsed ? item.label : undefined}
            >
              <div
                className={`flex items-center justify-center rounded-lg p-1.5 mr-3 transition-colors ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-sm shadow-teal-900/50'
                    : 'bg-[#122023] text-slate-400 group-hover:text-teal-300'
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
              </div>

              {!isSidebarCollapsed && (
                <div className="flex-1 text-left truncate">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{item.label}</span>
                    {item.badge && (
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-teal-950 text-teal-400 border border-teal-800/40">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <span className="block text-[11px] text-slate-500 truncate font-normal">
                    {item.description}
                  </span>
                </div>
              )}
            </button>
          )
        })}
      </div>
    </aside>
  )
}
