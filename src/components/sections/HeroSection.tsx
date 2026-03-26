'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import dynamic from 'next/dynamic'

const HeroCanvas = dynamic(() => import('@/components/three/HeroCanvas'), {
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-void" />,
})

export default function HeroSection() {
  return (
    <section className="relative min-h-[60vh] flex flex-col items-center justify-center overflow-hidden">
      {/* 3D background */}
      <HeroCanvas />

      {/* Dark gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-void/40 via-transparent to-void pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-r from-void/60 via-transparent to-void/60 pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 text-center px-6 pt-12 pb-8">

        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-raw-orange/25 bg-raw-orange/5 mb-8"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-raw-orange animate-pulse" />
          <span className="font-mono text-[10px] tracking-[0.3em] text-raw-orange/80 uppercase">
            AI-Powered · Hardstyle · Rawstyle
          </span>
        </motion.div>

        {/* Logo wordmark */}
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <h1 className="font-display font-bold leading-none tracking-tight">
            <span
              className="block text-[clamp(4rem,12vw,9rem)] text-pearl"
              style={{
                textShadow: '0 0 80px rgba(255, 77, 0, 0.15)',
                letterSpacing: '-0.02em',
              }}
            >
              RAW
            </span>
            <span
              className="block text-[clamp(2rem,6vw,4.5rem)] text-raw-orange text-glow-raw"
              style={{ letterSpacing: '0.35em', marginTop: '-0.1em' }}
            >
              GEN
            </span>
          </h1>
        </motion.div>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="font-display text-lg font-light text-chrome/60 mt-4 max-w-md mx-auto tracking-wide"
        >
          Upload a bassline. Get production-ready{' '}
          <span className="text-pearl font-medium">Hardstyle MIDI</span>{' '}
          in seconds.
        </motion.p>

        {/* Feature pills */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="flex flex-wrap justify-center gap-2 mt-6"
        >
          {[
            'Lead Melody',
            'Chord Stabs',
            'Atmosphere Pads',
            'FL Studio Ready',
          ].map((feature) => (
            <span
              key={feature}
              className="px-3 py-1 rounded-full border border-white/10 bg-white/4 font-mono text-[10px] text-chrome/50 tracking-widest uppercase"
            >
              {feature}
            </span>
          ))}
        </motion.div>

        {/* BPM indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.0 }}
          className="flex items-center justify-center gap-3 mt-8"
        >
          <BPMIndicator />
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
      >
        <span className="font-mono text-[9px] tracking-[0.3em] text-chrome/30 uppercase">Upload</span>
        <motion.div
          className="w-px h-8 bg-gradient-to-b from-raw-orange/40 to-transparent"
          animate={{ scaleY: [0, 1, 0], opacity: [0, 1, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
      </motion.div>
    </section>
  )
}

function BPMIndicator() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5">
        {[150, 155, 160, 165, 170].map((bpm, i) => (
          <div key={bpm} className="flex flex-col items-center gap-1">
            <motion.div
              className="w-px bg-raw-orange/60"
              animate={{ height: [8, 20, 8] }}
              transition={{
                duration: 0.5,
                delay: i * 0.1,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
            {i === 2 && (
              <span className="font-mono text-[9px] text-raw-orange/70">160</span>
            )}
          </div>
        ))}
      </div>
      <span className="font-mono text-[10px] text-chrome/30 tracking-widest">BPM RANGE</span>
    </div>
  )
}
