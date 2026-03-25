'use client'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-arc-dark via-arc-gray to-arc-dark flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-5xl font-bold text-arc-light mb-4">
          Research Paper → Jupyter Notebook
        </h1>
        <p className="text-xl text-arc-light opacity-75 mb-8">
          Convert research papers into executable, publication-ready notebooks
        </p>
        <button className="bg-arc-purple hover:bg-arc-accent text-white font-bold py-3 px-8 rounded-lg transition-colors">
          Get Started
        </button>
      </div>
    </main>
  )
}
