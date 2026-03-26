'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '@/lib/store'
import { downloadBlob } from '@/lib/api'
import { useState, useEffect } from 'react'

const TRACKS = [
  {
    id: 'lead',
    label: 'LEAD MELODY',
    desc: 'Main synth lead — hardstyle pattern',
    color: '#FF4D00',
    colorClass: 'text-raw-orange border-raw-orange/40 bg-raw-orange/8',
    icon: '◈',
    notePattern: [0.7, 0, 0.4, 0, 0.9, 0, 0.6, 0, 0.3, 0, 0.8, 0, 0.5, 0, 1, 0],
  },
  {
    id: 'chords',
    label: 'CHORD STABS',
    desc: 'Power chords — rhythmic punches',
    color: '#A855F7',
    colorClass: 'text-violet-400 border-violet-400/40 bg-violet-500/8',
    icon: '◇',
    notePattern: [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
  },
  {
    id: 'pads',
    label: 'ATMOSPHERE PAD',
    desc: 'Wide pads — harmonic bed',
    color: '#00D4FF',
    colorClass: 'text-euphoric-cyan border-euphoric-cyan/40 bg-euphoric-cyan/8',
    icon: '○',
    notePattern: [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
  },
]

export default function ResultsSection() {
  const { phase, result } = useAppStore()
  const [downloaded, setDownloaded] = useState<string[]>([])
  const [allDownloaded, setAllDownloaded] = useState(false)

  const isVisible = phase === 'done' && result !== null

  useEffect(() => {
    if (downloaded.length === 3) setAllDownloaded(true)
  }, [downloaded])

  const handleDownloadAll = () => {
    if (!result?.downloadUrl) return
    const link = document.createElement('a')
    link.href = result.downloadUrl
    link.download = `RAWGEN_${result.sessionId}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    setDownloaded(['lead', 'chords', 'pads'])
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.section
          key="results"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 px-6 pb-16"
          id="results"
        >
          <div className="max-w-2xl mx-auto space-y-6">

            {/* Section label */}
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent to-raw-orange/30" />
              <span className="font-mono text-xs tracking-[0.25em] text-raw-orange/70 uppercase">
                03 / Results
              </span>
              <div className="h-px flex-1 bg-gradient-to-l from-transparent to-raw-orange/30" />
            </div>

            {/* Success header */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="text-center py-2"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-raw-orange/30 bg-raw-orange/5 mb-4">
                <motion.div
                  className="w-2 h-2 rounded-full bg-raw-orange"
                  animate={{ scale: [1, 1.5, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                />
                <span className="font-mono text-xs text-raw-orange tracking-widest">
                  GENERATION COMPLETE — SESSION {result?.sessionId}
                </span>
              </div>

              <div className="flex justify-center gap-6 font-mono text-xs text-chrome/40">
                <span>BPM: <span className="text-chrome/70">{Math.round(result?.metadata.bpm || 0)}</span></span>
                <span>KEY: <span className="text-chrome/70">{result?.metadata.key}</span></span>
                <span>STYLE: <span className="text-chrome/70">{result?.metadata.style?.toUpperCase()}</span></span>
                <span>BARS: <span className="text-chrome/70">{result?.metadata.bars_generated}</span></span>
              </div>
            </motion.div>

            {/* Piano Roll Preview */}
            <PianoRollPreview />

            {/* Track Cards */}
            <div className="space-y-3">
              {TRACKS.map((track, i) => (
                <motion.div
                  key={track.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                >
                  <TrackCard
                    track={track}
                    isDownloaded={downloaded.includes(track.id)}
                  />
                </motion.div>
              ))}
            </div>

            {/* Download All CTA */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
            >
              <button
                onClick={handleDownloadAll}
                className="w-full btn-raw text-white rounded-xl py-5 flex items-center justify-center gap-3 font-display font-bold text-xl tracking-[0.15em]"
              >
                <DownloadIcon />
                <span>DOWNLOAD ALL — ZIP</span>
              </button>
              <p className="text-center font-mono text-[10px] text-chrome/30 mt-3 tracking-wide">
                Contains lead.mid + chords.mid + pads.mid + metadata.json
              </p>
            </motion.div>

            {/* FL Studio tip */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.9 }}
              className="rounded-xl border border-white/6 bg-ash/20 p-4"
            >
              <div className="font-mono text-[10px] text-chrome/40 tracking-widest uppercase mb-2">
                FL Studio Instructions
              </div>
              <p className="font-mono text-xs text-chrome/60 leading-relaxed">
                Unzip → Drag each .mid into the <span className="text-pearl">FL Studio playlist</span> or
                directly onto an instrument channel.
                Lead → Synth/Lead sound ·
                Chords → Pluck/Stab ·
                Pads → Long atmospheric pad
              </p>
            </motion.div>

          </div>
        </motion.section>
      )}
    </AnimatePresence>
  )
}

function PianoRollPreview() {
  // Visual piano roll mockup showing the generated pattern
  const rows = 16
  const cols = 32

  const leadPattern = generateVisualPattern(rows, cols, 'lead')
  const chordPattern = generateVisualPattern(rows, cols, 'chords')
  const padPattern = generateVisualPattern(rows, cols, 'pads')

  return (
    <div className="rounded-xl border border-white/8 bg-ash/30 overflow-hidden">
      <div className="px-4 py-2 border-b border-white/6 flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-raw-orange animate-pulse" />
        <span className="font-mono text-[10px] text-chrome/50 tracking-widest uppercase">
          Piano Roll Preview
        </span>
      </div>
      <div className="p-4 space-y-2">
        {[
          { pattern: leadPattern, color: '#FF4D00', label: 'LEAD' },
          { pattern: chordPattern, color: '#A855F7', label: 'CHORDS' },
          { pattern: padPattern, color: '#00D4FF', label: 'PADS' },
        ].map(({ pattern, color, label }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="font-mono text-[9px] text-chrome/30 w-10 text-right shrink-0">
              {label}
            </span>
            <div className="flex-1 h-6 relative bg-void/60 rounded overflow-hidden">
              {pattern.map((note, i) => note && (
                <motion.div
                  key={i}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: i * 0.01, duration: 0.2 }}
                  className="absolute top-0.5 rounded-sm"
                  style={{
                    left: `${(i / cols) * 100}%`,
                    width: `${(note.duration / cols) * 100}%`,
                    height: `${20 - note.pitch * 1.2}px`,
                    top: `${note.pitch * 1.2}px`,
                    backgroundColor: color,
                    opacity: 0.8,
                    transformOrigin: 'left',
                  }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function generateVisualPattern(
  rows: number,
  cols: number,
  type: string
): Array<{ pitch: number; duration: number } | null> {
  const result: Array<{ pitch: number; duration: number } | null> = new Array(cols).fill(null)

  if (type === 'lead') {
    const positions = [0, 2, 4, 6, 9, 11, 13, 15, 16, 18, 20, 24, 26, 28, 30]
    const pitches = [4, 8, 6, 10, 5, 9, 7, 11, 4, 8, 6, 10, 5, 9, 7]
    positions.forEach((pos, i) => {
      result[pos] = { pitch: pitches[i] || 6, duration: 1.5 }
    })
  } else if (type === 'chords') {
    ;[0, 8, 16, 24].forEach((pos) => {
      result[pos] = { pitch: 2, duration: 3 }
      result[pos + 1] = { pitch: 6, duration: 3 }
    })
  } else {
    result[0] = { pitch: 1, duration: 14 }
    result[16] = { pitch: 1, duration: 14 }
  }

  return result
}

function TrackCard({
  track,
  isDownloaded,
}: {
  track: (typeof TRACKS)[0]
  isDownloaded: boolean
}) {
  return (
    <div className={`
      rounded-xl border p-4 flex items-center gap-4
      transition-all duration-300
      ${isDownloaded ? track.colorClass : 'border-white/8 bg-ash/20'}
    `}>
      {/* Icon */}
      <div className={`
        w-10 h-10 rounded-lg border flex items-center justify-center
        font-mono text-lg flex-shrink-0
        ${isDownloaded ? track.colorClass : 'border-white/10 text-chrome/40'}
      `}>
        {track.icon}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className={`font-display font-bold text-base ${isDownloaded ? '' : 'text-pearl'}`}>
          {track.label}
        </div>
        <div className="font-mono text-[10px] text-chrome/40 tracking-wide mt-0.5">
          {track.desc}
        </div>
        {/* Mini waveform */}
        <div className="flex items-end gap-px mt-1.5 h-3">
          {track.notePattern.map((h, i) => (
            <div
              key={i}
              className="w-1 rounded-sm flex-shrink-0"
              style={{
                height: `${Math.max(h * 12, 2)}px`,
                backgroundColor: h > 0 ? track.color : 'rgba(255,255,255,0.08)',
                opacity: isDownloaded ? 1 : 0.5,
              }}
            />
          ))}
        </div>
      </div>

      {/* Filename */}
      <div className="font-mono text-xs text-chrome/40 shrink-0">
        {track.id}.mid
      </div>
    </div>
  )
}

function DownloadIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path
        d="M10 2v10M10 12l-3-3M10 12l3-3M3 14v2a1 1 0 001 1h12a1 1 0 001-1v-2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
