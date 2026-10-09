import { Eye, Pencil, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { ROUTES } from '../constants'
import type { Student } from '../types'

interface StudentTableProps {
  students: Student[]
  onDelete: (student: Student) => void
}

export default function StudentTable({ students, onDelete }: StudentTableProps) {
  const navigate = useNavigate()

  return (
    <table className="w-full text-left">
      <thead className="border-b border-line bg-background text-xs uppercase text-secondary">
        <tr>
          <th className="px-4 py-3">Roll No.</th>
          <th className="px-4 py-3">Name</th>
          <th className="px-4 py-3">Class</th>
          <th className="px-4 py-3">Email</th>
          <th className="px-4 py-3">Phone</th>
          <th className="px-4 py-3 text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        {students.map((student) => (
          <tr
            key={student.id}
            onClick={() => navigate(ROUTES.studentDetail(student.id))}
            className="cursor-pointer border-b border-line last:border-0 hover:bg-background"
          >
            <td className="px-4 py-3 font-medium">{student.rollNumber}</td>
            <td className="px-4 py-3">{student.name}</td>
            <td className="px-4 py-3">Class {student.classLevel}</td>
            <td className="px-4 py-3 text-secondary">{student.email || '—'}</td>
            <td className="px-4 py-3 text-secondary">{student.phone || '—'}</td>
            <td className="px-4 py-3">
              <div className="flex justify-end gap-1">
                <button
                  type="button"
                  aria-label={`View ${student.name}`}
                  onClick={(event) => {
                    event.stopPropagation()
                    navigate(ROUTES.studentDetail(student.id))
                  }}
                  className="rounded p-2 text-secondary hover:bg-line"
                >
                  <Eye className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  aria-label={`Edit ${student.name}`}
                  onClick={(event) => {
                    event.stopPropagation()
                    navigate(ROUTES.editStudent(student.id))
                  }}
                  className="rounded p-2 text-primary hover:bg-line"
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  aria-label={`Delete ${student.name}`}
                  onClick={(event) => {
                    event.stopPropagation()
                    onDelete(student)
                  }}
                  className="rounded p-2 text-danger hover:bg-line"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
