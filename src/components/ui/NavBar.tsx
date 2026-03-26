'use client'

import { motion } from 'framer-motion'
import { useAppStore } from '@/lib/store'

export default function NavBar() {
  const { phase, reset } = useAppStore()

  return (
    <motion.nav
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50 glass-heavy border-b border-white/6"
    >
      <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <button onClick={reset} className="flex items-center gap-3 group">
          <div className="w-7 h-7 rounded-md border border-raw-orange/50 flex items-center justify-center bg-raw-orange/10">
            <div className="flex items-end gap-px">
              {[0.5, 1, 0.7].map((h, i) => (
                <div
                  key={i}
                  className="w-0.5 rounded-sm bg-raw-orange"
                  style={{ height: `${h * 14}px` }}
                />
              ))}
            </div>
          </div>
          <span className="font-display font-bold text-base tracking-[0.2em] text-pearl group-hover:text-raw-orange transition-colors">
            RAWGEN
          </span>
        </button>

        {/* Center — phase indicator */}
        <div className="hidden md:flex items-center gap-2">
          {[
            { label: 'UPLOAD', phases: ['idle', 'uploaded', 'analyzing', 'analyzed'] },
            { label: 'CONFIGURE', phases: ['analyzed', 'generating'] },
            { label: 'DOWNLOAD', phases: ['done'] },
          ].map(({ label, phases }, i) => {
            const isActive = phases.some((p) =>
              phase === p || (p === 'analyzed' && phase === 'done')
            )
            const isDone =
              (label === 'UPLOAD' && ['analyzed', 'generating', 'done'].includes(phase)) ||
              (label === 'CONFIGURE' && phase === 'done')

            return (
              <div key={label} className="flex items-center gap-2">
                {i > 0 && <div className="w-6 h-px bg-white/10" />}
                <span
                  className={`font-mono text-[9px] tracking-[0.2em] transition-colors duration-300 ${
                    isDone
                      ? 'text-raw-orange/70'
                      : isActive
                      ? 'text-chrome/80'
                      : 'text-chrome/25'
                  }`}
                >
                  {isDone ? '✓' : `0${i + 1}`} {label}
                </span>
              </div>
            )
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          <a
            href="#upload"
            className="hidden md:block font-mono text-[10px] tracking-widest text-chrome/40 hover:text-chrome/70 transition-colors uppercase"
          >
            Docs
          </a>
          {phase !== 'idle' && (
            <motion.button
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              onClick={reset}
              className="btn-ghost px-3 py-1.5 rounded-lg text-[10px] text-chrome/60"
            >
              Reset
            </motion.button>
          )}
        </div>
      </div>
    </motion.nav>
  )
}
