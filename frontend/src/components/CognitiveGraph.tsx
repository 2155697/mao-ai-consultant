import { motion } from 'framer-motion'
import { GitBranch } from 'lucide-react'
import type { CognitiveGraph as CognitiveGraphType } from '../types'

interface Props {
  graph: CognitiveGraphType | null
}

const typeColors: Record<string, string> = {
  main_contradiction: 'bg-red-600/30 border-red-500/50 text-red-300',
  breakthrough: 'bg-amber-600/30 border-amber-500/50 text-amber-300',
  insight: 'bg-purple-600/30 border-purple-500/50 text-purple-300',
  conclusion: 'bg-green-600/30 border-green-500/50 text-green-300',
  question: 'bg-gray-600/30 border-gray-500/50 text-gray-300',
}

const typeLabels: Record<string, string> = {
  main_contradiction: '主要矛盾',
  breakthrough: '突破口',
  insight: '洞察',
  conclusion: '结论',
  question: '问题',
}

export default function CognitiveGraphComponent({ graph }: Props) {
  if (!graph || graph.nodes.length === 0) return null

  return (
    <div className="bg-dark-800/40 border border-mao-800/30 rounded-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-mao-800/20 flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-mao-400" />
        <span className="text-xs text-gray-400 font-medium">认知结构</span>
        <span className="text-xs text-gray-600 ml-auto">{graph.nodes.length} 节点</span>
      </div>

      <div className="p-4">
        {/* Node flow */}
        <div className="flex flex-col gap-3">
          {graph.nodes.map((node, index) => {
            const colorClass = typeColors[node.type] || typeColors.question
            const label = typeLabels[node.type] || node.type

            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.15 }}
                className="flex items-center gap-3"
              >
                {/* Connector line */}
                {index > 0 && (
                  <div className="absolute left-6 w-px h-6 bg-mao-700/30 -mt-8" />
                )}

                {/* Node */}
                <div
                  className={`flex-1 rounded-lg border px-3 py-2 ${colorClass}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase tracking-wider opacity-70">
                      {label}
                    </span>
                    {node.confidence > 0 && (
                      <span className="text-[10px] opacity-50 ml-auto">
                        {Math.round(node.confidence * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="text-xs mt-1 font-medium">{node.label}</p>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Edges visualization */}
        {graph.edges.length > 0 && (
          <div className="mt-3 pt-3 border-t border-dark-700/50">
            <div className="flex flex-wrap gap-2">
              {graph.edges.map((edge, i) => (
                <span
                  key={i}
                  className="text-[10px] text-gray-600 bg-dark-900/50 px-2 py-1 rounded"
                >
                  {edge.from} → {edge.to}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
