import React, { useState, useEffect } from 'react'
import {
  BookOpen,
  ExternalLink,
  ShieldCheck,
  Code,
  FileText,
  Database,
  GraduationCap,
} from 'lucide-react'
import { fetchMethodology } from '../../services/api'
import { LoadingSkeleton } from '../common/LoadingSkeleton'

export const MethodologyView: React.FC = () => {
  const [methodology, setMethodology] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    fetchMethodology()
      .then((data) => setMethodology(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false))
  }, [])

  if (loading || !methodology) {
    return (
      <div className="space-y-6 p-6 max-w-7xl mx-auto">
        <LoadingSkeleton count={3} />
      </div>
    )
  }

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-[#1b2f34] pb-6">
        <div className="flex items-center gap-2 text-teal-400 text-xs font-semibold uppercase tracking-wider mb-1">
          <BookOpen className="w-4 h-4" />
          <span>Scientific Transparency & Technical Architecture</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Data Sources, Econometric Methodology & Assumptions
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
          Comprehensive documentation of data providers, frequency alignment safeguards, mathematical
          equations, machine learning pipelines, and academic references.
        </p>
      </div>

      {/* Data Taxonomy Legend */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-emerald-900/40 bg-[#0d1c1a] text-xs">
          <span className="font-bold text-emerald-300 block mb-1">1. Observed Live Data</span>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Raw empirical macroeconomic time series fetched directly from FRED and World Bank Open Data APIs.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-teal-900/40 bg-[#0d1a1e] text-xs">
          <span className="font-bold text-teal-300 block mb-1">2. Calculated Derived Metrics</span>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Deterministic economic formulas computed dynamically (Misery Index, Ex-Post Real Interest Rate).
          </p>
        </div>

        <div className="p-4 rounded-xl border border-indigo-900/40 bg-[#121626] text-xs">
          <span className="font-bold text-indigo-300 block mb-1">3. Statistical ML Forecasts</span>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Empirical next-quarter predictions using Ridge Regression with strict chronological holdout splits.
          </p>
        </div>

        <div className="p-4 rounded-xl border border-amber-900/40 bg-[#21190d] text-xs">
          <span className="font-bold text-amber-300 block mb-1">4. Policy Shock Scenarios</span>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Theoretical laboratory simulations (Keynesian Multiplier and IS–LM equilibrium shifts). Not official forecasts.
          </p>
        </div>
      </section>

      {/* Data Providers & Series Codes */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg space-y-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-teal-400" />
          <span>Official Data Providers & Indicator Series Inventory</span>
        </h2>

        {methodology.data_sources.map((src: any) => (
          <div key={src.name} className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-[#182b2f] pb-2">
              <div>
                <span className="font-bold text-white text-sm">{src.name}</span>
                <span className="text-xs text-slate-400 ml-2">({src.organization})</span>
              </div>
              <a
                href={src.api_docs}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-teal-400 hover:text-teal-300 font-semibold"
              >
                Official API Docs <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0b1416] text-slate-400 uppercase text-[10px] tracking-wider border-b border-[#1b2f34]">
                  <tr>
                    <th className="py-2 px-3">Series Code</th>
                    <th className="py-2 px-3">Indicator Description</th>
                    <th className="py-2 px-3 text-right">Update Frequency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#16272b]">
                  {src.series.map((s: any) => (
                    <tr key={s.code} className="hover:bg-[#132326]">
                      <td className="py-2 px-3 text-teal-300 font-bold">{s.code}</td>
                      <td className="py-2 px-3 font-sans text-slate-200">{s.name}</td>
                      <td className="py-2 px-3 text-right text-slate-400">{s.freq}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </section>

      {/* Mathematical Formulations */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <Code className="w-4 h-4 text-teal-400" />
          <span>Mathematical & Econometric Equations</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-[#0b1416] border border-[#1c3237]">
            <span className="text-xs font-bold text-teal-400 block mb-1">
              Arthur Okun's Misery Index:
            </span>
            <code className="text-sm text-white font-mono block bg-[#070e10] p-2.5 rounded border border-[#172b2f]">
              {methodology.formulas.misery_index}
            </code>
            <p className="text-[11px] text-slate-400 mt-2">
              Evaluates stagflationary consumer discomfort by summing headline consumer price inflation and the civilian unemployment rate.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0b1416] border border-[#1c3237]">
            <span className="text-xs font-bold text-teal-400 block mb-1">
              Fisher Real Interest Rate Equation:
            </span>
            <code className="text-sm text-white font-mono block bg-[#070e10] p-2.5 rounded border border-[#172b2f]">
              {methodology.formulas.fisher_real_rate}
            </code>
            <p className="text-[11px] text-slate-400 mt-2">
              Distinguishes theoretical ex-ante borrowing costs (using inflation expectations π^e) from realized ex-post real rates.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0b1416] border border-[#1c3237]">
            <span className="text-xs font-bold text-teal-400 block mb-1">
              Ridge Regression Regularization Objective:
            </span>
            <code className="text-sm text-white font-mono block bg-[#070e10] p-2.5 rounded border border-[#172b2f]">
              {methodology.formulas.ridge_regression}
            </code>
            <p className="text-[11px] text-slate-400 mt-2">
              Applies an L₂ penalty (λΣβⱼ²) to shrink coefficients, stabilizing multicollinear economic regressors and preventing overfitting.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#0b1416] border border-[#1c3237]">
            <span className="text-xs font-bold text-teal-400 block mb-1">
              Keynesian Multiplier & IS-LM Curves:
            </span>
            <code className="text-sm text-white font-mono block bg-[#070e10] p-2.5 rounded border border-[#172b2f]">
              {methodology.formulas.keynesian_multiplier}
            </code>
            <p className="text-[11px] text-slate-400 mt-2">
              Models autonomous expenditure multipliers and goods-market (IS) / money-market (LM) equilibrium shifts.
            </p>
          </div>
        </div>
      </section>

      {/* Methodological Safeguards & Data Integrity */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Econometric Safeguards & Anti-Leakage Protocol</span>
        </h2>
        <ul className="space-y-2 text-xs text-slate-300">
          {methodology.methodological_safeguards.map((item: string, idx: number) => (
            <li key={idx} className="flex items-start gap-2.5 p-2 rounded-lg bg-[#0b1416] border border-[#182b2f]">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-400 mt-1.5 flex-shrink-0"></span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Academic Literature References */}
      <section className="rounded-xl border border-[#1d3338] bg-[#111e21] p-5 shadow-lg space-y-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-teal-400" />
          <span>Academic Literature & Peer-Reviewed References</span>
        </h2>
        <div className="space-y-2">
          {methodology.academic_references.map((ref: string, idx: number) => (
            <div key={idx} className="p-3 rounded-lg bg-[#0b1416] border border-[#1b2f34] text-xs text-slate-300 font-mono">
              <span className="text-teal-400 font-bold mr-2">[{idx + 1}]</span>
              <span className="font-sans">{ref}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Project Presentation Meta */}
      <div className="rounded-2xl border border-teal-800/40 bg-gradient-to-r from-[#0c181a] via-[#102226] to-[#0c191c] p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-teal-400 text-xs font-bold uppercase tracking-wider mb-1">
            <GraduationCap className="w-5 h-5 text-teal-400" />
            <span>Macroeconomics Course Project Review</span>
          </div>
          <h3 className="text-lg font-extrabold text-white">
            EcoSim: Real-Time Economic Data Analytics & Policy Simulation
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Based on the project review presentation <code>EcoSim_Ridge_Regression_Green_Teal_Theme.pptx</code>.
          </p>
        </div>
        <div className="text-right text-xs text-slate-300 font-medium">
          <div><b className="text-white">Rohith Reddy</b> — 24BEC0065</div>
          <div><b className="text-white">Lakshmi Narasimha</b> — 24BEC0645</div>
        </div>
      </div>
    </div>
  )
}
