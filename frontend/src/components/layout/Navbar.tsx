import React, { useState, useRef, useEffect } from 'react'
import {
  Activity,
  ChevronDown,
  Search,
  Check,
  Menu,
  ShieldCheck,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

export const Navbar: React.FC = () => {
  const {
    selectedCountry,
    setSelectedCountry,
    countryList,
    currentCountryMeta,
    isSidebarCollapsed,
    setIsSidebarCollapsed,
  } = useApp()

  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredCountries = countryList.filter(
    (c) =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.region.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-[#1b2f34] bg-[#090e10]/95 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between">
      {/* Left side: Hamburger + EcoSim Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsSidebarCollapsed((prev) => !prev)}
          className="rounded-lg p-2 text-slate-400 hover:bg-[#122023] hover:text-teal-300 transition-colors"
          title={isSidebarCollapsed ? 'Expand navigation' : 'Collapse navigation'}
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-tr from-teal-700 to-emerald-500 shadow-md shadow-teal-950/40">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-base tracking-tight font-mono">EcoSim</span>
              <span className="inline-flex items-center gap-1 rounded bg-teal-950 px-1.5 py-0.5 text-[10px] font-semibold text-teal-300 border border-teal-800/50">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                LIVE INTEL
              </span>
            </div>
            <span className="hidden sm:inline-block text-[11px] text-slate-400">
              Macroeconomic Data & Policy Simulation
            </span>
          </div>
        </div>
      </div>

      {/* Right side: Country Switcher & Live Badges */}
      <div className="flex items-center gap-3">
        {/* Status Badge */}
        <div className="hidden md:flex items-center gap-2 rounded-lg bg-[#0e171a] px-3 py-1.5 border border-[#1a2d31] text-xs text-slate-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-[11px] font-medium">FRED & World Bank Connected</span>
        </div>

        {/* Synchronized Country Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen((prev) => !prev)}
            className="flex items-center gap-2.5 rounded-lg border border-teal-600/40 bg-[#101e21] px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:border-teal-500 hover:bg-[#14282c] transition-all"
          >
            <span className="text-base">{currentCountryMeta?.flag || '🌐'}</span>
            <span className="font-semibold">{currentCountryMeta?.name || selectedCountry}</span>
            <span className="rounded bg-teal-950 px-1 py-0.5 text-[10px] text-teal-400 border border-teal-800/40 font-mono">
              {selectedCountry}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-400 ml-1" />
          </button>

          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl border border-[#213a3f] bg-[#0d1618] shadow-2xl shadow-black/80 z-50 overflow-hidden">
              <div className="p-2 border-b border-[#1b2f33]">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search country or region..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full rounded-md bg-[#132225] pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 border border-[#233f45] focus:outline-none focus:border-teal-500"
                    autoFocus
                  />
                </div>
              </div>

              <div className="max-h-64 overflow-y-auto p-1 divide-y divide-[#17272b]">
                {filteredCountries.map((c) => (
                  <button
                    key={c.code}
                    onClick={() => {
                      setSelectedCountry(c.code)
                      setIsDropdownOpen(false)
                      setSearchTerm('')
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs text-left rounded-lg transition-colors ${
                      c.code === selectedCountry
                        ? 'bg-teal-900/40 text-teal-200 font-semibold'
                        : 'text-slate-300 hover:bg-[#132427]'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-base">{c.flag}</span>
                      <div className="truncate">
                        <span className="block truncate">{c.name}</span>
                        <span className="text-[10px] text-slate-500">{c.region}</span>
                      </div>
                    </div>
                    {c.code === selectedCountry && (
                      <Check className="w-4 h-4 text-teal-400 flex-shrink-0" />
                    )}
                  </button>
                ))}
                {filteredCountries.length === 0 && (
                  <div className="p-3 text-center text-xs text-slate-500">No countries match</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
