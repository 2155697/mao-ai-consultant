import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'
import type { MaoQuote } from '../types'

interface Props {
  quotes: MaoQuote[]
}

export default function MaoQuoteCard({ quotes }: Props) {
  if (quotes.length === 0) return null

  return (
    <div className="space-y-2">
      {quotes.map((quote, index) => (
        <motion.div
          key={`${quote.text}-${index}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-gradient-to-br from-mao-900/60 to-dark-800/80 
                     border border-mao-700/30 rounded-lg p-4"
        >
          <div className="flex items-start gap-3">
            <BookOpen className="w-5 h-5 text-gold-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-gold-400/90 italic font-serif text-sm leading-relaxed">
                "{quote.text}"
              </p>
              {quote.source && (
                <p className="text-gray-500 text-xs mt-2">
                  ——{quote.source}
                  {quote.date && ` · ${quote.date}`}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
