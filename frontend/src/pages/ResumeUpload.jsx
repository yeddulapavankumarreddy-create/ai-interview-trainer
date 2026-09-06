import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, CheckCircle2, AlertCircle, X } from 'lucide-react'
import { uploadResume, getResume } from '../services/api'
import { DemoNotice } from '../components/UI'

export default function ResumeUpload() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [resume, setResume] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)

  useEffect(() => {
    getResume(1).then(setResume).catch(() => {})
  }, [])

  const handleFile = (file) => {
    const allowed = ['.pdf', '.docx', '.txt']
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
    if (!allowed.includes(ext)) {
      setError('Unsupported file type. Please upload a PDF, DOCX, or TXT file.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File exceeds 10 MB limit.')
      return
    }
    setError(null)
    setSelectedFile(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    setError(null)
    try {
      const result = await uploadResume(selectedFile, 1)
      setResume(result)
      setSelectedFile(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const parsed = resume?.parsed_information || {}

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="section-title">Resume Upload</h1>
        <p className="section-subtitle">Upload your resume for AI-powered analysis and personalised questions.</p>
      </div>

      {parsed.is_demo && <DemoNotice />}

      {/* Upload area */}
      <div className="card p-5">
        <h2 className="font-semibold text-gray-900 text-sm mb-4">Upload Resume</h2>

        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={32} className="text-gray-400 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-700 mb-1">
            Drag and drop your resume here
          </p>
          <p className="text-xs text-gray-500 mb-3">or click to browse</p>
          <p className="text-xs text-gray-400">PDF, DOCX, or TXT · Max 10 MB</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </div>

        {selectedFile && (
          <div className="mt-4 flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2">
              <FileText size={16} className="text-blue-600" />
              <span className="text-sm text-blue-800 font-medium">{selectedFile.name}</span>
              <span className="text-xs text-blue-500">({(selectedFile.size / 1024).toFixed(0)} KB)</span>
            </div>
            <button onClick={() => setSelectedFile(null)}>
              <X size={16} className="text-blue-500 hover:text-blue-700" />
            </button>
          </div>
        )}

        {error && (
          <div className="mt-3 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle size={15} className="mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        {selectedFile && (
          <button
            className="btn-primary w-full mt-4"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analysing resume with IBM Granite...
              </span>
            ) : (
              'Upload & Analyse Resume'
            )}
          </button>
        )}
      </div>

      {/* Parsed Info */}
      {resume && (
        <div className="card p-5 space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={18} className="text-green-500" />
            <h2 className="font-semibold text-gray-900 text-sm">Resume Analysed Successfully</h2>
            <span className="text-xs text-gray-400 ml-auto">{resume.filename}</span>
          </div>

          {parsed.is_demo && (
            <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
              Demo Mode — parsed with heuristics. IBM Granite analysis will be used when credentials are configured.
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            {parsed.name && <InfoRow label="Name" value={parsed.name} />}
            {parsed.email && <InfoRow label="Email" value={parsed.email} />}
          </div>

          {parsed.education?.length > 0 && (
            <TagSection title="Education" items={parsed.education} />
          )}
          {parsed.skills?.length > 0 && (
            <TagSection title="Skills" items={parsed.skills} color="blue" />
          )}
          {parsed.programming_languages?.length > 0 && (
            <TagSection title="Programming Languages" items={parsed.programming_languages} color="purple" />
          )}
          {parsed.technologies?.length > 0 && (
            <TagSection title="Technologies" items={parsed.technologies} color="green" />
          )}
          {parsed.certifications?.length > 0 && (
            <TagSection title="Certifications" items={parsed.certifications} color="orange" />
          )}

          {parsed.projects?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-2">Projects</p>
              <div className="space-y-2">
                {parsed.projects.map((p, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg text-xs">
                    <p className="font-medium text-gray-900">{typeof p === 'string' ? p : p.name}</p>
                    {p.description && <p className="text-gray-500 mt-1">{p.description}</p>}
                    {p.tech_stack?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {p.tech_stack.map((t, ti) => (
                          <span key={ti} className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <button className="btn-primary" onClick={() => navigate('/interview/setup')}>
          Continue to Interview Setup
        </button>
        <button className="btn-secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="font-medium text-gray-900">{value}</p>
    </div>
  )
}

function TagSection({ title, items, color = 'gray' }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-700',
    purple: 'bg-purple-50 text-purple-700',
    green: 'bg-green-50 text-green-700',
    orange: 'bg-orange-50 text-orange-700',
    gray: 'bg-gray-100 text-gray-700',
  }
  const cls = colorMap[color] || colorMap.gray
  return (
    <div>
      <p className="text-xs font-semibold text-gray-600 mb-2">{title}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className={`badge ${cls}`}>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
        ))}
      </div>
    </div>
  )
}
