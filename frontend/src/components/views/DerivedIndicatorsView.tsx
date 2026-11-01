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
  ReferenceLine,
} from 'recharts'
import {
  Calculator,
  CheckCircle,
  Scale,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { fetchDerivedIndicators } from '../../services/api'
import type { DerivedIndicatorsData } from '../../types'
import { LoadingSkeleton } from '../common/LoadingSkeleton'
import { ErrorMessage } from '../common/ErrorMessage'

export const DerivedIndicatorsView: React.FC = () => {
  const { selectedCountry } = useApp()
  const [data, setData] = useState<DerivedIndicatorsData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<'misery' | 'real_rate'>('misery')

  const loadData = async (code: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchDerivedIndicators(code)
      setData(res)
    } catch (err: any) {
      setError(err.message || 'Failed to calculate derived indicators')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(selectedCountry)
  }, [selectedCountry])

  if (loading) {
    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto">
        <LoadingSkeleton count={4} />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <ErrorMessage message={error || 'No derived indicators data available.'} onRetry={() => loadData(selectedCountry)} />
      </div>
    )
  }

  const { country, misery_index, real_interest_rate } = data

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1b2f34] pb-6">
        <div>
          <div className="flex items-center gap-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Calculator className="w-4 h-4" />
            <span>Macroeconomic Analytics Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Derived Economic Indicators
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Dynamically synthesized indicators computed from selected country ({country.name} {country.flag}):{' '}
            <b className="text-slate-300">Arthur Okun’s Misery Index</b> and the{' '}
            <b className="text-slate-300">Fisher Real Interest Rate Estimate</b>.
          </p>
        </div>

        {/* Sub-tab Switcher */}
        <div className="flex bg-[#0d1618] p-1 rounded-xl border border-[#1b2f34] self-start sm:self-auto">
          <button
            onClick={() => setActiveSubTab('misery')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              activeSubTab === 'misery'
                ? 'bg-teal-600 text-white shadow-md shadow-teal-950/50'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Misery Index
          </button>
          <button
            onClick={() => setActiveSubTab('real_rate')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              activeSubTab === 'real_rate'
                ? 'bg-teal-600 text-white shadow-md shadow-teal-950/50'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Real Interest Rate
          </button>
        </div>
      </div>

      {/* SUB-TAB 1: MISERY INDEX */}
      {activeSubTab === 'misery' && (
        <div className="space-y-6">
          {/* Top Score & Components Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Primary Misery KPI */}
            <div className="rounded-2xl border border-teal-500/30 bg-gradient-to-br from-[#0c181a] via-[#102226] to-[#0d1a1c] p-6 shadow-xl flex flex-col justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-teal-400">
                  Current Misery Index
                </span>
                <div className="flex items-baseline gap-2 mt-2 mb-1">
                  <span className="text-4xl sm:text-5xl font-black text-white font-mono">
                    {misery_index.value !== null ? misery_index.value.toFixed(2) : '—'}
                  </span>
                  <span className="text-sm font-semibold text-teal-300">points</span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold mt-2 bg-teal-950 text-teal-300 border border-teal-800/60">
                  <span className="h-2 w-2 rounded-full bg-teal-400 animate-pulse"></span>
                  {misery_index.severity}
                </div>
              </div>
              <p className="text-xs text-slate-400 mt-4 leading-relaxed">
                {misery_index.severity_desc}
              </p>
            </div>

            {/* Inflation Component Card */}
            <div className="rounded-2xl border border-[#1d3237] bg-[#111e21] p-6 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
                    Inflation Component (π)
                  </span>
                  <span className="text-[11px] font-mono text-slate-400 bg-[#0c1517] px-2 py-0.5 rounded border border-[#1b2f33]">
                    {misery_index.inflation_component.year}
                  </span>
                </div>
                <div className="text-3xl font-extrabold text-white font-mono my-2">
                  {misery_index.inflation_component.value !== null
                    ? `${misery_index.inflation_component.value.toFixed(2)}%`
                    : 'N/A'}
                </div>
                <div className="text-xs text-slate-400">
                  Share of index: <b className="text-amber-300">{misery_index.inflation_component.share_percent}%</b>
                </div>
                {/* Visual Progress bar */}
                <div className="w-full bg-[#17272b] h-2 rounded-full mt-3 overflow-hidden">
                  <div
                    className="bg-amber-400 h-full rounded-full transition-all"
                    style={{ width: `${misery_index.inflation_component.share_percent}%` }}
                  ></div>
                </div>
              </div>
              <div className="text-[11px] text-slate-500 pt-3 border-t border-[#1a2c30]">
                Source: {misery_index.inflation_component.source}
              </div>
            </div>

            {/* Unemployment Component Card */}
            <div className="rounded-2xl border border-[#1d3237] bg-[#111e21] p-6 shadow-lg flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                    Unemployment Component (u)
                  </span>
                  <span className="text-[11px] font-mono text-slate-400 bg-[#0c1517] px-2 py-0.5 rounded border border-[#1b2f33]">
                    {misery_index.unemployment_component.year}
                  </span>
                </div>
                <div className="text-3xl font-extrabold text-white font-mono my-2">
                  {misery_index.unemployment_component.value !== null
                    ? `${misery_index.unemployment_component.value.toFixed(2)}%`
                    : 'N/A'}
                </div>
                <div className="text-xs text-slate-400">
                  Share of index: <b className="text-indigo-300">{misery_index.unemployment_component.share_percent}%</b>
                </div>
                {/* Visual Progress bar */}
                <div className="w-full bg-[#17272b] h-2 rounded-full mt-3 overflow-hidden">
                  <div
                    className="bg-indigo-400 h-full rounded-full transition-all"
                    style={{ width: `${misery_index.unemployment_component.share_percent}%` }}
                  ></div>
                </div>
              </div>
              <div className="text-[11px] text-slate-500 pt-3 border-t border-[#1a2c30]">
                Source: {misery_index.unemployment_component.source}
              </div>
            </div>
          </div>

          {/* Compatibility Notice */}
          <div className="flex items-center gap-2 rounded-xl bg-[#0c1518] px-4 py-2.5 border border-[#1a2f33] text-xs text-slate-300">
            <CheckCircle className="w-4 h-4 text-teal-400 flex-shrink-0" />
            <span>{misery_index.compatibility_note}</span>
          </div>

          {/* Historical Misery Index Chart */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Historical Misery Index & Decomposed Drivers (1995–Present)
                </h3>
                <p className="text-xs text-slate-400">
                  Stacked breakdown of headline CPI inflation and total labor force unemployment
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400"></span> Misery Index
                </span>
                <span className="flex items-center gap-1.5 text-amber-400">
                  <span className="h-2 w-2 rounded-full bg-amber-400"></span> Inflation Component
                </span>
                <span className="flex items-center gap-1.5 text-indigo-400">
                  <span className="h-2 w-2 rounded-full bg-indigo-400"></span> Unemployment Component
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={misery_index.historical} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                  <XAxis dataKey="year" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} unit=" pts" />
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
                    dataKey="misery_index"
                    name="Misery Index"
                    stroke="#14b8a6"
                    strokeWidth={3}
                    dot={{ r: 2 }}
                    activeDot={{ r: 6 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="inflation"
                    name="Inflation (π)"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="unemployment"
                    name="Unemployment (u)"
                    stroke="#818cf8"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Cross-Country Benchmark Comparison */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">
              International Misery Index Comparison
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Comparing economic discomfort across major global peers (Lowest to Highest)
            </p>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={misery_index.benchmarks.slice(0, 10)} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                  <XAxis dataKey="code" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} unit=" pts" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0c1618',
                      borderColor: '#1d353b',
                      borderRadius: '8px',
                      color: '#e2e8f0',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="misery_index" name="Misery Index" fill="#0d9488" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Interpretation Card */}
          <div className="rounded-xl border border-[#1b2f34] bg-[#0c1618] p-5 text-xs text-slate-300 leading-relaxed">
            <h4 className="font-bold text-teal-300 text-sm mb-1.5">Economic Interpretation:</h4>
            <p>{misery_index.interpretation}</p>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: REAL INTEREST RATE */}
      {activeSubTab === 'real_rate' && (
        <div className="space-y-6">
          {/* Ex-Ante vs Ex-Post Distinction Alert */}
          <div className="rounded-xl border border-teal-800/60 bg-gradient-to-r from-teal-950/40 via-[#0f2125] to-[#0c1618] p-4 text-xs text-slate-200">
            <div className="flex items-center gap-2 font-bold text-teal-300 mb-1">
              <Scale className="w-4 h-4 text-teal-400" />
              <span>Fisher Equation Framework: Ex-Ante vs. Ex-Post Real Interest Rates</span>
            </div>
            <p className="text-slate-300 text-[11px] leading-relaxed">
              {real_interest_rate.methodology_note}
            </p>
          </div>

          {/* 3 Metric Cards for Real Rate */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Nominal Rate */}
            <div className="rounded-2xl border border-[#1d3237] bg-[#111e21] p-6 shadow-lg">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-400">
                1. Nominal Policy Rate (i)
              </span>
              <div className="text-4xl font-extrabold text-white font-mono my-2">
                {real_interest_rate.nominal_rate !== null
                  ? `${real_interest_rate.nominal_rate.toFixed(2)}%`
                  : 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 pt-2 border-t border-[#1a2b2f]">
                {real_interest_rate.nominal_source} ({real_interest_rate.nominal_period})
              </div>
            </div>

            {/* Observed Inflation */}
            <div className="rounded-2xl border border-[#1d3237] bg-[#111e21] p-6 shadow-lg">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
                2. Observed Inflation (π)
              </span>
              <div className="text-4xl font-extrabold text-white font-mono my-2">
                {real_interest_rate.inflation_used !== null
                  ? `${real_interest_rate.inflation_used.toFixed(2)}%`
                  : 'N/A'}
              </div>
              <div className="text-[11px] text-slate-400 pt-2 border-t border-[#1a2b2f]">
                Annual CPI Inflation ({real_interest_rate.inflation_period})
              </div>
            </div>

            {/* Ex-Post Real Interest Rate */}
            <div className="rounded-2xl border border-teal-500/30 bg-gradient-to-br from-[#0c181a] via-[#102226] to-[#0d1a1c] p-6 shadow-xl">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                3. Estimated Real Rate (r ≈ i − π)
              </span>
              <div className="text-4xl font-black text-white font-mono my-2">
                {real_interest_rate.ex_post_real_rate !== null
                  ? `${real_interest_rate.ex_post_real_rate > 0 ? '+' : ''}${real_interest_rate.ex_post_real_rate.toFixed(2)}%`
                  : 'N/A'}
              </div>
              <div className="text-xs font-bold text-teal-300">
                Stance: {real_interest_rate.policy_stance}
              </div>
            </div>
          </div>

          {/* Historical Real Rate Chart */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Historical Real Interest Rate Trajectory (1995–Present)
                </h3>
                <p className="text-xs text-slate-400">
                  Observed inflation-adjusted borrowing costs against the zero lower bound threshold
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400"></span> Real Rate (%)
                </span>
                <span className="flex items-center gap-1.5 text-amber-400">
                  <span className="h-2 w-2 rounded-full bg-amber-400"></span> Inflation (%)
                </span>
              </div>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={real_interest_rate.historical} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
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
                  <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Zero Real Rate', fill: '#ef4444', fontSize: 10 }} />
                  <Line
                    type="monotone"
                    dataKey="real_rate"
                    name="Real Interest Rate"
                    stroke="#14b8a6"
                    strokeWidth={2.5}
                    dot={{ r: 2 }}
                    activeDot={{ r: 5 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="inflation"
                    name="Inflation"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Policy Stance Explanation Card */}
          <div className="rounded-xl border border-[#1b2f34] bg-[#0c1618] p-5 text-xs text-slate-300 leading-relaxed">
            <h4 className="font-bold text-teal-300 text-sm mb-1.5">Monetary Policy Transmission:</h4>
            <p>{real_interest_rate.policy_stance_desc}</p>
          </div>
        </div>
      )}
    </div>
  )
}
