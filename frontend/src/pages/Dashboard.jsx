import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Play, Upload, User, History, BarChart2, BookOpen, AlertCircle } from 'lucide-react'
import { getProfile, getAnalytics, listInterviews, getStatus } from '../services/api'
import { LoadingSpinner, ErrorMessage, ReadinessBadge, DemoNotice, GraniteNotice } from '../components/UI'

export default function Dashboard() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [interviews, setInterviews] = useState([])
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [statusData, analyticsData, interviewsData] = await Promise.all([
          getStatus(),
          getAnalytics(1),
          listInterviews(1),
        ])
        setStatus(statusData)
        setAnalytics(analyticsData)
        setInterviews(interviewsData)

        try {
          const profileData = await getProfile(1)
          setProfile(profileData)
        } catch {
          // Profile may not exist yet
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <LoadingSpinner label="Loading dashboard..." />
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />

  const recent = interviews.slice(0, 5)

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="section-title">Dashboard</h1>
        <p className="section-subtitle">
          {profile ? `Welcome back, ${profile.name}` : 'Welcome to AI Interview Trainer'}
        </p>
      </div>

      {/* AI Status Banner */}
      {status && (status.demo_mode ? <DemoNotice /> : <GraniteNotice />)}

      {/* No profile nudge */}
      {!profile && (
        <div className="card p-5 border-blue-200 bg-blue-50 flex items-start gap-4">
          <AlertCircle size={20} className="text-blue-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-blue-900 text-sm">Complete your profile to get started</p>
            <p className="text-xs text-blue-700 mt-0.5">Add your name, target role, and skills to personalise your interview questions.</p>
            <button className="btn-primary text-xs mt-3 py-1.5 px-4" onClick={() => navigate('/profile')}>
              Set Up Profile
            </button>
          </div>
        </div>
      )}

      {/* Profile summary */}
      {profile && (
        <div className="card p-5 flex flex-wrap gap-5 items-start">
          <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white text-lg font-bold shrink-0">
            {profile.name?.[0]?.toUpperCase() || 'C'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-gray-900">{profile.name}</p>
            <p className="text-sm text-gray-500">{profile.target_role}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="badge bg-blue-50 text-blue-700">{profile.experience_level}</span>
              {profile.target_company && (
                <span className="badge bg-gray-100 text-gray-700">Target: {profile.target_company}</span>
              )}
            </div>
          </div>
          <button className="btn-secondary text-xs py-1.5 px-3" onClick={() => navigate('/profile')}>
            Edit Profile
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Interviews Done', value: analytics?.total_interviews ?? 0, color: 'text-blue-600' },
          { label: 'Average Score', value: analytics?.average_score != null ? `${analytics.average_score}/10` : '—', color: 'text-green-600' },
          { label: 'Best Score', value: analytics?.best_score != null ? `${analytics.best_score}/10` : '—', color: 'text-purple-600' },
          { label: 'Trend', value: analytics?.improvement_trend ?? '—', color: 'text-orange-600' },
        ].map((s) => (
          <div key={s.label} className="card p-4 text-center">
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { icon: Play, label: 'Start New Interview', path: '/interview/setup', primary: true },
            { icon: Upload, label: 'Upload Resume', path: '/resume', primary: false },
            { icon: BarChart2, label: 'View Analytics', path: '/analytics', primary: false },
            { icon: History, label: 'Interview History', path: '/history', primary: false },
            { icon: BookOpen, label: 'Preparation Plan', path: '/preparation', primary: false },
            { icon: User, label: 'Edit Profile', path: '/profile', primary: false },
          ].map(({ icon: Icon, label, path, primary }) => (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`card p-4 text-left flex items-center gap-3 transition-colors hover:border-blue-200 ${
                primary ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700' : ''
              }`}
            >
              <Icon size={18} className={primary ? 'text-white' : 'text-blue-600'} />
              <span className={`text-sm font-medium ${primary ? 'text-white' : 'text-gray-700'}`}>
                {label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Recent interviews */}
      {recent.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Recent Interviews</h2>
          <div className="card divide-y divide-gray-100">
            {recent.map((iv) => (
              <div
                key={iv.id}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer"
                onClick={() =>
                  iv.status === 'completed'
                    ? navigate(`/interview/${iv.id}/report`)
                    : navigate(`/interview/${iv.id}`)
                }
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{iv.target_role}</p>
                  <p className="text-xs text-gray-500">
                    {iv.interview_type} · {new Date(iv.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {iv.overall_score != null && (
                    <span className="text-sm font-semibold text-blue-600">{iv.overall_score.toFixed(1)}/10</span>
                  )}
                  {iv.readiness_level && <ReadinessBadge level={iv.readiness_level} />}
                  <span className={`badge ${iv.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {iv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weak areas */}
      {analytics?.weak_skill_areas?.length > 0 && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Areas to Improve</h2>
          <div className="flex flex-wrap gap-2">
            {analytics.weak_skill_areas.map((a, i) => (
              <span key={i} className="badge bg-red-50 text-red-700">{a}</span>
            ))}
          </div>
          <button
            className="btn-secondary text-xs mt-4 py-1.5 px-3"
            onClick={() => navigate('/preparation')}
          >
            View Preparation Plan
          </button>
        </div>
      )}
    </div>
  )
}
