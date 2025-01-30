'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface AnalysisResult {
  threat_actor: string
  malware_name: string
  attack_vector: string
  indicators?: string
  targeted_sectors?: string
  severity?: string
  relevance?: string
}

export default function Home() {
  const [apiKey, setApiKey] = useState('')
  const [files, setFiles] = useState<string[]>([])
  const [selectedFile, setSelectedFile] = useState('')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<AnalysisResult[]>([])
  const [loading, setLoading] = useState(false)
  const [isKeySet, setIsKeySet] = useState(false)
  const router = useRouter()

  // 載入已上傳的文件列表
  const fetchFiles = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/files')
      const data = await res.json()
      setFiles(data.files)
    } catch (error) {
      console.error('Error fetching files:', error)
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [])

  const handleKeySubmit = async () => {
    try {
      const res = await fetch('http://localhost:8080/api/key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key: apiKey }),
      })

      if (!res.ok) throw new Error('Failed to update API key')

      setIsKeySet(true)
      alert('API key updated successfully')
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to update API key')
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      const res = await fetch('http://localhost:8080/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) throw new Error('Failed to upload file')

      const data = await res.json()
      setSelectedFile(data.filename)
      fetchFiles() // 重新載入文件列表
      alert('File uploaded successfully')
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to upload file')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedFile) {
      alert('Please select a PDF file first')
      return
    }

    if (!isKeySet) {
      alert('Please set your OpenAI API key first')
      return
    }

    try {
      setLoading(true)
      const res = await fetch('http://localhost:8080/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: selectedFile,
          query: query || undefined,
        }),
      })

      if (!res.ok) throw new Error('Failed to analyze')

      const data = await res.json()
      setResults(data.results)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to analyze')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          Threat Intelligence Analyzer
        </h1>

        {/* API Key Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">OpenAI API Key Setup</h2>
          <div className="flex gap-4">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your OpenAI API key"
              className="flex-1 p-2 border rounded"
            />
            <button
              onClick={handleKeySubmit}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Save Key
            </button>
          </div>
        </div>

        {/* File Upload Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Upload PDF</h2>
          <div className="space-y-4">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              className="block w-full"
            />
          </div>
        </div>

        {/* File Selection Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Select PDF to Analyze</h2>
          <select
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="">Select a file</option>
            {files.map((file) => (
              <option key={file} value={file}>
                {file}
              </option>
            ))}
          </select>
        </div>

        {/* Analysis Section */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Analysis Query</h2>
          <div className="space-y-4">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your query about the threat intelligence (optional)"
              className="w-full p-2 border rounded h-32"
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !selectedFile || !isKeySet}
              className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </div>

        {/* Results Section */}
        {results.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
            <div className="space-y-6">
              {results.map((result, index) => (
                <div key={index} className="border-b pb-4 last:border-b-0">
                  <h3 className="font-semibold text-lg mb-2">Finding {index + 1}</h3>
                  {result.relevance && (
                    <div className="mb-2">
                      <span className="font-medium">Relevance:</span>
                      <p className="ml-2">{result.relevance}</p>
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(result).map(([key, value]) => {
                      if (key !== 'relevance' && value) {
                        return (
                          <div key={key}>
                            <span className="font-medium">
                              {key.replace('_', ' ').toUpperCase()}:
                            </span>
                            <p className="ml-2">{value}</p>
                          </div>
                        )
                      }
                      return null
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
