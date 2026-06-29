import { motion, AnimatePresence } from 'framer-motion'
import { Lightbulb, AlertTriangle, Brain, Flame, RotateCcw, Search } from 'lucide-react'
import type { ThinkingStreamEvent } from '../types'

interface Props {
  events: ThinkingStreamEvent[]
}

const emotionConfig: Record<string, { icon: typeof Lightbulb; color: string; label: string }> = {
  '💡': { icon: Lightbulb, color: 'text-gold-400', label: '顿悟' },
  '⚡': { icon: AlertTriangle, color: 'text-orange-400', label: '警醒' },
  '🤔': { icon: Brain, color: 'text-blue-400', label: '沉思' },
  '💪': { icon: Flame, color: 'text-red-400', label: '坚定' },
  '🔄': { icon: RotateCcw, color: 'text-gray-400', label: '回退' },
  '🔍': { icon: Search, color: 'text-purple-400', label: '搜索' },
}

export default function ThinkingStream({ events }: Props) {
  // Show last 15 events
  const displayEvents = events.slice(-15)

  return (
    <div className="bg-dark-800/40 border border-mao-800/30 rounded-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-mao-800/20 flex items-center gap-2">
        <Brain className="w-4 h-4 text-mao-400" />
        <span className="text-xs text-gray-400 font-medium">思考流</span>
        {events.length > 0 && (
          <span className="text-xs text-mao-500 ml-auto">{events.length} 步</span>
        )}
      </div>
      <div className="p-3 space-y-1 max-h-60 overflow-y-auto">
        <AnimatePresence initial={false}>
          {displayEvents.map((event) => {
            const config = emotionConfig[event.emotion] || emotionConfig['🤔']
            const Icon = config.icon

            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: event.is_revert ? 0.4 : 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.3 }}
                className={`flex items-start gap-2 py-1 ${
                  event.is_revert ? 'line-through text-gray-600' : 'text-gray-400'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${config.color}`} />
                <span className="text-xs leading-relaxed">{event.text}</span>
              </motion.div>
            )
          })}
        </AnimatePresence>
        {events.length === 0 && (
          <div className="text-xs text-gray-600 text-center py-4">等待思考...</div>
        )}
      </div>
    </div>
  )
}
