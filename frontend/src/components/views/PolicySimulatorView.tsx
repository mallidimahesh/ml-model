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
import {
  Sliders,
  RotateCcw,
  ShieldAlert,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { simulateKeynesian, simulateISLM, fetchCountryProfile } from '../../services/api'
import type { KeynesianResult, ISLMResult } from '../../types'

export const PolicySimulatorView: React.FC = () => {
  const { selectedCountry, currentCountryMeta } = useApp()
  const [activeTab, setActiveTab] = useState<'keynesian' | 'islm'>('keynesian')

  // Keynesian State
  const [keynesianGdp, setKeynesianGdp] = useState<number>(27800.0)
  const [deltaG, setDeltaG] = useState<number>(250.0)
  const [mpc, setMpc] = useState<number>(0.75)
  const [taxRate, setTaxRate] = useState<number>(0.0)
  const [importPropensity, setImportPropensity] = useState<number>(0.0)
  const [keynesianResult, setKeynesianResult] = useState<KeynesianResult | null>(null)

  // IS-LM State
  const [deltaR, setDeltaR] = useState<number>(1.0)
  const [deltaFiscalG, setDeltaFiscalG] = useState<number>(0.0)
  const [paramC, setParamC] = useState<number>(0.75)
  const [paramB, setParamB] = useState<number>(50.0)
  const [paramKy, setParamKy] = useState<number>(0.20)
  const [paramH, setParamH] = useState<number>(40.0)
  const [islmResult, setIslmResult] = useState<ISLMResult | null>(null)

  // Sync selected country GDP into Keynesian baseline
  useEffect(() => {
    fetchCountryProfile(selectedCountry).then((p) => {
      const gdpVal = p.latest['NY.GDP.MKTP.CD']?.value
      if (gdpVal && gdpVal > 0) {
        setKeynesianGdp(Math.round(gdpVal / 1e9))
        setDeltaG(Math.round((gdpVal / 1e9) * 0.01))
      }
    })
  }, [selectedCountry])

  // Run Keynesian simulation
  useEffect(() => {
    let isCancelled = false
    simulateKeynesian({
      baseline_gdp: keynesianGdp,
      delta_g: deltaG,
      mpc,
      tax_rate: taxRate,
      import_propensity: importPropensity,
    })
      .then((res) => {
        if (!isCancelled) setKeynesianResult(res)
      })
      .catch((err) => console.error(err))
    return () => {
      isCancelled = true
    }
  }, [keynesianGdp, deltaG, mpc, taxRate, importPropensity])

  // Run IS-LM simulation
  useEffect(() => {
    let isCancelled = false
    simulateISLM({
      delta_r: deltaR,
      delta_g: deltaFiscalG,
      c: paramC,
      b: paramB,
      k_y: paramKy,
      h: paramH,
    })
      .then((res) => {
        if (!isCancelled) setIslmResult(res)
      })
      .catch((err) => console.error(err))
    return () => {
      isCancelled = true
    }
  }, [deltaR, deltaFiscalG, paramC, paramB, paramKy, paramH])

  const applyISLMPreset = (preset: { delta_r: number; delta_g: number }) => {
    setDeltaR(preset.delta_r)
    setDeltaFiscalG(preset.delta_g)
  }

  const resetISLM = () => {
    setDeltaR(1.0)
    setDeltaFiscalG(0.0)
    setParamC(0.75)
    setParamB(50.0)
    setParamKy(0.20)
    setParamH(40.0)
  }

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1b2f34] pb-6">
        <div>
          <div className="flex items-center gap-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Sliders className="w-4 h-4" />
            <span>Interactive Policy Laboratory</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Macroeconomic Policy Simulator
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Simulate theoretical policy shocks calibrated with {currentCountryMeta?.name}'s ({currentCountryMeta?.flag}) economic parameters:{' '}
            <b className="text-slate-300">Keynesian Government Expenditure Multiplier</b> and the{' '}
            <b className="text-slate-300">IS–LM Equilibrium Framework</b>.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-[#0d1618] p-1 rounded-xl border border-[#1b2f34] self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('keynesian')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              activeTab === 'keynesian'
                ? 'bg-teal-600 text-white shadow-md shadow-teal-950/50'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            A. Keynesian Multiplier
          </button>
          <button
            onClick={() => setActiveTab('islm')}
            className={`px-4 py-2 text-xs font-bold rounded-lg transition-all ${
              activeTab === 'islm'
                ? 'bg-teal-600 text-white shadow-md shadow-teal-950/50'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            B. IS–LM Policy Model
          </button>
        </div>
      </div>

      {/* MODULE A: KEYNESIAN EXPENDITURE MULTIPLIER */}
      {activeTab === 'keynesian' && keynesianResult && (
        <div className="space-y-6">
          {/* Controls Card */}
          <section className="rounded-2xl border border-[#1d3338] bg-[#0d171a] p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#182b2f] pb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Expenditure Multiplier Controls & Assumptions
              </h3>
              <span className="text-[11px] font-mono text-teal-400 bg-teal-950 px-2 py-0.5 rounded border border-teal-800/40">
                Formula: ΔY = ΔG / (1 − MPC)
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Baseline GDP */}
              <div>
                <label className="block text-xs text-slate-300 font-medium mb-1">
                  Baseline National Income (Y₀ in $ Billions):
                </label>
                <input
                  type="number"
                  min="1"
                  step="10"
                  value={keynesianGdp}
                  onChange={(e) => setKeynesianGdp(Math.max(1, parseFloat(e.target.value) || 1))}
                  className="w-full rounded-lg bg-[#111e21] px-3 py-2 text-sm text-white font-mono border border-[#1f373d] focus:outline-none focus:border-teal-500"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Pre-filled with {currentCountryMeta?.name}'s latest nominal GDP.
                </span>
              </div>

              {/* Spending Shock Delta G */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Spending Shock (ΔG in $B):</span>
                  <span className="font-mono font-bold text-teal-300">
                    {deltaG > 0 ? `+` : ''}${deltaG.toLocaleString()}B
                  </span>
                </div>
                <input
                  type="range"
                  min="-1000"
                  max="2000"
                  step="25"
                  value={deltaG}
                  onChange={(e) => setDeltaG(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Autonomous government expenditure shock injected into goods market.
                </span>
              </div>

              {/* MPC Slider */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Marginal Propensity to Consume (MPC):</span>
                  <span className="font-mono font-bold text-teal-300">{mpc.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.95"
                  step="0.01"
                  value={mpc}
                  onChange={(e) => setMpc(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Share of each additional dollar spent by households (0 &lt; MPC &lt; 1).
                </span>
              </div>

              {/* Optional Leakage 1: Tax Rate */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Proportional Tax Rate (t):</span>
                  <span className="font-mono font-bold text-slate-300">{(taxRate * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.40"
                  step="0.05"
                  value={taxRate}
                  onChange={(e) => setTaxRate(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Optional leakage: income taxes reduce induced disposable income.
                </span>
              </div>

              {/* Optional Leakage 2: Import Propensity */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Import Propensity (m):</span>
                  <span className="font-mono font-bold text-slate-300">
                    {(importPropensity * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="0.30"
                  step="0.02"
                  value={importPropensity}
                  onChange={(e) => setImportPropensity(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Optional leakage: spending diverted to foreign imports.
                </span>
              </div>
            </div>
          </section>

          {/* Results Grid (4 KPIs) */}
          <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-xl border border-teal-500/40 bg-[#0e1b1e] p-5">
              <span className="text-[11px] font-semibold text-teal-300 uppercase tracking-wider">
                Expenditure Multiplier (k)
              </span>
              <div className="text-3xl font-extrabold text-white font-mono mt-1">
                {keynesianResult.results.active_multiplier.toFixed(2)}x
              </div>
              <span className="text-[10px] text-slate-400 font-mono">
                MPS = {keynesianResult.results.mps.toFixed(2)}
              </span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Output Expansion (ΔY)
              </span>
              <div className="text-3xl font-extrabold text-white font-mono mt-1">
                {keynesianResult.results.delta_y > 0 ? `+` : ''}$
                {keynesianResult.results.delta_y.toLocaleString()}B
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Total Cumulative Impact</span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Simulated Output (Y₁)
              </span>
              <div className="text-3xl font-extrabold text-teal-300 font-mono mt-1">
                ${keynesianResult.results.simulated_gdp.toLocaleString()}B
              </div>
              <span className="text-[10px] text-slate-400 font-mono">New Equilibrium National Income</span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Percentage Change
              </span>
              <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-1">
                {keynesianResult.results.percent_change > 0 ? `+` : ''}
                {keynesianResult.results.percent_change.toFixed(2)}%
              </div>
              <span className="text-[10px] text-slate-400 font-mono">vs Baseline Economy</span>
            </div>
          </section>

          {/* Sequential Round-by-Round Propagation Chart & Table */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Round-by-Round Consumption Multiplier Ripple (Rounds 1–10)
            </h3>
            <p className="text-xs text-slate-400">
              Each round induces consumer spending equal to the effective MPC multiplied by the previous round's income.
            </p>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={keynesianResult.round_breakdown} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                  <XAxis dataKey="round" stroke="#64748b" fontSize={11} label={{ value: 'Economic Round', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 11 }} />
                  <YAxis stroke="#64748b" fontSize={11} unit=" $B" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0c1618',
                      borderColor: '#1d353b',
                      borderRadius: '8px',
                      color: '#e2e8f0',
                      fontSize: '12px',
                    }}
                    formatter={(val: any) => [`$${Number(val).toFixed(2)}B`, 'Round Addition']}
                  />
                  <Bar dataKey="round_addition" name="Addition to GDP ($B)" fill="#0d9488" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Breakdown Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0b1416] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1b2f34]">
                  <tr>
                    <th className="py-2 px-3">Round</th>
                    <th className="py-2 px-3">Economic Stage</th>
                    <th className="py-2 px-3 text-right">Round Addition ($B)</th>
                    <th className="py-2 px-3 text-right">Cumulative Expansion ($B)</th>
                    <th className="py-2 px-3 text-right">% Realized</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#152528]">
                  {keynesianResult.round_breakdown.map((r) => (
                    <tr key={r.round} className="hover:bg-[#122226]">
                      <td className="py-2 px-3 text-slate-400">Round {r.round}</td>
                      <td className="py-2 px-3 font-sans text-slate-300">{r.description}</td>
                      <td className="py-2 px-3 text-right text-teal-300 font-bold">
                        ${r.round_addition.toFixed(2)}B
                      </td>
                      <td className="py-2 px-3 text-right text-white">
                        ${r.cumulative_output.toFixed(2)}B
                      </td>
                      <td className="py-2 px-3 text-right text-emerald-400">{r.percent_realized}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Narrative & Assumptions Disclaimers */}
          <div className="rounded-xl border border-[#1b2f34] bg-[#0c1618] p-5 text-xs text-slate-300 leading-relaxed space-y-3">
            <div>
              <h4 className="font-bold text-teal-300 text-sm mb-1">Economic Mechanism Narrative:</h4>
              <p>{keynesianResult.explanation}</p>
            </div>
            <div className="border-t border-[#1a2f33] pt-3 text-[11px] text-slate-400 flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>{keynesianResult.assumptions_disclaimer}</span>
            </div>
          </div>
        </div>
      )}

      {/* MODULE B: IS–LM EQUILIBRIUM POLICY SIMULATOR */}
      {activeTab === 'islm' && islmResult && (
        <div className="space-y-6">
          {/* Preset Policy Scenarios Bar */}
          <div className="rounded-xl border border-[#1d3338] bg-[#0d171a] p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Preset Scenarios:
            </span>
            <div className="flex flex-wrap gap-2">
              {islmResult.preset_scenarios.map((sc) => (
                <button
                  key={sc.id}
                  onClick={() => applyISLMPreset(sc)}
                  className="px-3 py-1.5 rounded-lg bg-[#112023] border border-[#1e383e] text-xs font-semibold text-slate-200 hover:border-teal-500 hover:bg-teal-950/60 transition-colors"
                >
                  {sc.name}
                </button>
              ))}
              <button
                onClick={resetISLM}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a2225] text-xs font-medium text-slate-400 hover:text-white transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Reset
              </button>
            </div>
          </div>

          {/* Shock Controls & Sliders */}
          <section className="rounded-2xl border border-[#1d3338] bg-[#0d171a] p-5 shadow-xl space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 border-b border-[#182b2f] pb-3">
              Policy Shocks & Behavioral Parameters
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Interest Rate Shock */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Policy Rate Shock (Δr):</span>
                  <span className="font-mono font-bold text-teal-300">
                    {deltaR > 0 ? `+` : ''}{deltaR.toFixed(2)}% pts
                  </span>
                </div>
                <input
                  type="range"
                  min="-3.0"
                  max="4.0"
                  step="0.25"
                  value={deltaR}
                  onChange={(e) => setDeltaR(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Central bank moves target policy rate (r₁* = r₀* + Δr).
                </span>
              </div>

              {/* Fiscal Shock */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Fiscal Spending Shock (ΔG):</span>
                  <span className="font-mono font-bold text-teal-300">
                    {deltaFiscalG > 0 ? `+` : ''}{deltaFiscalG} units
                  </span>
                </div>
                <input
                  type="range"
                  min="-300"
                  max="500"
                  step="25"
                  value={deltaFiscalG}
                  onChange={(e) => setDeltaFiscalG(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Shifts Goods-Market (IS) curve rightward (+ΔG) or leftward (−ΔG).
                </span>
              </div>

              {/* Investment Sensitivity b */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Investment Sensitivity (b):</span>
                  <span className="font-mono font-bold text-slate-300">{paramB}</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={paramB}
                  onChange={(e) => setParamB(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Slope of IS curve: dI/dr responsiveness.
                </span>
              </div>

              {/* Speculative Money Demand h */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="text-slate-300 font-medium">Liquidity Preference (h):</span>
                  <span className="font-mono font-bold text-slate-300">{paramH}</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={paramH}
                  onChange={(e) => setParamH(parseFloat(e.target.value))}
                  className="w-full accent-teal-500 cursor-pointer"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Slope of LM curve: speculative demand dL/dr.
                </span>
              </div>
            </div>
          </section>

          {/* Equilibrium Before-and-After KPI Grid */}
          <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Equilibrium Output (Y)
              </span>
              <div className="text-2xl font-bold text-white font-mono mt-1">
                {islmResult.policy.y.toFixed(1)}
              </div>
              <div className="text-[11px] font-mono mt-1 text-slate-400">
                Baseline Y₀*: {islmResult.baseline.y.toFixed(1)} (
                <span className={islmResult.deltas.delta_y >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                  {islmResult.deltas.delta_y > 0 ? `+` : ''}{islmResult.deltas.delta_y}
                </span>)
              </div>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Equilibrium Rate (r)
              </span>
              <div className="text-2xl font-bold text-teal-300 font-mono mt-1">
                {islmResult.policy.r.toFixed(2)}%
              </div>
              <div className="text-[11px] font-mono mt-1 text-slate-400">
                Baseline r₀*: {islmResult.baseline.r.toFixed(2)}% (
                <span className={islmResult.deltas.delta_r >= 0 ? 'text-amber-400' : 'text-emerald-400'}>
                  {islmResult.deltas.delta_r > 0 ? `+` : ''}{islmResult.deltas.delta_r}%
                </span>)
              </div>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Planned Investment (ΔI)
              </span>
              <div className="text-2xl font-bold text-white font-mono mt-1">
                {islmResult.deltas.delta_i > 0 ? `+` : ''}{islmResult.deltas.delta_i.toFixed(1)}
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Interest Sensitivity Channel</span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Endogenous Money Supply (M)
              </span>
              <div className="text-2xl font-bold text-indigo-300 font-mono mt-1">
                {islmResult.policy.m_implied.toFixed(1)}
              </div>
              <div className="text-[11px] font-mono mt-1 text-slate-400">
                ΔM = {islmResult.deltas.delta_m > 0 ? `+` : ''}{islmResult.deltas.delta_m.toFixed(1)}
              </div>
            </div>
          </section>

          {/* Interactive IS–LM Curves Visualization */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  IS–LM Goods & Money Market Equilibrium Diagram
                </h3>
                <p className="text-xs text-slate-400">
                  Goods Market (IS) vs. Money Market (LM) shifts under policy rate shock Δr and fiscal shock ΔG
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400"></span> IS Baseline
                </span>
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-400"></span> IS Policy
                </span>
                <span className="flex items-center gap-1.5 text-indigo-400">
                  <span className="h-2 w-2 rounded-full bg-indigo-400"></span> LM Baseline
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="h-2 w-2 rounded-full bg-rose-400"></span> LM Policy
                </span>
              </div>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={islmResult.curve_points} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                  <XAxis dataKey="y" type="number" stroke="#64748b" fontSize={11} label={{ value: 'Equilibrium National Income (Y)', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 11 }} />
                  <YAxis stroke="#64748b" fontSize={11} unit="%" label={{ value: 'Interest Rate (r %)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
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
                    dataKey="is_baseline"
                    name="IS Curve (Baseline)"
                    stroke="#14b8a6"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="is_policy"
                    name="IS Curve (Policy)"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="lm_baseline"
                    name="LM Curve (Baseline)"
                    stroke="#818cf8"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="lm_policy"
                    name="LM Curve (Policy Shift)"
                    stroke="#f43f5e"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Step-by-Step Monetary Transmission Mechanism */}
          <section className="rounded-xl border border-[#1d3338] bg-[#0d171a] p-5 shadow-lg space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-teal-300">
              Macroeconomic Transmission Channels:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {islmResult.transmission_steps.map((st) => (
                <div key={st.step} className="p-3 rounded-lg bg-[#111e21] border border-[#1a2e33] text-xs">
                  <div className="font-bold text-white mb-1">{st.title}</div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">{st.description}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-[#182b2f] pt-3 text-[11px] text-slate-400 flex items-start gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>{islmResult.assumptions_disclaimer}</span>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
