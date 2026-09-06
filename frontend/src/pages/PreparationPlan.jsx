import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPreparationPlans, generatePreparationPlan } from '../services/api'
import { LoadingSpinner, ErrorMessage, DemoNotice } from '../components/UI'
import { BookOpen, Calendar, RefreshCw } from 'lucide-react'

export default function PreparationPlan() {
  const navigate = useNavigate()
  const [plans, setPlans] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)
  const [selectedPlanIdx, setSelectedPlanIdx] = useState(0)

  const loadPlans = async () => {
    try {
      const data = await getPreparationPlans(1)
      setPlans(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPlans()
  }, [])

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    try {
      await generatePreparationPlan(1, '')
      await loadPlans()
      setSelectedPlanIdx(0)
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSpinner label="Loading preparation plans..." />
  if (error) return <ErrorMessage message={error} onRetry={loadPlans} />

  const plan = plans[selectedPlanIdx]
  const dailyPlan = plan?.daily_plan || []
  const recommendations = plan?.recommendations || []

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">Preparation Plan</h1>
          <p className="section-subtitle">Personalised study plan based on your interview performance.</p>
        </div>
        <button
          className="btn-secondary flex items-center gap-2 text-sm"
          onClick={handleGenerate}
          disabled={generating}
        >
          <RefreshCw size={14} className={generating ? 'animate-spin' : ''} />
          {generating ? 'Generating...' : 'Generate New Plan'}
        </button>
      </div>

      {plans.length === 0 ? (
        <div className="card p-10 text-center">
          <BookOpen size={40} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-2">No preparation plan yet.</p>
          <p className="text-xs text-gray-400 mb-4">
            Complete an interview to get a personalised plan, or generate one manually.
          </p>
          <div className="flex gap-3 justify-center">
            <button className="btn-primary" onClick={() => navigate('/interview/setup')}>
              Start Interview
            </button>
            <button className="btn-secondary" onClick={handleGenerate} disabled={generating}>
              {generating ? 'Generating...' : 'Generate Plan'}
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Plan selector */}
          {plans.length > 1 && (
            <div className="flex gap-2 flex-wrap">
              {plans.map((p, i) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPlanIdx(i)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    selectedPlanIdx === i
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 text-gray-600 hover:border-gray-300'
                  }`}
                >
                  Plan {plans.length - i} · {new Date(p.created_at).toLocaleDateString()}
                </button>
              ))}
            </div>
          )}

          {plan?.weak_areas?.length > 0 && (
            <div className="card p-4">
              <p className="text-xs font-semibold text-red-600 mb-2">Identified Weak Areas</p>
              <div className="flex flex-wrap gap-2">
                {plan.weak_areas.map((a, i) => (
                  <span key={i} className="badge bg-red-50 text-red-700">{a}</span>
                ))}
              </div>
            </div>
          )}

          {/* Daily plan */}
          {dailyPlan.length > 0 && (
            <div>
              <h2 className="font-semibold text-gray-900 text-sm mb-3 flex items-center gap-2">
                <Calendar size={15} className="text-blue-600" /> 7-Day Study Plan
              </h2>
              <div className="space-y-3">
                {dailyPlan.map((day, i) => (
                  <div key={i} className="card p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0">
                        D{day.day}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900 text-sm">{day.focus}</p>
                        <p className="text-xs text-blue-600">Day {day.day}</p>
                      </div>
                    </div>

                    {day.activities?.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-600 mb-1.5">Activities</p>
                        <ul className="space-y-1">
                          {day.activities.map((act, ai) => (
                            <li key={ai} className="text-xs text-gray-700 flex items-start gap-2">
                              <span className="text-blue-400 mt-0.5">→</span> {act}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {day.resources?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-gray-600 mb-1.5">Resources</p>
                        <div className="flex flex-wrap gap-1.5">
                          {day.resources.map((r, ri) => (
                            <span key={ri} className="badge bg-gray-100 text-gray-600">{r}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 text-sm mb-3">Overall Recommendations</h2>
              <ul className="space-y-2">
                {recommendations.map((r, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2.5">
                    <span className="text-blue-500 mt-0.5 font-bold">{i + 1}.</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {plan?.topics?.length > 0 && (
            <div className="card p-4">
              <p className="text-xs font-semibold text-gray-700 mb-2">Priority Topics</p>
              <div className="flex flex-wrap gap-2">
                {plan.topics.map((t, i) => (
                  <span key={i} className="badge bg-blue-50 text-blue-700">{t}</span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
