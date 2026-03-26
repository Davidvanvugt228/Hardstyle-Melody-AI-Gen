import { create } from 'zustand'

export type AppPhase = 'idle' | 'uploaded' | 'analyzing' | 'analyzed' | 'generating' | 'done' | 'error'
export type Style = 'rawstyle' | 'euphoric'
export type Energy = 'dark' | 'aggressive' | 'medium' | 'high'

export interface AnalysisResult {
  bpm: number
  key: string
  scale: string
  total_bars: number
  note_count: number
  detected_style: Style
  key_root: number
}

export interface GenerationResult {
  downloadUrl: string
  sessionId: string
  metadata: {
    bpm: number
    key: string
    style: string
    energy: string
    bars_generated: number
    melody_pattern: string
    chord_progression: string
  }
}

interface AppState {
  // Phase
  phase: AppPhase
  setPhase: (phase: AppPhase) => void

  // File
  midiFile: File | null
  setMidiFile: (file: File | null) => void

  // Analysis
  analysis: AnalysisResult | null
  setAnalysis: (analysis: AnalysisResult | null) => void

  // Generation config
  style: Style
  setStyle: (style: Style) => void
  energy: Energy
  setEnergy: (energy: Energy) => void
  bars: number
  setBars: (bars: number) => void

  // Results
  result: GenerationResult | null
  setResult: (result: GenerationResult | null) => void

  // Error
  error: string | null
  setError: (error: string | null) => void

  // Reset
  reset: () => void
}

export const useAppStore = create<AppState>((set) => ({
  phase: 'idle',
  setPhase: (phase) => set({ phase }),

  midiFile: null,
  setMidiFile: (midiFile) => set({ midiFile }),

  analysis: null,
  setAnalysis: (analysis) => set({ analysis }),

  style: 'rawstyle',
  setStyle: (style) => set({ style }),
  energy: 'aggressive',
  setEnergy: (energy) => set({ energy }),
  bars: 8,
  setBars: (bars) => set({ bars }),

  result: null,
  setResult: (result) => set({ result }),

  error: null,
  setError: (error) => set({ error }),

  reset: () => set({
    phase: 'idle',
    midiFile: null,
    analysis: null,
    result: null,
    error: null,
    style: 'rawstyle',
    energy: 'aggressive',
    bars: 8,
  }),
}))
