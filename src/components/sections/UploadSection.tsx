'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'

export default function UploadSection() {
  const { phase, setPhase, setMidiFile, setAnalysis, setError } = useAppStore()
  const [isDragActive, setIsDragActive] = useState(false)

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.match(/\.(mid|midi)$/i)) {
      setError('Please upload a valid MIDI file (.mid or .midi)')
      setPhase('error')
      return
    }

    setMidiFile(file)
    setPhase('analyzing')
    setError(null)

    try {
      const analysis = await api.analyzeMidi(file)
      setAnalysis(analysis)
      // Auto-detect style
      useAppStore.getState().setStyle(analysis.detected_style)
      setPhase('analyzed')
    } catch (err: any) {
      setError(err.message || 'Failed to analyze MIDI file')
      setPhase('error')
    }
  }, [setPhase, setMidiFile, setAnalysis, setError])

  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'audio/midi': ['.mid', '.midi'], 'audio/x-midi': ['.mid', '.midi'] },
    maxFiles: 1,
    onDrop: (accepted) => { if (accepted[0]) handleFile(accepted[0]) },
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    onDropAccepted: () => setIsDragActive(false),
    onDropRejected: () => {
      setIsDragActive(false)
      setError('Invalid file type. Please upload a .mid or .midi file.')
      setPhase('error')
    },
    disabled: ['analyzing', 'generating'].includes(phase),
  })

  return (
    <section className="relative z-10 px-6 py-8" id="upload">
      <div className="max-w-2xl mx-auto">
        {/* Section label */}
        <div className="flex items-center gap-3 mb-6">
          <div className="h-px flex-1 bg-gradient-to-r from-transparent to-raw-orange/30" />
          <span className="font-mono text-xs tracking-[0.25em] text-raw-orange/70 uppercase">
            01 / Upload
          </span>
          <div className="h-px flex-1 bg-gradient-to-l from-transparent to-raw-orange/30" />
        </div>

        <motion.div
          {...(getRootProps() as any)}
          className="relative cursor-pointer group"
          animate={{
            scale: isDragActive ? 1.02 : 1,
          }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <input {...getInputProps()} />

          {/* Drop zone */}
          <div className={`
            relative overflow-hidden rounded-2xl border-2 transition-all duration-300
            ${isDragActive
              ? 'border-raw-orange bg-raw-orange/5 glow-raw'
              : phase === 'analyzed' || phase === 'done'
              ? 'border-raw-orange/40 bg-ash/40'
              : 'border-white/10 bg-ash/20 hover:border-white/20 hover:bg-ash/30'
            }
          `}>
            {/* Grid lines bg */}
            <div className="absolute inset-0 grid-lines opacity-30" />

            {/* Corner decorations */}
            <CornerDeco active={isDragActive} />

            <div className="relative z-10 px-8 py-12 text-center">
              <AnimatePresence mode="wait">
                {phase === 'idle' && (
                  <motion.div
                    key="idle"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <MidiIcon active={isDragActive} />
                    <p className="font-display font-semibold text-2xl text-pearl mt-4 mb-2">
                      {isDragActive ? 'DROP IT' : 'DROP YOUR BASSLINE'}
                    </p>
                    <p className="font-mono text-sm text-chrome/60">
                      .mid / .midi — Drag & drop or click to browse
                    </p>
                    <div className="mt-6 flex justify-center gap-4 text-xs font-mono text-chrome/40">
                      <span>HARDSTYLE READY</span>
                      <span>·</span>
                      <span>FL STUDIO COMPATIBLE</span>
                      <span>·</span>
                      <span>MAX 5MB</span>
                    </div>
                  </motion.div>
                )}

                {phase === 'analyzing' && (
                  <motion.div
                    key="analyzing"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="py-4"
                  >
                    <AnalyzingAnimation />
                    <p className="font-display font-semibold text-xl text-pearl mt-4">
                      ANALYZING BASSLINE
                    </p>
                    <p className="font-mono text-xs text-chrome/50 mt-1">
                      Detecting key, BPM, and pattern structure...
                    </p>
                  </motion.div>
                )}

                {(phase === 'analyzed' || phase === 'generating' || phase === 'done') && (
                  <motion.div
                    key="analyzed"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <AnalysisDisplay />
                    <p className="mt-4 font-mono text-xs text-chrome/40">
                      Click to upload a different file
                    </p>
                  </motion.div>
                )}

                {phase === 'error' && (
                  <motion.div
                    key="error"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <div className="w-12 h-12 mx-auto rounded-full border-2 border-red-500/60 flex items-center justify-center mb-4">
                      <span className="text-red-400 text-2xl font-mono">!</span>
                    </div>
                    <p className="font-display font-semibold text-xl text-red-400">ERROR</p>
                    <p className="font-mono text-xs text-red-400/70 mt-1">
                      {useAppStore.getState().error}
                    </p>
                    <p className="mt-4 font-mono text-xs text-chrome/40">
                      Click to try again
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

function MidiIcon({ active }: { active: boolean }) {
  return (
    <motion.div
      className="w-16 h-16 mx-auto relative"
      animate={{ y: active ? -4 : 0 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div className={`w-full h-full rounded-xl border-2 flex items-center justify-center transition-colors duration-300 ${active ? 'border-raw-orange bg-raw-orange/10' : 'border-white/20 bg-white/5'}`}>
        {/* Mini piano roll icon */}
        <div className="grid grid-cols-4 gap-0.5 p-2">
          {[0.7, 0.4, 1, 0.6, 0.9, 0.3, 0.8, 0.5].map((h, i) => (
            <div
              key={i}
              className={`w-1.5 rounded-sm transition-colors duration-300 ${active ? 'bg-raw-orange' : 'bg-chrome/40'}`}
              style={{ height: `${h * 20}px` }}
            />
          ))}
        </div>
      </div>
      {active && (
        <motion.div
          className="absolute inset-0 rounded-xl border-2 border-raw-orange"
          animate={{ scale: [1, 1.3, 1], opacity: [0.6, 0, 0.6] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}
    </motion.div>
  )
}

function AnalyzingAnimation() {
  return (
    <div className="flex items-end justify-center gap-1 h-12">
      {Array.from({ length: 12 }).map((_, i) => (
        <motion.div
          key={i}
          className="w-1.5 bg-raw-orange rounded-sm"
          animate={{ scaleY: [0.2, 1, 0.2] }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.06,
            ease: 'easeInOut',
          }}
          style={{ height: '40px', transformOrigin: 'bottom' }}
        />
      ))}
    </div>
  )
}

function AnalysisDisplay() {
  const analysis = useAppStore((s) => s.analysis)
  const midiFile = useAppStore((s) => s.midiFile)
  if (!analysis) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center gap-3">
        <div className="w-2 h-2 rounded-full bg-raw-orange animate-pulse" />
        <span className="font-display font-bold text-lg text-pearl">
          {midiFile?.name || 'bassline.mid'}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'BPM', value: Math.round(analysis.bpm) },
          { label: 'KEY', value: analysis.key },
          { label: 'BARS', value: analysis.total_bars },
        ].map(({ label, value }) => (
          <div key={label} className="bg-void/60 rounded-lg border border-white/8 p-3">
            <div className="font-mono text-[10px] text-chrome/50 tracking-widest mb-1">{label}</div>
            <div className="font-display font-bold text-xl text-raw-orange">{value}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2">
        <div className={`
          px-3 py-1 rounded-full border font-mono text-xs tracking-widest
          ${analysis.detected_style === 'rawstyle'
            ? 'border-raw-orange/50 text-raw-orange bg-raw-orange/10'
            : 'border-euphoric-cyan/50 text-euphoric-cyan bg-euphoric-cyan/10'
          }
        `}>
          {analysis.detected_style.toUpperCase()} DETECTED
        </div>
      </div>
    </div>
  )
}

function CornerDeco({ active }: { active: boolean }) {
  const color = active ? 'border-raw-orange' : 'border-white/20'
  return (
    <>
      {[
        'top-3 left-3 border-t-2 border-l-2 rounded-tl-sm',
        'top-3 right-3 border-t-2 border-r-2 rounded-tr-sm',
        'bottom-3 left-3 border-b-2 border-l-2 rounded-bl-sm',
        'bottom-3 right-3 border-b-2 border-r-2 rounded-br-sm',
      ].map((pos, i) => (
        <div key={i} className={`absolute w-4 h-4 ${pos} ${color} transition-colors duration-300`} />
      ))}
    </>
  )
}
