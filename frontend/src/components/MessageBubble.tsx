import { motion } from 'framer-motion'
import { User, Bot } from 'lucide-react'
import type { ChatMessage } from '../types'

interface Props {
  message: ChatMessage
  isLatest?: boolean
}

export default function MessageBubble({ message, isLatest }: Props) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
          isUser
            ? 'bg-dark-700'
            : 'bg-gradient-to-br from-mao-700 to-mao-900'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-gray-400" />
        ) : (
          <Bot className="w-4 h-4 text-gold-400" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-dark-700 text-gray-200 rounded-tr-sm'
            : 'bg-dark-800/80 border border-mao-800/30 text-gray-100 rounded-tl-sm'
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
          {isLatest && !isUser && (
            <span className="inline-block w-0.5 h-4 bg-mao-500 ml-0.5 animate-pulse" />
          )}
        </p>
      </div>
    </motion.div>
  )
}
