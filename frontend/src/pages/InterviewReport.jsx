import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Download, BookOpen, Play, ChevronDown, ChevronUp } from 'lucide-react'
import { getReport } from '../services/api'
import { LoadingSpinner, ErrorMessage, ScoreCard, ReadinessBadge, DemoNotice } from '../components/UI'

export default function InterviewReport() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedQ, setExpandedQ] = useState(null)

  useEffect(() => {
    getReport(id)
      .then(setReport)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <LoadingSpinner label="Generating your report with IBM Granite..." />
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />
  if (!report) return null

  const planDays = report.preparation_plan?.daily_plan || []

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-xs text-gray-400 mb-1">Interview Report</p>
            <h1 className="text-xl font-bold text-gray-900">{report.candidate_name}</h1>
            <p className="text-gray-500 text-sm">{report.target_role}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="badge bg-blue-100 text-blue-700">{report.interview_type}</span>
              <span className="badge bg-gray-100 text-gray-700">{report.question_count} questions</span>
              <span className="badge bg-gray-100 text-gray-700">{new Date(report.date).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400">Overall Score</p>
            <p className="text-4xl font-bold text-blue-600">{report.overall_score?.toFixed(1)}</p>
            <p className="text-gray-400 text-sm">/ 10</p>
            <div className="mt-2">
              <ReadinessBadge level={report.readiness_level} />
            </div>
          </div>
        </div>
        {report.summary && (
          <p className="mt-4 text-sm text-gray-600 leading-relaxed p-3 bg-gray-50 rounded-lg">
            {report.summary}
          </p>
        )}
        {report.is_demo && <div className="mt-3"><DemoNotice /></div>}
      </div>

      {/* Scores */}
      <div>
        <h2 className="font-semibold text-gray-900 text-sm mb-3">Performance Breakdown</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <ScoreCard label="Overall" score={report.overall_score} color="blue" />
          {report.technical_score != null && <ScoreCard label="Technical" score={report.technical_score} color="purple" />}
          {report.hr_score != null && <ScoreCard label="HR" score={report.hr_score} color="green" />}
          {report.behavioral_score != null && <ScoreCard label="Behavioral" score={report.behavioral_score} color="orange" />}
          {report.communication_score != null && <ScoreCard label="Communication" score={report.communication_score} color="blue" />}
          {report.relevance_score != null && <ScoreCard label="Relevance" score={report.relevance_score} color="green" />}
        </div>
      </div>

      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {report.strong_areas?.length > 0 && (
          <div className="card p-4">
            <h2 className="font-semibold text-green-700 text-sm mb-3">Strong Areas ✓</h2>
            <ul className="space-y-1.5">
              {report.strong_areas.map((a, i) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">•</span> {a}
                </li>
              ))}
            </ul>
          </div>
        )}
        {report.weak_areas?.length > 0 && (
          <div className="card p-4">
            <h2 className="font-semibold text-red-600 text-sm mb-3">Areas to Improve</h2>
            <ul className="space-y-1.5">
              {report.weak_areas.map((a, i) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">•</span> {a}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Key feedback */}
      {report.key_feedback && (
        <div className="card p-4 bg-blue-50 border-blue-200">
          <p className="text-xs font-semibold text-blue-800 mb-1">Key Feedback</p>
          <p className="text-sm text-blue-700">{report.key_feedback}</p>
        </div>
      )}

      {/* Q&A Review */}
      {report.qa_pairs?.length > 0 && (
        <div>
          <h2 className="font-semibold text-gray-900 text-sm mb-3">Question Review ({report.qa_pairs.length})</h2>
          <div className="space-y-2">
            {report.qa_pairs.map((qa, i) => (
              <div key={i} className="card overflow-hidden">
                <button
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50"
                  onClick={() => setExpandedQ(expandedQ === i ? null : i)}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                      (qa.score || 0) >= 7 ? 'bg-green-100 text-green-700' :
                      (qa.score || 0) >= 5 ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {qa.score?.toFixed(0) ?? '?'}
                    </div>
                    <span className="text-sm font-medium text-gray-900 truncate">{qa.question}</span>
                  </div>
                  {expandedQ === i ? <ChevronUp size={16} className="text-gray-400 shrink-0" /> : <ChevronDown size={16} className="text-gray-400 shrink-0" />}
                </button>

                {expandedQ === i && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-100">
                    <div>
                      <p className="text-xs font-semibold text-gray-500 mt-3 mb-1">Your Answer</p>
                      <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">{qa.answer}</p>
                    </div>
                    {qa.strengths?.length > 0 && (
                      <p className="text-xs text-green-700">✓ {qa.strengths.join(' · ')}</p>
                    )}
                    {qa.weaknesses?.length > 0 && (
                      <p className="text-xs text-red-600">✗ {qa.weaknesses.join(' · ')}</p>
                    )}
                    {qa.model_answer && (
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <p className="text-xs font-semibold text-blue-800 mb-1">Model Answer</p>
                        <p className="text-xs text-blue-700">{qa.model_answer}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Preparation Plan Preview */}
      {planDays.length > 0 && (
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 text-sm mb-3">Personalised 7-Day Study Plan</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {planDays.slice(0, 4).map((day, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs font-bold text-blue-700 mb-1">Day {day.day}</p>
                <p className="text-sm font-medium text-gray-900">{day.focus}</p>
                {day.activities?.[0] && (
                  <p className="text-xs text-gray-500 mt-1">{day.activities[0]}</p>
                )}
              </div>
            ))}
          </div>
          {planDays.length > 4 && (
            <button
              className="text-xs text-blue-600 mt-3 hover:underline"
              onClick={() => navigate('/preparation')}
            >
              View full plan →
            </button>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <button className="btn-primary flex items-center gap-2" onClick={() => navigate('/interview/setup')}>
          <Play size={15} /> New Interview
        </button>
        <button className="btn-secondary flex items-center gap-2" onClick={() => navigate('/preparation')}>
          <BookOpen size={15} /> Preparation Plan
        </button>
        <button className="btn-secondary flex items-center gap-2" onClick={() => navigate('/analytics')}>
          View Analytics
        </button>
        <button className="btn-secondary" onClick={() => navigate('/dashboard')}>
          Dashboard
        </button>
      </div>
    </div>
  )
}
