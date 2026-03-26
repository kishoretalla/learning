'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">
      {/* Animated background elements (ARC Prize aesthetic) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-arc-purple opacity-5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-arc-accent opacity-5 rounded-full blur-3xl"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto text-center space-y-8 md:space-y-12">
        {/* Main heading */}
        <div className="space-y-4">
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-bold text-arc-light tracking-tight leading-[1.1]">
            Research Paper
            <br />
            <span className="bg-gradient-to-r from-arc-purple to-arc-accent bg-clip-text text-transparent">
              → Jupyter Notebook
            </span>
          </h1>
        </div>

        {/* Subtitle */}
        <p className="text-lg sm:text-xl md:text-2xl text-arc-light opacity-75 leading-relaxed max-w-2xl mx-auto">
          Convert research papers into executable, publication-ready Jupyter notebooks
          with extracted methodologies, algorithms, and synthetic data experiments.
        </p>

        {/* Features list */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 md:gap-8 my-8 md:my-12">
          {[
            { icon: '📄', label: 'PDF Upload', desc: 'Support for research papers up to 10MB' },
            { icon: '🤖', label: 'AI Analysis', desc: 'Gemini powered extraction' },
            { icon: '📓', label: 'Notebooks', desc: 'Publication-ready notebooks' },
          ].map((feature, idx) => (
            <div key={idx} className="space-y-2 p-4 rounded-lg bg-arc-gray/30 backdrop-blur border border-arc-purple/10 hover:border-arc-purple/30 transition-colors">
              <div className="text-3xl">{feature.icon}</div>
              <h3 className="font-semibold text-arc-light text-sm">{feature.label}</h3>
              <p className="text-arc-light opacity-60 text-xs">{feature.desc}</p>
            </div>
          ))}
        </div>

        {/* Call-to-action button */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 md:pt-8">
          <Link
            href="/upload"
            className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-arc-purple to-arc-accent text-white font-bold rounded-lg hover:shadow-lg hover:shadow-arc-purple/50 transform hover:scale-105 transition-all duration-200 data-testid='get-started-button'"
            data-testid="get-started-button"
          >
            Get Started
            <span className="ml-2">→</span>
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center px-8 py-4 border-2 border-arc-purple/50 text-arc-light font-semibold rounded-lg hover:border-arc-purple transition-all duration-200"
          >
            View Docs
          </a>
        </div>

        {/* Footer text */}
        <div className="pt-8 md:pt-12 text-arc-light opacity-50 text-sm">
          <p>Built for researchers at OpenAI, DeepMind, and beyond</p>
        </div>
      </div>
    </main>
  )
}

