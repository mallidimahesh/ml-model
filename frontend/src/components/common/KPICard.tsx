import React from 'react'
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react'

interface KPICardProps {
  label: string
  value: string | number
  unit?: string
  period?: string
  change?: number
  changeLabel?: string
  source?: string
  coverage?: string
  highlight?: boolean
  tooltip?: string
}

export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  unit,
  period,
  change,
  changeLabel = 'vs prev year',
  source,
  coverage,
  highlight = false,
  tooltip,
}) => {
  return (
    <div
      className={`relative overflow-hidden rounded-xl border p-5 transition-all duration-200 hover:shadow-lg ${
        highlight
          ? 'bg-gradient-to-br from-teal-950/60 via-[#112225] to-[#0c181a] border-teal-500/40 shadow-teal-950/20'
          : 'bg-[#111d20]/90 border-[#1d3237] hover:border-teal-700/50 shadow-black/30'
      }`}
    >
      {/* Top Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">
          {label}
        </span>
        {period && (
          <span className="inline-flex items-center rounded-md bg-teal-950/80 px-2 py-0.5 text-[11px] font-medium text-teal-300 border border-teal-800/40">
            {period}
          </span>
        )}
      </div>

      {/* Primary Value */}
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-2xl font-bold tracking-tight text-white font-mono">
          {value !== null && value !== undefined ? value : '—'}
        </span>
        {unit && <span className="text-xs text-slate-400 font-medium">{unit}</span>}
      </div>

      {/* Delta Indicator */}
      {change !== undefined && change !== null && (
        <div className="flex items-center gap-1.5 text-xs mb-3">
          {change > 0 ? (
            <span className="flex items-center text-emerald-400 font-medium">
              <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
              {change > 0 ? `+${change}` : change}%
            </span>
          ) : change < 0 ? (
            <span className="flex items-center text-rose-400 font-medium">
              <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
              {change}%
            </span>
          ) : (
            <span className="flex items-center text-slate-400 font-medium">
              <Minus className="w-3.5 h-3.5 mr-0.5" /> 0.00%
            </span>
          )}
          <span className="text-slate-500 text-[11px]">{changeLabel}</span>
        </div>
      )}

      {/* Bottom Metadata & Source Tag */}
      {(source || coverage) && (
        <div className="pt-3 border-t border-[#1a2f34] flex items-center justify-between text-[11px] text-slate-500">
          <span className="truncate max-w-[200px]" title={coverage || source}>
            {coverage || source}
          </span>
          {tooltip && (
            <span title={tooltip} className="cursor-help text-slate-400 hover:text-teal-300">
              <Info className="w-3.5 h-3.5" />
            </span>
          )}
        </div>
      )}
    </div>
  )
}
