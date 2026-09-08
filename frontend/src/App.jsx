import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import ProfileSetup from './pages/ProfileSetup'
import ResumeUpload from './pages/ResumeUpload'
import InterviewSetup from './pages/InterviewSetup'
import LiveInterview from './pages/LiveInterview'
import InterviewReport from './pages/InterviewReport'
import Analytics from './pages/Analytics'
import InterviewHistory from './pages/InterviewHistory'
import PreparationPlan from './pages/PreparationPlan'
import Layout from './components/Layout'

export default function App() {
  return (
    <BrowserRouter basename="/ai-interview-trainer">
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<ProfileSetup />} />
          <Route path="/resume" element={<ResumeUpload />} />
          <Route path="/interview/setup" element={<InterviewSetup />} />
          <Route path="/interview/:id" element={<LiveInterview />} />
          <Route path="/interview/:id/report" element={<InterviewReport />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/history" element={<InterviewHistory />} />
          <Route path="/preparation" element={<PreparationPlan />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
