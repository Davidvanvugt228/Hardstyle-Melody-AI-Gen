'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore, Style, Energy } from '@/lib/store'
import { api, downloadBlob } from '@/lib/api'

export default function ConfigPanel() {
  const {
    phase, style, energy, bars,
    setStyle, setEnergy, setBars,
    setPhase, setResult, setError,
    midiFile,
  } = useAppStore()

  const isVisible = ['analyzed', 'generating', 'done', 'error'].includes(phase) &&
    useAppStore.getState().analysis !== null

  const handleGenerate = async () => {
    if (!midiFile) return
    setPhase('generating')
    setError(null)

    try {
      const { blob, sessionId } = await api.generateMidi(midiFile, { style, energy, bars })
      const downloadUrl = URL.createObjectURL(blob)
      setResult({
        downloadUrl,
        sessionId,
        metadata: {
          bpm: useAppStore.getState().analysis?.bpm || 160,
          key: useAppStore.getState().analysis?.key || 'Unknown',
          style,
          energy,
          bars_generated: bars,
          melody_pattern: '',
          chord_progression: '',
        },
      })
      setPhase('done')
    } catch (err: any) {
      setError(err.message || 'Generation failed')
      setPhase('error')
    }
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.section
          key="config"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 px-6 pb-8"
          id="configure"
        >
          <div className="max-w-2xl mx-auto space-y-6">

            {/* Section label */}
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent to-raw-orange/30" />
              <span className="font-mono text-xs tracking-[0.25em] text-raw-orange/70 uppercase">
                02 / Configure
              </span>
              <div className="h-px flex-1 bg-gradient-to-l from-transparent to-raw-orange/30" />
            </div>

            {/* Style Selector */}
            <div>
              <label className="font-mono text-xs tracking-widest text-chrome/50 uppercase mb-3 block">
                Genre Style
              </label>
              <div className="grid grid-cols-2 gap-3">
                {([
                  {
                    id: 'rawstyle' as Style,
                    name: 'RAWSTYLE',
                    desc: 'Dark · Distorted · Aggressive',
                    accent: 'raw',
                  },
                  {
                    id: 'euphoric' as Style,
                    name: 'EUPHORIC',
                    desc: 'Uplifting · Melodic · Emotional',
                    accent: 'euphoric',
                  },
                ] as const).map(({ id, name, desc, accent }) => (
                  <StyleCard
                    key={id}
                    id={id}
                    name={name}
                    desc={desc}
                    accent={accent}
                    selected={style === id}
                    onSelect={() => setStyle(id)}
                  />
                ))}
              </div>
            </div>

            {/* Energy Selector */}
            <div>
              <label className="font-mono text-xs tracking-widest text-chrome/50 uppercase mb-3 block">
                Energy Level
              </label>
              <div className="grid grid-cols-4 gap-2">
                {(
                  style === 'rawstyle'
                    ? [
                        { id: 'dark' as Energy, label: 'DARK', intensity: 3 },
                        { id: 'aggressive' as Energy, label: 'AGGRO', intensity: 4 },
                      ]
                    : [
                        { id: 'medium' as Energy, label: 'MED', intensity: 2 },
                        { id: 'high' as Energy, label: 'HIGH', intensity: 4 },
                      ]
                ).map(({ id, label, intensity }) => (
                  <EnergyButton
                    key={id}
                    id={id}
                    label={label}
                    intensity={intensity}
                    selected={energy === id}
                    onSelect={() => setEnergy(id)}
                  />
                ))}
              </div>
            </div>

            {/* Bars Selector */}
            <div>
              <label className="font-mono text-xs tracking-widest text-chrome/50 uppercase mb-3 block">
                Length (Bars)
              </label>
              <div className="flex gap-2">
                {[4, 8, 16, 32].map((b) => (
                  <button
                    key={b}
                    onClick={() => setBars(b)}
                    className={`
                      flex-1 py-2.5 rounded-lg font-mono text-sm font-bold
                      border transition-all duration-200
                      ${bars === b
                        ? 'border-raw-orange/60 bg-raw-orange/10 text-raw-orange'
                        : 'border-white/10 bg-white/3 text-chrome/50 hover:border-white/20 hover:text-chrome'
                      }
                    `}
                  >
                    {b}
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <GenerateButton
              phase={phase}
              onGenerate={handleGenerate}
            />

          </div>
        </motion.section>
      )}
    </AnimatePresence>
  )
}

function StyleCard({
  id, name, desc, accent, selected, onSelect,
}: {
  id: string
  name: string
  desc: string
  accent: 'raw' | 'euphoric'
  selected: boolean
  onSelect: () => void
}) {
  const isRaw = accent === 'raw'
  return (
    <motion.button
      onClick={onSelect}
      whileTap={{ scale: 0.98 }}
      className={`
        relative overflow-hidden rounded-xl border p-4 text-left
        transition-all duration-300 group
        ${selected
          ? isRaw
            ? 'border-raw-orange/60 bg-raw-orange/8 glow-raw'
            : 'border-euphoric-cyan/60 bg-euphoric-cyan/8 glow-cyan'
          : 'border-white/10 bg-ash/30 hover:border-white/20'
        }
      `}
    >
      {/* Selected indicator */}
      <div className={`
        absolute top-3 right-3 w-2 h-2 rounded-full transition-all duration-300
        ${selected
          ? isRaw ? 'bg-raw-orange' : 'bg-euphoric-cyan'
          : 'bg-white/20'
        }
      `} />

      {/* Bars decoration */}
      <div className="flex items-end gap-0.5 mb-3 h-6">
        {(isRaw ? [0.4, 1, 0.6, 0.9, 0.3, 0.7] : [0.3, 0.6, 0.9, 1, 0.7, 0.5]).map((h, i) => (
          <div
            key={i}
            className={`w-1 rounded-sm transition-colors duration-300 ${
              selected
                ? isRaw ? 'bg-raw-orange' : 'bg-euphoric-cyan'
                : 'bg-chrome/30'
            }`}
            style={{ height: `${h * 24}px` }}
          />
        ))}
      </div>

      <div className={`font-display font-bold text-base transition-colors ${selected ? (isRaw ? 'text-raw-orange' : 'text-euphoric-cyan') : 'text-pearl'}`}>
        {name}
      </div>
      <div className="font-mono text-[10px] text-chrome/50 mt-0.5 tracking-wide">
        {desc}
      </div>
    </motion.button>
  )
}

function EnergyButton({
  id, label, intensity, selected, onSelect,
}: {
  id: string
  label: string
  intensity: number
  selected: boolean
  onSelect: () => void
}) {
  return (
    <motion.button
      onClick={onSelect}
      whileTap={{ scale: 0.96 }}
      className={`
        col-span-2 relative rounded-lg border px-4 py-3
        font-mono text-sm font-bold tracking-widest uppercase
        transition-all duration-200
        ${selected
          ? 'border-raw-orange/60 bg-raw-orange/10 text-raw-orange'
          : 'border-white/10 bg-white/3 text-chrome/60 hover:border-white/20 hover:text-chrome'
        }
      `}
    >
      <div className="flex items-center justify-between">
        <span>{label}</span>
        <div className="flex gap-0.5">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className={`w-1 h-3 rounded-sm ${
                i < intensity
                  ? selected ? 'bg-raw-orange' : 'bg-chrome/40'
                  : 'bg-white/10'
              }`}
            />
          ))}
        </div>
      </div>
    </motion.button>
  )
}

