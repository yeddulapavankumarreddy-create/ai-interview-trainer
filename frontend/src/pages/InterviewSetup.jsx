import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap } from 'lucide-react'
import { getProfile, createInterview, getStatus } from '../services/api'
import { LoadingSpinner, DemoNotice, GraniteNotice } from '../components/UI'

const INTERVIEW_TYPES = [
  { value: 'technical', label: 'Technical', desc: 'DS&A, system design, coding, frameworks' },
  { value: 'hr', label: 'HR', desc: 'Motivation, culture fit, career goals' },
  { value: 'behavioral', label: 'Behavioral', desc: 'STAR stories, soft skills, teamwork' },
  { value: 'mixed', label: 'Mixed', desc: 'Combination of all types' },
]

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
  { value: 'adaptive', label: 'Adaptive' },
]

const QUESTION_COUNTS = [5, 10, 15]

export default function InterviewSetup() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [status, setStatus] = useState(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    interview_type: 'mixed',
    difficulty: 'medium',
    question_count: 10,
    target_role: '',
    target_company: '',
  })

  useEffect(() => {
    // Fetch status and profile in parallel
    Promise.all([
      getStatus().catch(() => null),
      getProfile(1).catch(() => null),
    ]).then(([statusData, profileData]) => {
      setStatus(statusData)
      if (profileData) {
        setProfile(profileData)
        setForm((f) => ({
          ...f,
          target_role: profileData.target_role || '',
          target_company: profileData.target_company || '',
        }))
      }
    }).finally(() => setLoadingProfile(false))
  }, [])

  const handleCreate = async () => {
    if (!form.target_role.trim()) {
      setError('Please enter a target role.')
      return
    }
    setError(null)
    setCreating(true)
    try {
      const interview = await createInterview({
        profile_id: 1,
        ...form,
        question_count: Number(form.question_count),
      })
      navigate(`/interview/${interview.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setCreating(false)
    }
  }

  if (loadingProfile) return <LoadingSpinner label="Loading profile..." />

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="section-title">Interview Setup</h1>
        <p className="section-subtitle">Configure your mock interview session.</p>
      </div>

      {!profile && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
          Profile not set up yet. Questions will be generic.{' '}
          <button className="underline" onClick={() => navigate('/profile')}>Set up profile →</button>
        </div>
      )}

      {status && (status.demo_mode ? <DemoNotice /> : <GraniteNotice />)}

      {/* Interview Type */}
      <div className="card p-5">
        <h2 className="font-semibold text-gray-900 text-sm mb-4">Interview Type</h2>
        <div className="grid grid-cols-2 gap-3">
          {INTERVIEW_TYPES.map((t) => (
            <button
              key={t.value}
              onClick={() => setForm((f) => ({ ...f, interview_type: t.value }))}
              className={`p-3 rounded-lg border-2 text-left transition-colors ${
                form.interview_type === t.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <p className={`font-semibold text-sm ${form.interview_type === t.value ? 'text-blue-700' : 'text-gray-900'}`}>
                {t.label}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">{t.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Config */}
      <div className="card p-5 space-y-5">
        <h2 className="font-semibold text-gray-900 text-sm">Configuration</h2>

        <div>
          <label className="label">Difficulty</label>
          <div className="flex gap-2 flex-wrap">
            {DIFFICULTIES.map((d) => (
              <button
                key={d.value}
                onClick={() => setForm((f) => ({ ...f, difficulty: d.value }))}
                className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                  form.difficulty === d.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Number of Questions</label>
          <div className="flex gap-2">
            {QUESTION_COUNTS.map((n) => (
              <button
                key={n}
                onClick={() => setForm((f) => ({ ...f, question_count: n }))}
                className={`px-5 py-2 rounded-lg border text-sm font-medium transition-colors ${
                  form.question_count === n
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Target Role *</label>
          <input
            className="input-field"
            value={form.target_role}
            onChange={(e) => setForm((f) => ({ ...f, target_role: e.target.value }))}
            placeholder="e.g. Software Engineer"
          />
        </div>

        <div>
          <label className="label">Target Company (optional)</label>
          <input
            className="input-field"
            value={form.target_company}
            onChange={(e) => setForm((f) => ({ ...f, target_company: e.target.value }))}
            placeholder="e.g. Google"
          />
        </div>
      </div>

      {/* Summary */}
      <div className="card p-4 bg-blue-50 border-blue-200">
        <p className="text-sm font-medium text-blue-900 mb-2">Interview Summary</p>
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="badge bg-blue-100 text-blue-700">{form.interview_type}</span>
          <span className="badge bg-blue-100 text-blue-700">{form.difficulty}</span>
          <span className="badge bg-blue-100 text-blue-700">{form.question_count} questions</span>
          {form.target_role && <span className="badge bg-blue-100 text-blue-700">{form.target_role}</span>}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
      )}

      <button
        className="btn-primary w-full flex items-center justify-center gap-2 py-3"
        onClick={handleCreate}
        disabled={creating}
      >
        {creating ? (
          <>
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Generating personalised questions with IBM Granite...
          </>
        ) : (
          <>
            <Zap size={18} />
            Generate Interview
          </>
        )}
      </button>
    </div>
  )
}
