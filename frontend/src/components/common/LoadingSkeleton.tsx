import React from 'react'

export const LoadingSkeleton: React.FC<{ count?: number; className?: string }> = ({
  count = 4,
  className = 'h-32',
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`rounded-xl border border-[#1d3237] bg-[#111e21]/60 ${className} p-5 flex flex-col justify-between`}
        >
          <div className="flex justify-between items-center">
            <div className="h-3 w-24 bg-slate-800 rounded"></div>
            <div className="h-3 w-10 bg-slate-800 rounded"></div>
          </div>
          <div className="h-8 w-36 bg-slate-700/60 rounded"></div>
          <div className="h-2 w-full bg-slate-800/80 rounded"></div>
        </div>
      ))}
    </div>
  )
}
