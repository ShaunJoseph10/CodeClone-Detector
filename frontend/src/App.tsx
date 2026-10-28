import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import AssignmentPage from './pages/AssignmentPage'
import AstPage from './pages/AstPage'
import ComparePage from './pages/ComparePage'
import Dashboard from './pages/Dashboard'
import NotFound from './pages/NotFound'
import ResultsPage from './pages/ResultsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="assignments/:id" element={<AssignmentPage />} />
          <Route path="analyses/:id" element={<ResultsPage />} />
          <Route path="analyses/:analysisId/pairs/:pairId" element={<ComparePage />} />
          <Route path="submissions/:id/ast" element={<AstPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
