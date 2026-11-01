import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  ReferenceLine,
} from 'recharts'
import {
  Brain,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { runRidgeForecast } from '../../services/api'
import type { RidgeForecastResult } from '../../types'
import { LoadingSkeleton } from '../common/LoadingSkeleton'
import { ErrorMessage } from '../common/ErrorMessage'

export const InflationForecastView: React.FC = () => {
  const { selectedCountry, currentCountryMeta } = useApp()
  const [result, setResult] = useState<RidgeForecastResult | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Tunable ML hyperparameters
  const [alpha, setAlpha] = useState<number>(1.0)
  const [testRatio, setTestRatio] = useState<number>(0.20)
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([
    'inflation_lag',
    'unemployment',
    'gdp_growth',
    'interest_rate',
  ])

  const loadForecast = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await runRidgeForecast({
        country_code: selectedCountry,
        alpha,
        test_ratio: testRatio,
        features: selectedFeatures,
      })
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Failed to calibrate Ridge regression model')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadForecast()
  }, [selectedCountry])

  const toggleFeature = (feat: string) => {
    if (selectedFeatures.includes(feat)) {
      if (selectedFeatures.length > 1) {
        setSelectedFeatures(selectedFeatures.filter((f) => f !== feat))
      }
    } else {
      setSelectedFeatures([...selectedFeatures, feat])
    }
  }

  if (loading && !result) {
    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto">
        <LoadingSkeleton count={4} />
      </div>
    )
  }

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1b2f34] pb-6">
        <div>
          <div className="flex items-center gap-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Brain className="w-4 h-4" />
            <span>Phillips Curve Econometrics & Regularized Machine Learning</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Inflation Forecasting Studio
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Forecasts next-period inflation using a Phillips Curve-inspired feature set calibrated via{' '}
            <b className="text-teal-300">Ridge Regression (L₂ Regularization)</b> with strictly
            chronological holdout evaluation.
          </p>
        </div>

        {/* Country Badge */}
        <div className="flex items-center gap-2 self-start md:self-auto bg-[#0d1618] px-3.5 py-2 rounded-xl border border-[#1b2f34] text-xs">
          <span className="text-lg">{currentCountryMeta?.flag}</span>
          <span className="font-bold text-white">{currentCountryMeta?.name}</span>
          <span className="rounded bg-teal-950 px-1.5 py-0.5 text-[10px] font-mono text-teal-400 border border-teal-800/40">
            {result?.frequency || 'Quarterly'}
          </span>
        </div>
      </div>

      {/* Frequency / Annual Warning if applicable */}
      {result && !result.is_quarterly_native && (
        <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4 text-xs text-amber-200 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Econometric Frequency Integrity Notice:</span>{' '}
            {result.frequency_disclaimer}
          </div>
        </div>
      )}

      {error && <ErrorMessage message={error} onRetry={loadForecast} />}

      {/* Hyperparameter Controls & Feature Selection */}
      <section className="rounded-2xl border border-[#1d3338] bg-[#0d171a] p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-[#182b2f] pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-teal-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Interactive Model Controls & Hyperparameters
            </h3>
          </div>
          <button
            onClick={loadForecast}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-teal-500 disabled:opacity-50 transition-colors shadow-sm"
          >
            {loading ? 'Re-calibrating...' : 'Re-Calibrate Model'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Regularization Lambda (Alpha) */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-300 font-medium">L₂ Penalty λ (Alpha):</span>
              <span className="font-mono font-bold text-teal-300">{alpha.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.01"
              max="20.0"
              step="0.1"
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">
              Higher λ shrinks coefficients to curb collinearity and stabilize variance.
            </span>
          </div>

          {/* Test Split Ratio */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="text-slate-300 font-medium">Holdout Test Split:</span>
              <span className="font-mono font-bold text-teal-300">{Math.round(testRatio * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.35"
              step="0.05"
              value={testRatio}
              onChange={(e) => setTestRatio(parseFloat(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block mt-1">
              Strictly chronological holdout without random shuffling (zero data leakage).
            </span>
          </div>

          {/* Feature Selector */}
          <div>
            <span className="block text-xs text-slate-300 font-medium mb-1.5">
              Predictor Features (Observed at t):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {[
                { id: 'inflation_lag', label: 'Lagged Inflation (π_t)' },
                { id: 'unemployment', label: 'Unemployment (u_t)' },
                { id: 'gdp_growth', label: 'GDP Growth (%_t)' },
                { id: 'interest_rate', label: 'Interest Rate (i_t)' },
              ].map((feat) => {
                const isSelected = selectedFeatures.includes(feat.id)
                return (
                  <button
                    key={feat.id}
                    onClick={() => toggleFeature(feat.id)}
                    className={`px-2 py-1 text-[11px] rounded font-medium border transition-colors ${
                      isSelected
                        ? 'bg-teal-950 text-teal-300 border-teal-600/60'
                        : 'bg-[#101e21] text-slate-400 border-[#1f373d]'
                    }`}
                  >
                    {feat.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      {result && (
        <>
          {/* Point Forecast Banner */}
          <div className="rounded-2xl border border-teal-500/40 bg-gradient-to-r from-[#0c181a] via-[#102428] to-[#0c191c] p-6 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-300">
                  Target Forecast Horizon
                </span>
                <span className="rounded bg-teal-950 px-2 py-0.5 text-xs font-mono font-bold text-teal-400 border border-teal-800/50">
                  {result.next_forecast.target_period}
                </span>
              </div>
              <div className="flex items-baseline gap-3 my-2">
                <span className="text-4xl sm:text-5xl font-black text-white font-mono">
                  {result.next_forecast.point_forecast !== null
                    ? `${result.next_forecast.point_forecast.toFixed(2)}%`
                    : 'N/A'}
                </span>
                <span className="text-sm font-semibold text-teal-300">Point Forecast</span>
              </div>
              <div className="text-xs text-slate-300">
                95% Empirical Prediction Interval:{' '}
                <b className="font-mono text-emerald-300">
                  [{result.next_forecast.confidence_95.low.toFixed(2)}% –{' '}
                  {result.next_forecast.confidence_95.high.toFixed(2)}%]
                </b>{' '}
                <span className="text-slate-400 font-mono">(± {result.next_forecast.confidence_95.margin_error.toFixed(2)}% points)</span>
              </div>
            </div>

            {/* Outperformance Check */}
            <div className="bg-[#0b1416] p-4 rounded-xl border border-[#1b2f34] flex flex-col justify-center min-w-[240px]">
              <div className="text-xs font-semibold text-slate-400 mb-1">
                Out-of-Sample Performance:
              </div>
              <div className="flex items-center gap-2">
                {result.metrics.beats_baseline ? (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" /> Beats Persistence Baseline
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-400">
                    <AlertTriangle className="w-4 h-4" /> Meets Naive Persistence
                  </span>
                )}
              </div>
              <div className="text-[11px] text-slate-500 mt-1 font-mono">
                Ridge RMSE: {result.metrics.test_rmse} | Naive: {result.metrics.baseline_rmse}
              </div>
            </div>
          </div>

          {/* Model Evaluation Metrics Grid */}
          <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Out-of-Sample MAE
              </span>
              <div className="text-2xl font-bold text-white font-mono mt-1">
                {result.metrics.test_mae.toFixed(3)}%
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Baseline: {result.metrics.baseline_mae.toFixed(3)}%</span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Out-of-Sample RMSE
              </span>
              <div className="text-2xl font-bold text-white font-mono mt-1">
                {result.metrics.test_rmse.toFixed(3)}%
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Baseline: {result.metrics.baseline_rmse.toFixed(3)}%</span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Test Out-of-Sample R²
              </span>
              <div className="text-2xl font-bold text-white font-mono mt-1">
                {result.metrics.test_r2.toFixed(3)}
              </div>
              <span className="text-[10px] text-slate-500">Unseen Holdout Partition</span>
            </div>

            <div className="rounded-xl border border-[#1d3237] bg-[#111e21] p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Sample Size & Split
              </span>
              <div className="text-2xl font-bold text-teal-300 font-mono mt-1">
                {result.metrics.total_observations} obs
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                Train: {result.metrics.train_size} | Test: {result.metrics.test_size}
              </span>
            </div>
          </section>

          {/* Chart 1: Actual vs Ridge Predicted across Chronological Splits */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Actual vs. Ridge Predicted Inflation Trajectory
                </h3>
                <p className="text-xs text-slate-400">
                  Chronological progression across In-Sample Training, Out-of-Sample Testing, and Next-Period Forecast Point
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-white">
                  <span className="h-2 w-2 rounded-full bg-white"></span> Actual Inflation (%)
                </span>
                <span className="flex items-center gap-1.5 text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400"></span> Ridge Model (Predicted)
                </span>
              </div>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.chart_data} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                  <XAxis dataKey="label" stroke="#64748b" fontSize={11} interval="preserveStartEnd" />
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
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual Inflation"
                    stroke="#ffffff"
                    strokeWidth={2}
                    dot={{ r: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    name="Ridge Prediction"
                    stroke="#14b8a6"
                    strokeWidth={2.5}
                    dot={{ r: 2 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Chart 2: Standardized Feature Coefficients & Roles */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">
              Standardized Feature Coefficients (Empirical Weights)
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Standardized weights show directional sensitivity. Ridge penalty λ shrinks correlated coefficients toward zero.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
              {/* Bar Chart */}
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={result.coefficients} layout="vertical" margin={{ top: 10, right: 30, left: 40, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                    <XAxis type="number" stroke="#64748b" fontSize={11} />
                    <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={10} width={120} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0c1618',
                        borderColor: '#1d353b',
                        borderRadius: '8px',
                        color: '#e2e8f0',
                        fontSize: '12px',
                      }}
                    />
                    <ReferenceLine x={0} stroke="#64748b" />
                    <Bar dataKey="coefficient" name="Coefficient (β)" fill="#0d9488" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Economic Roles Table */}
              <div className="space-y-2">
                {result.coefficients.map((c) => (
                  <div key={c.feature} className="p-3 rounded-lg bg-[#0b1416] border border-[#1b2f34] text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-white">{c.name}</span>
                      <span
                        className={`font-mono font-bold ${
                          c.coefficient > 0 ? 'text-amber-400' : 'text-indigo-400'
                        }`}
                      >
                        β = {c.coefficient > 0 ? `+${c.coefficient}` : c.coefficient}
                      </span>
                    </div>
                    <div className="text-[11px] text-teal-400 font-medium mb-0.5">{c.role}</div>
                    <p className="text-[11px] text-slate-400 leading-tight">{c.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Chart 3: Empirical Phillips Curve Scatter */}
          <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Empirical Phillips Curve Trade-Off (Unemployment vs. Inflation)
                </h3>
                <p className="text-xs text-slate-400">
                  Scatter observations with fitted Ordinary Least Squares (OLS) regression line
                </p>
              </div>
              <span className="text-xs font-mono text-teal-300 bg-teal-950 px-2 py-1 rounded border border-teal-800/40">
                OLS Slope: β = {result.phillips_curve.ols_slope}
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#182c30" />
                  <XAxis dataKey="unemployment" name="Unemployment" unit="%" stroke="#64748b" fontSize={11} label={{ value: 'Unemployment Rate (u %)', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 11 }} />
                  <YAxis dataKey="inflation" name="Inflation" unit="%" stroke="#64748b" fontSize={11} label={{ value: 'CPI Inflation (π %)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0c1618',
                      borderColor: '#1d353b',
                      borderRadius: '8px',
                      color: '#e2e8f0',
                      fontSize: '12px',
                    }}
                    cursor={{ strokeDasharray: '3 3' }}
                  />
                  <Scatter name="Historical Observations" data={result.phillips_curve.scatter} fill="#14b8a6" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            {/* Lucas Critique Disclaimer */}
            <div className="mt-4 flex items-start gap-2.5 rounded-lg bg-[#0b1416] p-3 text-xs text-slate-400 border border-[#1a2f34]">
              <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <b className="text-slate-300">Methodological Caution (Lucas Critique & Friedman-Phelps):</b>{' '}
                {result.phillips_curve.interpretation}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
