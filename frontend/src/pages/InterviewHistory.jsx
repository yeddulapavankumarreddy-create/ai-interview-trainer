import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listInterviews } from '../services/api'
import { LoadingSpinner, ErrorMessage, ReadinessBadge } from '../components/UI'
import { ChevronRight, Play } from 'lucide-react'

const TYPE_COLORS = {
  technical: 'bg-purple-100 text-purple-700',
  hr: 'bg-green-100 text-green-700',
  behavioral: 'bg-orange-100 text-orange-700',
  mixed: 'bg-blue-100 text-blue-700',
}

export default function InterviewHistory() {
  const navigate = useNavigate()
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    listInterviews(1)
      .then(setInterviews)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner label="Loading history..." />
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="section-title">Interview History</h1>
          <p className="section-subtitle">{interviews.length} interview{interviews.length !== 1 ? 's' : ''} completed</p>
        </div>
        <button className="btn-primary text-sm flex items-center gap-2" onClick={() => navigate('/interview/setup')}>
          <Play size={14} /> New Interview
        </button>
      </div>

      {interviews.length === 0 ? (
        <div className="card p-10 text-center">
          <p className="text-gray-500 mb-4">No interviews yet. Start your first mock interview!</p>
          <button className="btn-primary" onClick={() => navigate('/interview/setup')}>Start Interview</button>
        </div>
      ) : (
        <div className="card divide-y divide-gray-100">
          {interviews.map((iv) => (
            <div
              key={iv.id}
              className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 cursor-pointer group"
              onClick={() =>
                iv.status === 'completed'
                  ? navigate(`/interview/${iv.id}/report`)
                  : navigate(`/interview/${iv.id}`)
              }
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-semibold text-gray-900 text-sm">{iv.target_role}</p>
                  <span className={`badge ${TYPE_COLORS[iv.interview_type] || 'bg-gray-100 text-gray-700'}`}>
                    {iv.interview_type}
                  </span>
                  {iv.difficulty && (
                    <span className="badge bg-gray-100 text-gray-600">{iv.difficulty}</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(iv.created_at).toLocaleDateString('en-IN', {
                    day: 'numeric', month: 'short', year: 'numeric'
                  })}
                  {iv.question_count && ` · ${iv.question_count} questions`}
                </p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                {iv.overall_score != null ? (
                  <div className="text-right">
                    <p className="text-lg font-bold text-blue-600">{iv.overall_score.toFixed(1)}</p>
                    <p className="text-xs text-gray-400">/ 10</p>
                  </div>
                ) : (
                  <span className="badge bg-yellow-100 text-yellow-700">In Progress</span>
                )}
                {iv.readiness_level && <ReadinessBadge level={iv.readiness_level} />}
                <ChevronRight size={16} className="text-gray-400 group-hover:text-gray-600" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
