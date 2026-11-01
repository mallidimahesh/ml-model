import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { Globe, ArrowRight, Filter } from 'lucide-react'
import { fetchGlobalOverview } from '../../services/api'
import type { GlobalOverviewData, RankingItem } from '../../types'
import { KPICard } from '../common/KPICard'
import { LoadingSkeleton } from '../common/LoadingSkeleton'
import { ErrorMessage } from '../common/ErrorMessage'
import { useApp } from '../../context/AppContext'

export const GlobalOverviewView: React.FC = () => {
  const { setSelectedCountry, setActiveTab, countryList } = useApp()
  const [data, setData] = useState<GlobalOverviewData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [rankingMetric, setRankingMetric] = useState<
    'by_gdp' | 'by_growth' | 'by_inflation' | 'by_unemployment' | 'by_pcap'
  >('by_gdp')
  const [selectedRegion, setSelectedRegion] = useState<string>('All')

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchGlobalOverview()
      setData(res)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch global macroeconomic overview')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <LoadingSkeleton count={6} />
        <div className="h-72 rounded-xl bg-[#111e21]/60 animate-pulse border border-[#1d3237]"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <ErrorMessage message={error || 'No global overview data available.'} onRetry={loadData} />
      </div>
    )
  }

  const regions = ['All', ...Array.from(new Set(countryList.map((c) => c.region)))]

  const filteredCountries = countryList.filter(
    (c) => selectedRegion === 'All' || c.region === selectedRegion
  )

  const currentRankingList: RankingItem[] = data.rankings[rankingMetric] || []
  const filteredRankings = currentRankingList
    .filter((item) => selectedRegion === 'All' || item.region === selectedRegion)
    .slice(0, 10)

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1b2f34] pb-6">
        <div>
          <div className="flex items-center gap-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Globe className="w-4 h-4" />
            <span>Worldwide Macroeconomic Aggregates</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Global Economic Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Real-time macroeconomic aggregates directly sourced from World Bank Open Data (official
            aggregate <code className="text-teal-300">1W/WLD</code>) and the Federal Reserve
            (FRED).
          </p>
        </div>

        {/* Region Filter */}
        <div className="flex items-center gap-2 self-start md:self-auto bg-[#101e21] border border-[#1f373d] p-1 rounded-xl text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-2" />
          <span className="text-slate-400 text-[11px] font-medium">Region:</span>
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="bg-transparent text-white text-xs font-semibold focus:outline-none pr-3 py-1 cursor-pointer"
          >
            {regions.map((r) => (
              <option key={r} value={r} className="bg-[#0e181a] text-slate-200">
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Global KPI Cards (6 metrics) */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Global Macroeconomic KPI Cards
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">
            Updated: {data.data_status.timestamp}
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.kpis.map((kpi, idx) => (
            <KPICard
              key={kpi.id}
              label={kpi.label}
              value={kpi.formatted}
              unit={kpi.unit}
              period={kpi.period}
              change={kpi.change}
              coverage={kpi.coverage}
              source={kpi.source}
              highlight={idx === 0}
            />
          ))}
        </div>
      </section>

      {/* Historical World Trends Chart (2000 - 2023) */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Global Macroeconomic Trends (2000–2023)
            </h3>
            <p className="text-xs text-slate-400">
              Annual World GDP Growth, CPI Inflation, and Unemployment Rate (World Bank 1W Aggregate)
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-teal-400">
              <span className="h-2 w-2 rounded-full bg-teal-400"></span> GDP Growth (%)
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="h-2 w-2 rounded-full bg-amber-400"></span> Inflation (%)
            </span>
            <span className="flex items-center gap-1.5 text-indigo-400">
              <span className="h-2 w-2 rounded-full bg-indigo-400"></span> Unemployment (%)
            </span>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.historical_trends} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
              <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0c1618',
                  borderColor: '#1d353b',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  fontSize: '12px',
                }}
              />
              <Line
                type="monotone"
                dataKey="gdp_growth"
                name="World GDP Growth"
                stroke="#14b8a6"
                strokeWidth={2.5}
                dot={{ r: 2 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="inflation"
                name="World Inflation"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 2 }}
              />
              <Line
                type="monotone"
                dataKey="unemployment"
                name="World Unemployment"
                stroke="#818cf8"
                strokeWidth={2}
                dot={{ r: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Multi-Country Comparative Rankings */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Cross-Country Rankings & Performance
            </h3>
            <p className="text-xs text-slate-400">
              Comparative analysis across economies. Click any country to open its Country Explorer profile.
            </p>
          </div>

          {/* Metric Selector Tabs */}
          <div className="flex flex-wrap gap-1 bg-[#0b1416] p-1 rounded-lg border border-[#1d3339]">
            {[
              { id: 'by_gdp', label: 'GDP Size' },
              { id: 'by_growth', label: 'GDP Growth' },
              { id: 'by_inflation', label: 'Inflation' },
              { id: 'by_unemployment', label: 'Unemployment' },
              { id: 'by_pcap', label: 'GDP Per Capita' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setRankingMetric(tab.id as any)}
                className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
                  rankingMetric === tab.id
                    ? 'bg-teal-600 text-white font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Bar Chart Visualization of Ranking */}
        <div className="h-64 w-full mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={filteredRankings.map((r) => ({
                name: r.code,
                fullName: r.name,
                value:
                  rankingMetric === 'by_gdp'
                    ? r.gdp_cd / 1e12
                    : rankingMetric === 'by_growth'
                    ? r.gdp_growth
                    : rankingMetric === 'by_inflation'
                    ? r.inflation
                    : rankingMetric === 'by_unemployment'
                    ? r.unemployment
                    : r.gdp_pcap,
              }))}
              margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                unit={
                  rankingMetric === 'by_gdp'
                    ? 'T$'
                    : rankingMetric === 'by_pcap'
                    ? '$'
                    : '%'
                }
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0c1618',
                  borderColor: '#1d353b',
                  borderRadius: '8px',
                  color: '#e2e8f0',
                  fontSize: '12px',
                }}
                formatter={(val: any) => [
                  rankingMetric === 'by_gdp'
                    ? `$${Number(val).toFixed(2)} Trillion`
                    : rankingMetric === 'by_pcap'
                    ? `$${Number(val).toLocaleString()}`
                    : `${Number(val).toFixed(2)}%`,
                  'Value',
                ]}
              />
              <Bar dataKey="value" fill="#0d9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Ranking Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0b1416] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1c3035]">
              <tr>
                <th className="py-2.5 px-3">Rank</th>
                <th className="py-2.5 px-3">Country</th>
                <th className="py-2.5 px-3 text-right">Nominal GDP</th>
                <th className="py-2.5 px-3 text-right">GDP Growth</th>
                <th className="py-2.5 px-3 text-right">Inflation</th>
                <th className="py-2.5 px-3 text-right">Unemployment</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#17272b]">
              {filteredRankings.map((item, index) => (
                <tr
                  key={item.code}
                  className="hover:bg-[#142327] transition-colors cursor-pointer group"
                  onClick={() => {
                    setSelectedCountry(item.code)
                    setActiveTab('country')
                  }}
                >
                  <td className="py-2.5 px-3 font-mono text-slate-500 font-bold">#{index + 1}</td>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{item.flag}</span>
                      <div>
                        <span className="font-semibold text-white group-hover:text-teal-300 transition-colors">
                          {item.name}
                        </span>
                        <span className="ml-1.5 text-[10px] text-slate-500 font-mono">
                          {item.code}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-white font-medium">
                    {item.gdp_formatted}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono">
                    <span
                      className={
                        item.gdp_growth >= 0
                          ? 'text-emerald-400 font-medium'
                          : 'text-rose-400 font-medium'
                      }
                    >
                      {item.gdp_growth > 0 ? `+${item.gdp_growth.toFixed(2)}` : item.gdp_growth.toFixed(2)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-amber-300">
                    {item.inflation.toFixed(2)}%
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-indigo-300">
                    {item.unemployment.toFixed(2)}%
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <span className="inline-flex items-center gap-1 text-teal-400 hover:text-teal-300 font-semibold group-hover:translate-x-0.5 transition-transform">
                      Explore <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Selectable Countries Grid */}
      <section>
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-3">
          Selectable National Economies ({filteredCountries.length})
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {filteredCountries.map((c) => (
            <button
              key={c.code}
              onClick={() => {
                setSelectedCountry(c.code)
                setActiveTab('country')
              }}
              className="group flex flex-col items-center justify-center p-3 rounded-xl border border-[#1b2f34] bg-[#101c1f] hover:border-teal-500 hover:bg-[#13272b] transition-all text-center"
            >
              <span className="text-2xl mb-1 group-hover:scale-110 transition-transform">
                {c.flag}
              </span>
              <span className="text-xs font-semibold text-white group-hover:text-teal-300 truncate w-full">
                {c.name}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">{c.code}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}
