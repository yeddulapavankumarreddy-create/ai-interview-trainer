import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProfile, saveProfile } from '../services/api'
import { LoadingSpinner } from '../components/UI'

const EXPERIENCE_LEVELS = [
  { value: 'student', label: 'Student' },
  { value: 'fresher', label: 'Fresher (0 years)' },
  { value: '0-2', label: '0–2 Years' },
  { value: '2-5', label: '2–5 Years' },
  { value: '5+', label: '5+ Years' },
]

const initialForm = {
  name: '',
  email: '',
  target_role: '',
  experience_level: 'fresher',
  education: '',
  skills: '',
  programming_languages: '',
  technologies: '',
  target_company: '',
  job_description: '',
}

export default function ProfileSetup() {
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getProfile(1)
      .then((p) => {
        setForm({
          name: p.name || '',
          email: p.email || '',
          target_role: p.target_role || '',
          experience_level: p.experience_level || 'fresher',
          education: p.education || '',
          skills: p.skills || '',
          programming_languages: p.programming_languages || '',
          technologies: p.technologies || '',
          target_company: p.target_company || '',
          job_description: p.job_description || '',
        })
      })
      .catch(() => {
        // No profile yet — use defaults
      })
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }))
    setSaved(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name.trim() || !form.target_role.trim()) {
      setError('Name and Target Role are required.')
      return
    }
    setError(null)
    setSaving(true)
    try {
      await saveProfile(form)
      setSaved(true)
      setTimeout(() => navigate('/resume'), 1000)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingSpinner label="Loading profile..." />

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="section-title">Profile Setup</h1>
        <p className="section-subtitle">Your profile helps us personalise your interview questions.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Basic Info */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900 text-sm">Basic Information</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Full Name *</label>
              <input className="input-field" value={form.name} onChange={handleChange('name')} placeholder="e.g. Priya Sharma" />
            </div>
            <div>
              <label className="label">Email</label>
              <input className="input-field" type="email" value={form.email} onChange={handleChange('email')} placeholder="priya@example.com" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">Target Job Role *</label>
              <input className="input-field" value={form.target_role} onChange={handleChange('target_role')} placeholder="e.g. Software Engineer" />
            </div>
            <div>
              <label className="label">Experience Level *</label>
              <select className="input-field" value={form.experience_level} onChange={handleChange('experience_level')}>
                {EXPERIENCE_LEVELS.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Education</label>
            <input className="input-field" value={form.education} onChange={handleChange('education')} placeholder="e.g. B.Tech Computer Science — VIT University, 2024" />
          </div>
        </div>

        {/* Skills */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900 text-sm">Skills & Technologies</h2>
          <div>
            <label className="label">Skills (comma-separated)</label>
            <input className="input-field" value={form.skills} onChange={handleChange('skills')} placeholder="e.g. Machine Learning, REST APIs, Problem Solving" />
          </div>
          <div>
            <label className="label">Programming Languages (comma-separated)</label>
            <input className="input-field" value={form.programming_languages} onChange={handleChange('programming_languages')} placeholder="e.g. Python, Java, JavaScript" />
          </div>
          <div>
            <label className="label">Technologies / Frameworks (comma-separated)</label>
            <input className="input-field" value={form.technologies} onChange={handleChange('technologies')} placeholder="e.g. React, FastAPI, Docker, TensorFlow" />
          </div>
        </div>

        {/* Optional */}
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold text-gray-900 text-sm">Optional Details</h2>
          <div>
            <label className="label">Target Company (optional)</label>
            <input className="input-field" value={form.target_company} onChange={handleChange('target_company')} placeholder="e.g. Google, Infosys, IBM" />
          </div>
          <div>
            <label className="label">Job Description (optional — paste for better personalisation)</label>
            <textarea
              className="input-field resize-none"
              rows={4}
              value={form.job_description}
              onChange={handleChange('job_description')}
              placeholder="Paste the job description here..."
            />
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
        )}

        {saved && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            ✓ Profile saved! Redirecting to Resume Upload...
          </div>
        )}

        <div className="flex gap-3">
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => navigate('/dashboard')}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
