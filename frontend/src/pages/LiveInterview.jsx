import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronRight, SkipForward, Send, CheckCircle2, AlertCircle } from 'lucide-react'
import {
  getInterview,
  getQuestions,
  getRagSources,
  submitAnswer,
  finishInterview,
} from '../services/api'
import { LoadingSpinner, ErrorMessage, ProgressBar, DemoNotice } from '../components/UI'

export default function LiveInterview() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [interview, setInterview] = useState(null)
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [followup, setFollowup] = useState(null)
  const [answeredCount, setAnsweredCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [finished, setFinished] = useState(false)
  const [finishing, setFinishing] = useState(false)
  const [isDemo, setIsDemo] = useState(false)
  const [ragSources, setRagSources] = useState([])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [iv, qs, rag] = await Promise.all([
          getInterview(id),
          getQuestions(id),
          getRagSources(id),
        ])

        setInterview(iv)
        setQuestions(qs)
        setRagSources(rag.sources || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Reload questions when a follow-up is added
  const reloadQuestions = async () => {
    const qs = await getQuestions(id)
    setQuestions(qs)
  }

  const currentQ = questions[currentIndex]

  const handleSubmit = async () => {
    if (!answer.trim()) {
      setError('Please write an answer before submitting.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const result = await submitAnswer(id, {
        question_id: currentQ.id,
        answer_text: answer,
        generate_followup: true,
      })
      setEvaluation(result.evaluation)
      setFollowup(result.followup_question)
      setAnsweredCount((c) => c + 1)
      setIsDemo(result.is_demo)
      if (result.followup_question) {
        await reloadQuestions()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleNext = () => {
    setEvaluation(null)
    setFollowup(null)
    setAnswer('')
    setError(null)
    if (currentIndex + 1 < questions.length) {
      setCurrentIndex(currentIndex + 1)
    } else {
      handleFinish()
    }
  }

  const handleSkip = () => {
    setEvaluation(null)
    setFollowup(null)
    setAnswer('')
    setError(null)
    if (currentIndex + 1 < questions.length) {
      setCurrentIndex(currentIndex + 1)
    } else {
      handleFinish()
    }
  }

  const handleFinish = async () => {
    setFinishing(true)
    try {
      await finishInterview(id)
      setFinished(true)
      setTimeout(() => navigate(`/interview/${id}/report`), 1200)
    } catch (err) {
      setError(err.message)
    } finally {
      setFinishing(false)
    }
  }

  if (loading) return <LoadingSpinner label="Loading interview..." />
  if (error && !currentQ) return <ErrorMessage message={error} onRetry={() => window.location.reload()} />

  if (finished) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20">
        <CheckCircle2 size={48} className="text-green-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Interview Complete!</h2>
        <p className="text-gray-500 text-sm">Generating your performance report...</p>
      </div>
    )
  }

  const totalQuestions = questions.length
  const answeredPct = totalQuestions > 0 ? Math.round((currentIndex / totalQuestions) * 100) : 0

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-bold text-gray-900">{interview?.target_role || 'Interview'}</h1>
          <div className="flex gap-2 mt-1">
            <span className="badge bg-blue-100 text-blue-700">{interview?.interview_type}</span>
            <span className="badge bg-gray-100 text-gray-700">{interview?.difficulty}</span>
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          Question {currentIndex + 1} / {totalQuestions}
        </div>
      </div>

      {isDemo && <DemoNotice />}

      {/* Progress */}
      <ProgressBar current={currentIndex} total={totalQuestions} label="Progress" />

      {/* Question */}
      {currentQ && !evaluation && (
        <div className="card p-6 space-y-5">
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5">
              Q{currentIndex + 1}
            </div>
            <div className="flex-1">
              <div className="flex flex-wrap gap-2 mb-3">
                {currentQ.category && (
                  <span className="badge bg-blue-50 text-blue-700">{currentQ.category}</span>
                )}
                {currentQ.difficulty && (
                  <span className="badge bg-gray-100 text-gray-700">{currentQ.difficulty}</span>
                )}
                {currentQ.is_followup === 1 && (
                  <span className="badge bg-amber-100 text-amber-700">Follow-up</span>
                )}
              </div>
              <p className="text-gray-900 leading-relaxed font-medium">{currentQ.question_text}</p>
              {ragSources.length > 0 && (
  <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
    <div className="flex items-center gap-2 mb-3">
      <span className="text-lg">📚</span>
      <p className="text-sm font-semibold text-purple-900">
        RAG Evidence Used
      </p>
    </div>

    <p className="text-xs text-purple-700 mb-3">
      This interview used retrieved knowledge-base context to generate AI questions.
    </p>

    <div className="space-y-2">
      {ragSources.map((source, index) => (
        <div
          key={`${source.source}-${source.category}-${index}`}
          className="flex items-center justify-between p-2 bg-white rounded border border-purple-100"
        >
          <span className="text-xs font-medium text-gray-700">
            {source.source}
          </span>

          <span className="badge bg-purple-100 text-purple-700">
            {source.category}
          </span>
        </div>
      ))}
    </div>
  </div>
)}
            </div>
          </div>

          <div>
            <label className="label">Your Answer</label>
            <textarea
              className="input-field resize-none"
              rows={6}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here. Be specific and provide examples where relevant..."
            />
            <p className="text-xs text-gray-400 mt-1">{answer.split(' ').filter(Boolean).length} words</p>
          </div>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              <AlertCircle size={15} className="mt-0.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              className="btn-primary flex items-center gap-2"
              onClick={handleSubmit}
              disabled={submitting || !answer.trim()}
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Evaluating with IBM Granite...
                </>
              ) : (
                <>
                  <Send size={15} /> Submit Answer
                </>
              )}
            </button>
            <button
              className="btn-secondary flex items-center gap-2"
              onClick={handleSkip}
              disabled={submitting}
            >
              <SkipForward size={15} /> Skip
            </button>
          </div>
        </div>
      )}

      {/* Evaluation feedback */}
      {evaluation && (
        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">AI Evaluation</h2>
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-bold ${
                  evaluation.score >= 7 ? 'text-green-600' :
                  evaluation.score >= 5 ? 'text-orange-500' : 'text-red-500'
                }`}>
                  {evaluation.score?.toFixed(1)}
                </span>
                <span className="text-gray-400 text-sm">/ 10</span>
              </div>
            </div>

            {/* Score bar */}
            <div className="h-2 bg-gray-100 rounded-full mb-5">
              <div
                className={`h-full rounded-full ${
                  evaluation.score >= 7 ? 'bg-green-500' :
                  evaluation.score >= 5 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${(evaluation.score / 10) * 100}%` }}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              {evaluation.strengths?.length > 0 && (
                <FeedbackList title="Strengths ✓" items={evaluation.strengths} color="green" />
              )}
              {evaluation.weaknesses?.length > 0 && (
                <FeedbackList title="Weaknesses ✗" items={evaluation.weaknesses} color="red" />
              )}
              {evaluation.missing_points?.length > 0 && (
                <FeedbackList title="What Was Missing" items={evaluation.missing_points} color="orange" />
              )}
              {evaluation.suggestions?.length > 0 && (
                <FeedbackList title="Suggestions" items={evaluation.suggestions} color="blue" />
              )}
            </div>

            {evaluation.model_answer && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs font-semibold text-blue-800 mb-1">Model Answer / Better Approach</p>
                <p className="text-xs text-blue-700 leading-relaxed">{evaluation.model_answer}</p>
              </div>
            )}

            {evaluation.key_concepts?.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-semibold text-gray-600 mb-2">Key Concepts to Revise</p>
                <div className="flex flex-wrap gap-1.5">
                  {evaluation.key_concepts.map((k, i) => (
                    <span key={i} className="badge bg-gray-100 text-gray-700">{k}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {followup && (
            <div className="card p-4 border-amber-200 bg-amber-50">
              <p className="text-xs font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
                <ChevronRight size={13} /> Adaptive Follow-up Question Added
              </p>
              <p className="text-sm text-amber-900">{followup.question_text}</p>
              {followup.reason && (
                <p className="text-xs text-amber-600 mt-1">{followup.reason}</p>
              )}
            </div>
          )}

          <div className="flex gap-3">
            <button className="btn-primary flex items-center gap-2" onClick={handleNext}>
              {currentIndex + 1 < questions.length ? (
                <><ChevronRight size={16} /> Next Question</>
              ) : (
                <><CheckCircle2 size={16} /> Finish Interview</>
              )}
            </button>
            {finishing && (
              <span className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                Generating report...
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function FeedbackList({ title, items, color }) {
  const colorMap = {
    green: 'text-green-700 bg-green-50',
    red: 'text-red-700 bg-red-50',
    orange: 'text-orange-700 bg-orange-50',
    blue: 'text-blue-700 bg-blue-50',
  }
  const cls = colorMap[color] || colorMap.blue
  return (
    <div className={`p-3 rounded-lg ${cls}`}>
      <p className="font-semibold text-xs mb-2">{title}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-xs flex items-start gap-1.5">
            <span className="mt-0.5">•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
