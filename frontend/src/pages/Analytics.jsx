import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts'
import { getAnalytics } from '../services/api'
import { LoadingSpinner, ErrorMessage, ScoreCard } from '../components/UI'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function Analytics() {
  const navigate = useNavigate()
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getAnalytics(1)
      .then(setAnalytics)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner label="Loading analytics..." />
  if (error) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />

  const noData = !analytics || analytics.total_interviews === 0

  const radarData = [
    { subject: 'Technical', value: analytics?.category_averages?.technical ?? 0 },
    { subject: 'HR', value: analytics?.category_averages?.hr ?? 0 },
    { subject: 'Behavioral', value: analytics?.category_averages?.behavioral ?? 0 },
    { subject: 'Communication', value: analytics?.category_averages?.communication ?? 0 },
  ].filter((d) => d.value > 0)

  const TrendIcon = analytics?.improvement_trend === 'Improving' ? TrendingUp :
                    analytics?.improvement_trend === 'Declining' ? TrendingDown : Minus

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="section-title">Analytics</h1>
        <p className="section-subtitle">AI-generated assessment scores across your interview sessions.</p>
      </div>

      {noData ? (
        <div className="card p-10 text-center">
          <p className="text-gray-500 mb-4">No completed interviews yet.</p>
          <button className="btn-primary" onClick={() => navigate('/interview/setup')}>Start Your First Interview</button>
        </div>
      ) : (
        <>
          {/* Summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{analytics.total_interviews}</p>
              <p className="text-xs text-gray-500 mt-1">Interviews</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{analytics.average_score?.toFixed(1) ?? '—'}</p>
              <p className="text-xs text-gray-500 mt-1">Average Score</p>
            </div>
            <div className="card p-4 text-center">
              <p className="text-2xl font-bold text-purple-600">{analytics.best_score?.toFixed(1) ?? '—'}</p>
              <p className="text-xs text-gray-500 mt-1">Best Score</p>
            </div>
            <div className="card p-4 text-center flex flex-col items-center justify-center gap-1">
              <TrendIcon size={24} className={
                analytics.improvement_trend === 'Improving' ? 'text-green-500' :
                analytics.improvement_trend === 'Declining' ? 'text-red-500' : 'text-gray-400'
              } />
              <p className="text-xs text-gray-500">{analytics.improvement_trend}</p>
            </div>
          </div>

          {/* Score history */}
          {analytics.score_history?.length > 1 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 text-sm mb-4">Score Progression</h2>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={analytics.score_history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => [`${v}/10`, 'Score']} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#3b82f6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Category scores */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <ScoreCard label="Technical" score={analytics.category_averages?.technical} color="purple" />
            <ScoreCard label="HR" score={analytics.category_averages?.hr} color="green" />
            <ScoreCard label="Behavioral" score={analytics.category_averages?.behavioral} color="orange" />
            <ScoreCard label="Communication" score={analytics.category_averages?.communication} color="blue" />
          </div>

          {/* Radar chart */}
          {radarData.length >= 3 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 text-sm mb-4">Skill Radar</h2>
              <ResponsiveContainer width="100%" height={220}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                  <Radar
                    dataKey="value"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Weak areas */}
          {analytics.weak_skill_areas?.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 text-sm mb-3">Weak Skill Areas</h2>
              <div className="flex flex-wrap gap-2">
                {analytics.weak_skill_areas.map((a, i) => (
                  <span key={i} className="badge bg-red-50 text-red-700">{a}</span>
                ))}
              </div>
              <button
                className="btn-secondary text-xs mt-4 py-1.5 px-3"
                onClick={() => navigate('/preparation')}
              >
                Get Preparation Plan
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
