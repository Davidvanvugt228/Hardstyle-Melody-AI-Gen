/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        void: '#050508',
        carbon: '#0A0A0F',
        graphite: '#111118',
        ash: '#1A1A24',
        slate: '#252535',
        mist: '#35354A',
        raw: {
          red: '#FF1A1A',
          orange: '#FF4D00',
          amber: '#FF8C00',
        },
        euphoric: {
          cyan: '#00D4FF',
          blue: '#0066FF',
          violet: '#7C3AED',
        },
        chrome: '#A8A8C4',
        pearl: '#E8E8F4',
      },
      fontFamily: {
        display: ['var(--font-display)', 'monospace'],
        body: ['var(--font-body)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      animation: {
        'pulse-raw': 'pulse-raw 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 3s linear infinite',
        'glitch': 'glitch 0.5s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'waveform': 'waveform 1.5s ease-in-out infinite',
      },
      keyframes: {
        'pulse-raw': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.7', transform: 'scale(0.98)' },
        },
        'scan': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'waveform': {
          '0%, 100%': { transform: 'scaleY(0.3)' },
          '50%': { transform: 'scaleY(1)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
