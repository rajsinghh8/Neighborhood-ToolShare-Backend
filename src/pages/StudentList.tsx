import { Plus, Search } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import ClassFilter from '../components/ClassFilter'
import ConfirmDialog from '../components/ConfirmDialog'
import StudentTable from '../components/StudentTable'
import { PAGE_SIZE, ROUTES } from '../constants'
import { deleteStudent, getClasses, getStudents } from '../data/store'
import type { ClassLevel, Student } from '../types'

type SortKey = 'name' | 'rollNumber'

export default function StudentList() {
  const navigate = useNavigate()
  const [students, setStudents] = useState<Student[]>([])
  const [classes, setClasses] = useState<ClassLevel[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [classFilter, setClassFilter] = useState<number | 'all'>('all')
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [page, setPage] = useState(1)
  const [pendingDelete, setPendingDelete] = useState<Student | null>(null)

  const loadData = useCallback(async () => {
    const [studentData, classData] = await Promise.all([getStudents(), getClasses()])
    setStudents(studentData)
    setClasses(classData)
    setIsLoading(false)
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return students
      .filter((student) => classFilter === 'all' || student.classLevel === classFilter)
      .filter(
        (student) =>
          !term ||
          student.name.toLowerCase().includes(term) ||
          student.rollNumber.toLowerCase().includes(term),
      )
      .sort((first, second) =>
        first[sortKey].localeCompare(second[sortKey], undefined, { numeric: true }),
      )
  }, [students, search, classFilter, sortKey])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  async function handleConfirmDelete() {
    if (!pendingDelete) return
    await deleteStudent(pendingDelete.id)
    toast.success(`${pendingDelete.name} was deleted`)
    setPendingDelete(null)
    await loadData()
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Students</h2>
          <p className="text-secondary">{students.length} students across classes 1–12</p>
        </div>
        <button
          type="button"
          onClick={() => navigate(ROUTES.newStudent)}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 font-semibold text-white hover:bg-primary-dark"
        >
          <Plus className="h-4 w-4" />
          Add Student
        </button>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-secondary" />
          <input
            type="search"
            placeholder="Search by name or roll number"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
            className="w-full rounded-lg border border-line bg-surface py-2 pl-9 pr-3 outline-none focus:border-primary"
          />
        </div>
        <ClassFilter
          classes={classes}
          value={classFilter}
          onChange={(value) => {
            setClassFilter(value)
            setPage(1)
          }}
        />
        <select
          aria-label="Sort students"
          value={sortKey}
          onChange={(event) => setSortKey(event.target.value as SortKey)}
          className="rounded-lg border border-line bg-surface px-3 py-2 outline-none focus:border-primary"
        >
          <option value="name">Sort by name</option>
          <option value="rollNumber">Sort by roll number</option>
        </select>
      </div>

      <div className="overflow-hidden rounded-xl border border-line bg-surface">
        {isLoading ? (
          <div className="space-y-3 p-4" aria-label="Loading students">
            {Array.from({ length: 5 }, (_, index) => (
              <div key={index} className="h-10 animate-pulse rounded bg-line" />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <div className="p-12 text-center text-secondary">
            <p>No students found — add one to get started.</p>
            <button
              type="button"
              onClick={() => navigate(ROUTES.newStudent)}
              className="mt-3 font-semibold text-primary"
            >
              Add Student
            </button>
          </div>
        ) : (
          <StudentTable students={visible} onDelete={setPendingDelete} />
        )}
      </div>

      <div className="mt-4 flex items-center justify-between text-secondary">
        <span>
          Page {currentPage} of {totalPages} · {filtered.length} results
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={currentPage === 1}
            onClick={() => setPage(currentPage - 1)}
            className="rounded-lg border border-line bg-surface px-3 py-1.5 disabled:opacity-50"
          >
            Previous
          </button>
          <button
            type="button"
            disabled={currentPage === totalPages}
            onClick={() => setPage(currentPage + 1)}
            className="rounded-lg border border-line bg-surface px-3 py-1.5 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

      <ConfirmDialog
        isOpen={pendingDelete !== null}
        title="Delete student?"
        message={`This will permanently remove ${pendingDelete?.name ?? 'this student'}. This cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleConfirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  )
}