function GenerateButton({ phase, onGenerate }: { phase: string; onGenerate: () => void }) {
  const isGenerating = phase === 'generating'
  const isDone = phase === 'done'

  return (
    <motion.button
      onClick={!isGenerating ? onGenerate : undefined}
      disabled={isGenerating}
      whileTap={!isGenerating ? { scale: 0.98 } : undefined}
      className={`
        w-full relative overflow-hidden rounded-xl py-5
        font-display font-bold text-xl tracking-[0.2em] uppercase
        transition-all duration-300 disabled:cursor-not-allowed
        ${isDone
          ? 'border border-raw-orange/40 bg-raw-orange/5 text-raw-orange'
          : 'btn-raw text-white'
        }
      `}
    >
      {/* Shimmer on generating */}
      {isGenerating && (
        <motion.div
          className="absolute inset-0 shimmer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        />
      )}

      <span className="relative z-10 flex items-center justify-center gap-3">
        {isGenerating ? (
          <>
            <GeneratingSpinner />
            <span>GENERATING...</span>
          </>
        ) : isDone ? (
          <span>↺ REGENERATE</span>
        ) : (
          <span>⚡ GENERATE MIDI</span>
        )}
      </span>
    </motion.button>
  )
}

function GeneratingSpinner() {
  return (
    <motion.div
      className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
      animate={{ rotate: 360 }}
      transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
    />
  )
}
