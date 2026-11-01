import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-6 text-center my-6">
      <div className="flex justify-center mb-3">
        <div className="rounded-full bg-rose-900/30 p-3 text-rose-400">
          <AlertCircle className="w-6 h-6" />
        </div>
      </div>
      <h3 className="text-base font-semibold text-rose-200 mb-1">Economic Intelligence Notice</h3>
      <p className="text-sm text-rose-300/80 max-w-lg mx-auto mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-500 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  )
}
