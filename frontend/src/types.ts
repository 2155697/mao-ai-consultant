export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface ThinkingStreamEvent {
  id: string
  text: string
  emotion: string
  is_revert: boolean
  timestamp: string
}

export interface CognitiveNode {
  id: string
  label: string
  type: string
  color: string
  confidence: number
}

export interface CognitiveGraph {
  nodes: CognitiveNode[]
  edges: {from: string, to: string}[]
}

export interface MaoQuote {
  text: string
  source: string
  date?: string
}

export interface ChatChunk {
  type: 'thinking_stream' | 'cognitive_structure' | 'mao_quote' | 'content' | 'done' | 'error'
  data?: string
  thinking_step?: {
    id: string
    name: string
    content?: string
    status?: string
  }
}
