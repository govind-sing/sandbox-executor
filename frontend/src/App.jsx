import { useState } from 'react'

const OUTPUT_LABELS = {
  image: 'Image',
  audio: 'Audio',
  pdf: 'PDF',
  csv: 'Table',
  text: 'Text',
}

function ResultRenderer({ outputType, data, description }) {
  const src = `data:${getMimeType(outputType)};base64,${data}`

  if (outputType === 'image') {
    return (
      <div className="flex flex-col items-center gap-3">
        <p className="text-sm text-gray-400">{description}</p>
        <img src={src} alt={description} className="max-w-full rounded-lg border border-gray-700" />
      </div>
    )
  }

  if (outputType === 'audio') {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-gray-400">{description}</p>
        <audio controls src={src} className="w-full" />
      </div>
    )
  }

  if (outputType === 'pdf') {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-gray-400">{description}</p>

      <a
        href={src}
        download="output.pdf"
        className="inline-block bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg w-fit"
      >
        Download PDF
      </a>
    </div>
  )
}

  if (outputType === 'csv') {
    // decode base64 and parse CSV into a table
    const text = atob(data)
    const rows = text.trim().split('\n').map(r => r.split(','))
    const headers = rows[0]
    const body = rows.slice(1)

    return (
      <div className="flex flex-col gap-3 overflow-x-auto">
        <p className="text-sm text-gray-400">{description}</p>
        <table className="min-w-full text-sm border border-gray-700 rounded-lg overflow-hidden">
          <thead className="bg-gray-800">
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="px-4 py-2 text-left text-gray-300 border-b border-gray-700">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {body.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-gray-900' : 'bg-gray-850'}>
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-2 text-gray-300 border-b border-gray-800">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (outputType === 'text') {
    const text = atob(data)
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-gray-400">{description}</p>
        <pre className="bg-gray-800 text-gray-200 p-4 rounded-lg text-sm whitespace-pre-wrap">
          {text}
        </pre>
      </div>
    )
  }

  return null
}

function getMimeType(outputType) {
  const map = {
    image: 'image/png',
    audio: 'audio/mpeg',
    pdf: 'application/pdf',
    csv: 'text/csv',
    text: 'text/plain',
  }
  return map[outputType] || 'application/octet-stream'
}

function CodePanel({ code }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800 text-sm text-gray-300 hover:bg-gray-750 transition"
      >
        <span>Generated Code</span>
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <pre className="bg-gray-900 text-green-400 p-4 text-xs overflow-x-auto whitespace-pre-wrap max-h-96">
          {code}
        </pre>
      )}
    </div>
  )
}

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleExecute() {
    if (!prompt.trim()) return

    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const res = await fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, context }),
      })

      const data = await res.json()

      if (!data.success) {
        setError(data.error || 'Execution failed')
      } else {
        setResult(data)
      }
    } catch (e) {
      setError('Failed to reach the server. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleExecute()
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center px-4 py-12">
      <div className="w-full max-w-2xl flex flex-col gap-6">

        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">Sandbox Executor</h1>
          <p className="text-gray-400 mt-1 text-sm">
            Describe what you want — a chart, audio, PDF, table — and the AI will build and run it.
          </p>
        </div>

        {/* Input */}
        <div className="flex flex-col gap-3 bg-gray-900 rounded-xl p-4 border border-gray-800">
          <textarea
            className="w-full bg-transparent text-white placeholder-gray-500 text-sm resize-none outline-none min-h-[80px]"
            placeholder="Give me a pie chart of population by continent..."
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
          />

          <textarea
            className="w-full bg-gray-800 text-gray-300 placeholder-gray-500 text-sm resize-none outline-none rounded-lg p-3 min-h-[60px]"
            placeholder="Additional context (optional)..."
            value={context}
            onChange={e => setContext(e.target.value)}
            onKeyDown={handleKeyDown}
          />

          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">⌘ + Enter to run</span>
            <button
              onClick={handleExecute}
              disabled={loading || !prompt.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded-lg transition"
            >
              {loading ? 'Running...' : 'Execute'}
            </button>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center gap-2 py-8 text-gray-400">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Generating and executing code...</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-950 border border-red-800 text-red-300 text-sm rounded-lg p-4 whitespace-pre-wrap">
            <p className="font-semibold mb-1">Execution Error</p>
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="flex flex-col gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded-full font-medium">
                  {OUTPUT_LABELS[result.output_type] || result.output_type}
                </span>
              </div>
              <ResultRenderer
                outputType={result.output_type}
                data={result.data}
                description={result.description}
              />
            </div>

            {result.code && <CodePanel code={result.code} />}
          </div>
        )}

      </div>
    </div>
  )
}