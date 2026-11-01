import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import {
  Activity,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { fetchCountryProfile } from '../../services/api'
import type { CountryProfile } from '../../types'
import { KPICard } from '../common/KPICard'
import { LoadingSkeleton } from '../common/LoadingSkeleton'
import { ErrorMessage } from '../common/ErrorMessage'

const INDICATOR_OPTIONS = [
  { code: 'NY.GDP.MKTP.CD', label: 'Nominal GDP (Current US$)', unit: '$' },
  { code: 'NY.GDP.MKTP.KD', label: 'Real GDP (Constant 2015 US$)', unit: '$' },
  { code: 'NY.GDP.PCAP.CD', label: 'Nominal GDP Per Capita (Current US$)', unit: '$' },
  { code: 'NY.GDP.PCAP.KD', label: 'Real GDP Per Capita (Constant 2015 US$)', unit: '$' },
  { code: 'NY.GDP.MKTP.KD.ZG', label: 'GDP Growth Rate (Annual %)', unit: '%' },
  { code: 'FP.CPI.TOTL.ZG', label: 'CPI Inflation (Annual %)', unit: '%' },
  { code: 'SL.UEM.TOTL.ZS', label: 'Unemployment Rate (% Labor Force)', unit: '%' },
  { code: 'NE.GDI.FTOT.ZS', label: 'Gross Capital Formation (% of GDP)', unit: '%' },
  { code: 'NE.CON.GOVT.ZS', label: 'Government Expenditure (% of GDP)', unit: '%' },
]

export const CountryExplorerView: React.FC = () => {
  const { selectedCountry, setSelectedCountry, countryList } = useApp()
  const [profile, setProfile] = useState<CountryProfile | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Chart controls
  const [selectedIndicator, setSelectedIndicator] = useState<string>('NY.GDP.MKTP.KD.ZG')
  const [timeRange, setTimeRange] = useState<'5Y' | '10Y' | '20Y' | 'ALL'>('20Y')
  const [compareCountry, setCompareCountry] = useState<string>('')
  const [compareProfile, setCompareProfile] = useState<CountryProfile | null>(null)

  const loadProfile = async (code: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchCountryProfile(code)
      setProfile(res)
    } catch (err: any) {
      setError(err.message || `Failed to fetch profile for ${code}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfile(selectedCountry)
  }, [selectedCountry])

  useEffect(() => {
    if (compareCountry && compareCountry !== selectedCountry) {
      fetchCountryProfile(compareCountry)
        .then((res) => setCompareProfile(res))
        .catch(() => setCompareProfile(null))
    } else {
      setCompareProfile(null)
    }
  }, [compareCountry, selectedCountry])

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <LoadingSkeleton count={8} />
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="p-6">
        <ErrorMessage message={error || 'No data available'} onRetry={() => loadProfile(selectedCountry)} />
      </div>
    )
  }

  const { metadata, latest, policy_rate, series, quarterly_series } = profile

  // Prepare chart data with time filtering & comparison
  const rawSeries = series[selectedIndicator] || []
  const currentYear = new Date().getFullYear()
  const startYearFilter =
    timeRange === '5Y'
      ? currentYear - 6
      : timeRange === '10Y'
      ? currentYear - 11
      : timeRange === '20Y'
      ? currentYear - 21
      : 1990

  const compareSeries = compareProfile?.series[selectedIndicator] || []
  const compareDict = new Map<number, number>(compareSeries.map((s) => [s.year, s.value]))

  const chartData = rawSeries
    .filter((pt) => pt.year >= startYearFilter)
    .map((pt) => ({
      year: pt.year,
      [metadata.code]: pt.value,
      ...(compareProfile ? { [compareProfile.metadata.code]: compareDict.get(pt.year) ?? null } : {}),
    }))



  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Country Header Card */}
      <div className="rounded-2xl border border-[#1d353b] bg-gradient-to-r from-[#0d171a] via-[#102024] to-[#0c1618] p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <span className="text-5xl drop-shadow-md">{metadata.flag}</span>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                {metadata.name}
              </h1>
              <span className="rounded bg-teal-950 px-2 py-0.5 text-xs font-mono font-bold text-teal-300 border border-teal-800/50">
                {metadata.code}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1.5">
              <span>Region: <b className="text-slate-200">{metadata.region}</b></span>
              <span>•</span>
              <span>Income: <b className="text-slate-200">{metadata.income}</b></span>
              <span>•</span>
              <span>Currency: <b className="text-teal-300 font-mono">{metadata.currency}</b></span>
            </div>
          </div>
        </div>

        {/* Quick Country Switcher */}
        <div className="flex items-center gap-2 self-start md:self-auto bg-[#0a1214] p-1.5 rounded-xl border border-[#1b2f34]">
          <span className="text-xs text-slate-400 font-medium ml-2">Switch Nation:</span>
          <select
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="bg-[#122226] text-white text-xs font-semibold rounded-lg px-3 py-1.5 border border-[#1f383e] focus:outline-none cursor-pointer"
          >
            {countryList.map((c) => (
              <option key={c.code} value={c.code}>
                {c.flag} {c.name} ({c.code})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Comprehensive Country Indicators KPI Grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Latest Available Macroeconomic Profile
          </h2>
          <span className="text-xs text-slate-400 font-mono">World Bank & National Sources</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 1. Nominal GDP */}
          <KPICard
            label="Nominal GDP (Current US$)"
            value={
              latest['NY.GDP.MKTP.CD']?.value
                ? `$${(latest['NY.GDP.MKTP.CD'].value / 1e12).toFixed(2)}T`
                : 'Data unavailable'
            }
            period={latest['NY.GDP.MKTP.CD']?.year ? `${latest['NY.GDP.MKTP.CD'].year}` : undefined}
            source="World Bank (NY.GDP.MKTP.CD)"
            coverage="Purchaser's prices in current US$"
            highlight={true}
          />

          {/* 2. Real GDP */}
          <KPICard
            label="Real GDP (Constant 2015 US$)"
            value={
              latest['NY.GDP.MKTP.KD']?.value
                ? `$${(latest['NY.GDP.MKTP.KD'].value / 1e12).toFixed(2)}T`
                : 'Data unavailable'
            }
            period={latest['NY.GDP.MKTP.KD']?.year ? `${latest['NY.GDP.MKTP.KD'].year}` : undefined}
            source="World Bank (NY.GDP.MKTP.KD)"
            coverage="Constant 2015 US$ (Inflation-adjusted)"
          />

          {/* 3. Nominal GDP Per Capita */}
          <KPICard
            label="Nominal GDP Per Capita"
            value={
              latest['NY.GDP.PCAP.CD']?.value
                ? `$${Math.round(latest['NY.GDP.PCAP.CD'].value).toLocaleString()}`
                : 'Data unavailable'
            }
            period={latest['NY.GDP.PCAP.CD']?.year ? `${latest['NY.GDP.PCAP.CD'].year}` : undefined}
            source="World Bank (NY.GDP.PCAP.CD)"
            coverage="Current US$ per person"
          />

          {/* 4. Real GDP Per Capita */}
          <KPICard
            label="Real GDP Per Capita"
            value={
              latest['NY.GDP.PCAP.KD']?.value
                ? `$${Math.round(latest['NY.GDP.PCAP.KD'].value).toLocaleString()}`
                : 'Data unavailable'
            }
            period={latest['NY.GDP.PCAP.KD']?.year ? `${latest['NY.GDP.PCAP.KD'].year}` : undefined}
            source="World Bank (NY.GDP.PCAP.KD)"
            coverage="Constant 2015 US$ per person"
          />

          {/* 5. Real GDP Growth */}
          <KPICard
            label="Annual GDP Growth"
            value={
              latest['NY.GDP.MKTP.KD.ZG']?.value !== null && latest['NY.GDP.MKTP.KD.ZG']?.value !== undefined
                ? `${latest['NY.GDP.MKTP.KD.ZG'].value > 0 ? '+' : ''}${latest['NY.GDP.MKTP.KD.ZG'].value.toFixed(2)}%`
                : 'Data unavailable'
            }
            period={latest['NY.GDP.MKTP.KD.ZG']?.year ? `${latest['NY.GDP.MKTP.KD.ZG'].year}` : undefined}
            source="World Bank (NY.GDP.MKTP.KD.ZG)"
            coverage="Annual real growth rate"
          />

          {/* 6. CPI Inflation */}
          <KPICard
            label="CPI Inflation (Annual %)"
            value={
              latest['FP.CPI.TOTL.ZG']?.value !== null && latest['FP.CPI.TOTL.ZG']?.value !== undefined
                ? `${latest['FP.CPI.TOTL.ZG'].value.toFixed(2)}%`
                : 'Data unavailable'
            }
            period={latest['FP.CPI.TOTL.ZG']?.year ? `${latest['FP.CPI.TOTL.ZG'].year}` : undefined}
            source="World Bank (FP.CPI.TOTL.ZG)"
            coverage="Headline Consumer Price Index"
          />

          {/* 7. Unemployment Rate */}
          <KPICard
            label="Unemployment Rate"
            value={
              latest['SL.UEM.TOTL.ZS']?.value !== null && latest['SL.UEM.TOTL.ZS']?.value !== undefined
                ? `${latest['SL.UEM.TOTL.ZS'].value.toFixed(2)}%`
                : 'Data unavailable'
            }
            period={latest['SL.UEM.TOTL.ZS']?.year ? `${latest['SL.UEM.TOTL.ZS'].year}` : undefined}
            source="World Bank / ILO Modeled (SL.UEM.TOTL.ZS)"
            coverage="% of total civilian labor force"
          />

          {/* 8. Policy Interest Rate */}
          <KPICard
            label="Policy / Benchmark Interest Rate"
            value={
              policy_rate?.value !== null && policy_rate?.value !== undefined
                ? `${policy_rate.value.toFixed(2)}%`
                : 'Data unavailable'
            }
            period={policy_rate?.period || 'Latest'}
            source={policy_rate?.source || 'National Central Bank'}
            coverage={policy_rate?.frequency || 'Official Target'}
          />

          {/* 9. Government Final Consumption */}
          <KPICard
            label="Government Consumption (% of GDP)"
            value={
              latest['NE.CON.GOVT.ZS']?.value !== null && latest['NE.CON.GOVT.ZS']?.value !== undefined
                ? `${latest['NE.CON.GOVT.ZS'].value.toFixed(1)}%`
                : 'Data unavailable'
            }
            period={latest['NE.CON.GOVT.ZS']?.year ? `${latest['NE.CON.GOVT.ZS'].year}` : undefined}
            source="World Bank (NE.CON.GOVT.ZS)"
            coverage="General gov final consumption / GDP"
          />

          {/* 10. Gross Capital Formation */}
          <KPICard
            label="Gross Capital Formation (% of GDP)"
            value={
              latest['NE.GDI.FTOT.ZS']?.value !== null && latest['NE.GDI.FTOT.ZS']?.value !== undefined
                ? `${latest['NE.GDI.FTOT.ZS'].value.toFixed(1)}%`
                : 'Data unavailable'
            }
            period={latest['NE.GDI.FTOT.ZS']?.year ? `${latest['NE.GDI.FTOT.ZS'].year}` : undefined}
            source="World Bank (NE.GDI.FTOT.ZS)"
            coverage="Domestic investment & infrastructure / GDP"
          />
        </div>
      </section>

      {/* Interactive Time-Series Section with Country Comparison */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Historical Time-Series Analytics
            </h3>
            <p className="text-xs text-slate-400">
              Interactive historical trajectory. Choose an indicator, timeframe, and optional benchmark nation.
            </p>
          </div>

          {/* Controls: Indicator selector, Range filters, Country Comparison */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Indicator Select */}
            <select
              value={selectedIndicator}
              onChange={(e) => setSelectedIndicator(e.target.value)}
              className="bg-[#0b1416] text-white text-xs font-medium rounded-lg px-3 py-1.5 border border-[#1f373d] focus:outline-none cursor-pointer"
            >
              {INDICATOR_OPTIONS.map((opt) => (
                <option key={opt.code} value={opt.code}>
                  {opt.label}
                </option>
              ))}
            </select>

            {/* Timeframe buttons */}
            <div className="flex bg-[#0b1416] p-1 rounded-lg border border-[#1d343a]">
              {(['5Y', '10Y', '20Y', 'ALL'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setTimeRange(r)}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                    timeRange === r
                      ? 'bg-teal-600 text-white font-semibold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* Compare Country Dropdown */}
            <div className="flex items-center gap-1.5 bg-[#0b1416] px-2.5 py-1 rounded-lg border border-[#1d343a] text-xs">
              <span className="text-slate-400 text-[11px]">Compare:</span>
              <select
                value={compareCountry}
                onChange={(e) => setCompareCountry(e.target.value)}
                className="bg-transparent text-teal-300 font-semibold focus:outline-none cursor-pointer"
              >
                <option value="" className="bg-[#0e1719] text-slate-400">
                  None
                </option>
                {countryList
                  .filter((c) => c.code !== selectedCountry)
                  .map((c) => (
                    <option key={c.code} value={c.code} className="bg-[#0e1719] text-slate-200">
                      {c.flag} {c.code}
                    </option>
                  ))}
              </select>
            </div>
          </div>
        </div>

        {/* Chart Container */}
        <div className="h-80 w-full">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  tickFormatter={(val) =>
                    val >= 1e12
                      ? `$${(val / 1e12).toFixed(1)}T`
                      : val >= 1e9
                      ? `$${(val / 1e9).toFixed(1)}B`
                      : `${val}`
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
                    typeof val === 'number'
                      ? val >= 1e12
                        ? `$${(val / 1e12).toFixed(2)} Trillion`
                        : val >= 1e9
                        ? `$${(val / 1e9).toFixed(2)} Billion`
                        : `${val.toFixed(2)}`
                      : 'N/A',
                    'Observation',
                  ]}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey={metadata.code}
                  name={`${metadata.name} (${metadata.code})`}
                  stroke="#14b8a6"
                  strokeWidth={2.5}
                  dot={{ r: 2 }}
                  activeDot={{ r: 5 }}
                />
                {compareProfile && (
                  <Line
                    type="monotone"
                    dataKey={compareProfile.metadata.code}
                    name={`${compareProfile.metadata.name} (${compareProfile.metadata.code})`}
                    stroke="#f59e0b"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={{ r: 2 }}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              No historical observations found for this indicator.
            </div>
          )}
        </div>
      </section>

      {/* High-Frequency Quarterly Section for US (FRED Series) */}
      {quarterly_series && quarterly_series.length > 0 && (
        <section className="rounded-xl border border-teal-800/40 bg-[#0d181b] p-5 shadow-lg">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-5 h-5 text-teal-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-teal-200">
              High-Frequency Quarterly Series (FRED St. Louis Fed)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Recent harmonized quarterly observations for Real GDP Growth (GDPC1), YoY Inflation (CPIAUCSL),
            Unemployment (UNRATE), and Effective Fed Funds Rate (FEDFUNDS).
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#091113] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1b2f34]">
                <tr>
                  <th className="py-2 px-3">Quarter</th>
                  <th className="py-2 px-3 text-right">Real GDP Growth (YoY %)</th>
                  <th className="py-2 px-3 text-right">CPI Inflation (YoY %)</th>
                  <th className="py-2 px-3 text-right">Unemployment (%)</th>
                  <th className="py-2 px-3 text-right">Fed Funds Rate (%)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#152528]">
                {quarterly_series.slice(-8).reverse().map((q) => (
                  <tr key={q.quarter} className="hover:bg-[#122226]">
                    <td className="py-2 px-3 font-semibold text-white">{q.quarter}</td>
                    <td className="py-2 px-3 text-right text-emerald-400">
                      {q.gdp_growth_yoy !== null ? `${q.gdp_growth_yoy > 0 ? '+' : ''}${q.gdp_growth_yoy}%` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right text-amber-300">
                      {q.inflation_yoy !== null ? `${q.inflation_yoy}%` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right text-indigo-300">
                      {q.unemployment !== null ? `${q.unemployment}%` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right text-teal-300">
                      {q.fedfunds !== null ? `${q.fedfunds}%` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
