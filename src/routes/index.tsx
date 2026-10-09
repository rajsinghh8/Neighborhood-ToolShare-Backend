import { Navigate, createBrowserRouter } from 'react-router-dom'
import App from '../App'
import NotFound from '../pages/NotFound'
import StudentDetail from '../pages/StudentDetail'
import StudentForm from '../pages/StudentForm'
import StudentList from '../pages/StudentList'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/students" replace /> },
      { path: 'students', element: <StudentList /> },
      { path: 'students/new', element: <StudentForm /> },
      { path: 'students/:id', element: <StudentDetail /> },
      { path: 'students/:id/edit', element: <StudentForm /> },
    ],
  },
  { path: '*', element: <NotFound /> },
])
