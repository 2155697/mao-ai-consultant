import { motion } from 'framer-motion'
import { MessageCircle, BookOpen, HelpCircle, Lightbulb } from 'lucide-react'

interface WelcomeScreenProps {
  onQuickAsk: (question: string) => void
}

export default function WelcomeScreen({ onQuickAsk }: WelcomeScreenProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center h-full px-4 py-12"
    >
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.5 }}
        className="w-20 h-20 rounded-full bg-gradient-to-br from-mao-700 to-mao-900 
                   flex items-center justify-center mb-6 shadow-lg shadow-mao-900/30"
      >
        <BookOpen className="w-10 h-10 text-gold-400" />
      </motion.div>

      {/* Greeting */}
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-2xl font-bold text-gray-100 mb-2 text-center"
      >
        小同志，你遇到什么问题，说来听听
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-gray-400 text-center mb-8 max-w-md"
      >
        我是教员，你可以跟我聊聊你遇到的困惑
      </motion.p>

      {/* Quick questions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {[
          { icon: MessageCircle, text: '教员，我最近工作压力大', color: 'bg-mao-900/50 border-mao-700/30' },
          { icon: HelpCircle, text: '遇到困难不知道怎么办', color: 'bg-mao-900/50 border-mao-700/30' },
          { icon: BookOpen, text: '想学习但找不到方向', color: 'bg-mao-900/50 border-mao-700/30' },
          { icon: Lightbulb, text: '做了错事心里过不去', color: 'bg-mao-900/50 border-mao-700/30' },
        ].map((item, index) => (
          <motion.button
            key={item.text}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            onClick={() => onQuickAsk(item.text)}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg border 
                       ${item.color} hover:bg-mao-800/50 transition-colors
                       text-left text-gray-300 hover:text-gray-100`}
          >
            <item.icon className="w-5 h-5 text-gold-400 shrink-0" />
            <span className="text-sm">{item.text}</span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}
