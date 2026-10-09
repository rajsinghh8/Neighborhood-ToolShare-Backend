import { ArrowLeft, Pencil, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ConfirmDialog from '../components/ConfirmDialog'
import { ROUTES } from '../constants'
import { deleteStudent, getStudent } from '../data/store'
import type { Student } from '../types'
import { formatDate, getInitials } from '../utils'

export default function StudentDetail() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const [student, setStudent] = useState<Student | undefined>()
  const [isLoading, setIsLoading] = useState(true)
  const [isConfirmOpen, setIsConfirmOpen] = useState(false)

  useEffect(() => {
    getStudent(id).then((result) => {
      setStudent(result)
      setIsLoading(false)
    })
  }, [id])

  async function handleDelete() {
    if (!student) return
    await deleteStudent(student.id)
    toast.success(`${student.name} was deleted`)
    navigate(ROUTES.students)
  }

  if (isLoading) {
    return <div className="h-64 animate-pulse rounded-xl bg-line" aria-label="Loading student" />
  }

  if (!student) {
    return (
      <div className="rounded-xl border border-line bg-surface p-12 text-center">
        <p className="text-secondary">Student not found.</p>
        <Link to={ROUTES.students} className="mt-3 inline-block font-semibold text-primary">
          Back to students
        </Link>
      </div>
    )
  }

  const sections = [
    {
      title: 'Personal information',
      rows: [
        ['Full name', student.name],
        ['Date of birth', formatDate(student.dateOfBirth)],
        ['Address', student.address || '—'],
      ],
    },
    {
      title: 'Class assignment',
      rows: [
        ['Class', `Class ${student.classLevel}`],
        ['Roll number', student.rollNumber],
      ],
    },
    {
      title: 'Contact details',
      rows: [
        ['Email', student.email || '—'],
        ['Phone', student.phone || '—'],
      ],
    },
  ]

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate(ROUTES.students)}
        className="mb-4 flex items-center gap-2 font-semibold text-secondary hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to students
      </button>

      <div className="mb-6 flex items-center justify-between rounded-xl border border-line bg-surface p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-xl font-bold text-white">
            {getInitials(student.name)}
          </div>
          <div>
            <h2 className="text-2xl font-bold">{student.name}</h2>
            <p className="text-secondary">
              Class {student.classLevel} · Roll {student.rollNumber}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => navigate(ROUTES.editStudent(student.id))}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 font-semibold text-white hover:bg-primary-dark"
          >
            <Pencil className="h-4 w-4" />
            Edit
          </button>
          <button
            type="button"
            onClick={() => setIsConfirmOpen(true)}
            className="flex items-center gap-2 rounded-lg border border-danger px-4 py-2 font-semibold text-danger hover:bg-danger/10"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {sections.map((section) => (
          <section key={section.title} className="rounded-xl border border-line bg-surface p-6">
            <h3 className="mb-4 text-base font-semibold">{section.title}</h3>
            <dl className="space-y-3">
              {section.rows.map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs text-secondary">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>

      <ConfirmDialog
        isOpen={isConfirmOpen}
        title="Delete student?"
        message={`This will permanently remove ${student.name}. This cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setIsConfirmOpen(false)}
      />
    </div>
  )
}
