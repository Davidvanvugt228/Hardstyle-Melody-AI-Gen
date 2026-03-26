'use client'

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import NavBar from '@/components/ui/NavBar'
import HeroSection from '@/components/sections/HeroSection'
import UploadSection from '@/components/sections/UploadSection'
import ConfigPanel from '@/components/sections/ConfigPanel'
import ResultsSection from '@/components/sections/ResultsSection'
import { useAppStore } from '@/lib/store'
import { api } from '@/lib/api'

export default function HomePage() {
  const phase = useAppStore((s) => s.phase)

  // Auto-scroll to sections as phase progresses
  useEffect(() => {
    if (phase === 'analyzed') {
      setTimeout(() => {
        document.getElementById('configure')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
    }
    if (phase === 'done') {
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
    }
  }, [phase])

  return (
    <main className="min-h-screen bg-void noise-overlay grid-lines">
      <NavBar />

      {/* Main content with top padding for fixed nav */}
      <div className="pt-14">
        <HeroSection />
        <UploadSection />
        <ConfigPanel />
        <ResultsSection />
      </div>

      {/* Footer */}
      <Footer />

      {/* Background ambient glow */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse 60% 40% at 50% 0%, rgba(255,77,0,0.04) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 100%, rgba(0,212,255,0.02) 0%, transparent 60%)
          `,
          zIndex: 0,
        }}
      />
    </main>
  )
}

function Footer() {
  return (
    <footer className="relative z-10 border-t border-white/5 py-8 px-6 mt-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="font-display font-bold text-sm tracking-[0.3em] text-pearl/40">
              RAWGEN
            </span>
            <span className="font-mono text-[9px] text-chrome/20 tracking-widest">
              HARDSTYLE MIDI GENERATOR v1.0
            </span>
          </div>

          <div className="flex items-center gap-6">
            {[
              { label: 'RAWSTYLE', active: true },
              { label: 'EUPHORIC', active: true },
              { label: 'FL STUDIO', active: true },
            ].map(({ label, active }) => (
              <span key={label} className="font-mono text-[9px] tracking-widest text-chrome/25 uppercase">
                {active ? '✓' : '○'} {label}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-white/4">
          <p className="font-mono text-[9px] text-chrome/15 tracking-widest text-center">
            GENERATES ORIGINAL MIDI · TREND-INFORMED · NOT RANDOM · PRODUCTION READY
          </p>
        </div>
      </div>
    </footer>
  )
}
