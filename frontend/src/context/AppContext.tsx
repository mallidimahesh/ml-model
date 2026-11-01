import React, { createContext, useContext, useState, useEffect } from 'react'
import type { CountryMeta } from '../types'
import { fetchCountries, fetchStatus } from '../services/api'

export type NavTab = 'global' | 'country' | 'derived' | 'forecast' | 'simulator'

interface AppContextType {
  activeTab: NavTab
  setActiveTab: (tab: NavTab) => void
  selectedCountry: string
  setSelectedCountry: (code: string) => void
  countryList: CountryMeta[]
  currentCountryMeta?: CountryMeta
  isSidebarCollapsed: boolean
  setIsSidebarCollapsed: React.Dispatch<React.SetStateAction<boolean>>
  systemStatus: any
  isLoadingCountries: boolean
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<NavTab>('global')
  const [selectedCountry, setSelectedCountry] = useState<string>('USA')
  const [countryList, setCountryList] = useState<CountryMeta[]>([])
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false)
  const [systemStatus, setSystemStatus] = useState<any>(null)
  const [isLoadingCountries, setIsLoadingCountries] = useState<boolean>(true)

  useEffect(() => {
    async function init() {
      try {
        const [countries, status] = await Promise.all([fetchCountries(), fetchStatus()])
        setCountryList(countries)
        setSystemStatus(status)
      } catch (err) {
        console.error('Failed to initialize app context', err)
      } finally {
        setIsLoadingCountries(false)
      }
    }
    init()
  }, [])

  const currentCountryMeta = countryList.find((c) => c.code === selectedCountry)

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedCountry,
        setSelectedCountry,
        countryList,
        currentCountryMeta,
        isSidebarCollapsed,
        setIsSidebarCollapsed,
        systemStatus,
        isLoadingCountries,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp(): AppContextType {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp must be used within an AppProvider')
  return context
}
