import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // ARC Prize inspired: dark with purple accents
        'arc-dark': '#0a0a0a',
        'arc-gray': '#1a1a1a',
        'arc-light': '#f5f5f5',
        'arc-purple': '#a855f7',
        'arc-accent': '#ec4899',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
