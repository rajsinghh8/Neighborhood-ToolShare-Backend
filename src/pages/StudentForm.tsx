import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import toast from 'react-hot-toast'
import { useNavigate, useParams } from 'react-router-dom'
import FormInput from '../components/FormInput'
import { ROUTES } from '../constants'
import { createStudent, getClasses, getStudent, getStudents, updateStudent } from '../data/store'
import type { ClassLevel } from '../types'
import {
  validateClassLevel,
  validateOptionalEmail,
  validateOptionalPhone,
  validateRequired,
} from '../validation'

export default function StudentForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const [classes, setClasses] = useState<ClassLevel[]>([])
  const [isLoading, setIsLoading] = useState(isEdit)
  const [name, setName] = useState('')
  const [classLevel, setClassLevel] = useState(1)
  const [rollNumber, setRollNumber] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [rollConflict, setRollConflict] = useState('')
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    getClasses().then(setClasses)
  }, [])

  useEffect(() => {
    if (!id) return
    getStudent(id).then((student) => {
      if (student) {
        setName(student.name)
        setClassLevel(student.classLevel)
        setRollNumber(student.rollNumber)
        setEmail(student.email)
        setPhone(student.phone)
        setAddress(student.address)
        setDateOfBirth(student.dateOfBirth)
      }
      setIsLoading(false)
    })
  }, [id])

  const errors = {
    name: validateRequired(name, 'Name'),
    rollNumber: validateRequired(rollNumber, 'Roll number') || rollConflict,
    classLevel: validateClassLevel(classLevel),
    email: validateOptionalEmail(email),
    phone: validateOptionalPhone(phone),
  }
  const isValid = Object.values(errors).every((message) => !message)

  function show(message: string): string {
    return hasSubmitted ? message : ''
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setHasSubmitted(true)
    if (!isValid || isSaving) return

    const existing = await getStudents()
    const duplicate = existing.some(
      (student) =>
        student.id !== id &&
        student.classLevel === classLevel &&
        student.rollNumber.toLowerCase() === rollNumber.trim().toLowerCase(),
    )
    if (duplicate) {
      setRollConflict('This roll number is already used in this class')
      return
    }

    setIsSaving(true)
    const input = {
      name: name.trim(),
      rollNumber: rollNumber.trim(),
      classLevel,
      email: email.trim(),
      phone: phone.trim(),
      address: address.trim(),
      dateOfBirth,
    }
    try {
      if (id) {
        await updateStudent(id, input)
        toast.success('Student updated')
        navigate(ROUTES.studentDetail(id))
      } else {
        const created = await createStudent(input)
        toast.success('Student created')
        navigate(ROUTES.studentDetail(created.id))
      }
    } catch {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <div className="h-64 animate-pulse rounded-xl bg-line" aria-label="Loading form" />
  }

  return (
    <div className="max-w-2xl">
      <h2 className="mb-6 text-2xl font-bold">{isEdit ? 'Edit student' : 'Add student'}</h2>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="space-y-4 rounded-xl border border-line bg-surface p-6"
      >
        <FormInput
          label="Full name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          error={show(errors.name)}
          placeholder="e.g. Aarav Sharma"
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="class-level" className="mb-1 block text-xs font-semibold">
              Class
            </label>
            <select
              id="class-level"
              value={classLevel}
              onChange={(event) => {
                setClassLevel(Number(event.target.value))
                setRollConflict('')
              }}
              className="w-full rounded-lg border border-line bg-surface px-3 py-2 outline-none focus:border-primary"
            >
              {classes.map((item) => (
                <option key={item.level} value={item.level}>
                  {item.name}
                </option>
              ))}
            </select>
            {show(errors.classLevel) && (
              <p className="mt-1 text-xs text-danger">{errors.classLevel}</p>
            )}
          </div>
          <FormInput
            label="Roll number"
            value={rollNumber}
            onChange={(event) => {
              setRollNumber(event.target.value)
              setRollConflict('')
            }}
            error={show(errors.rollNumber)}
            helper="Must be unique within the class"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormInput
            label="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            error={show(errors.email)}
            helper="Optional, must be a valid email"
          />
          <FormInput
            label="Phone"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            error={show(errors.phone)}
            helper="Optional, 7-15 digits"
          />
        </div>
        <FormInput
          label="Date of birth"
          type="date"
          value={dateOfBirth}
          onChange={(event) => setDateOfBirth(event.target.value)}
        />
        <FormInput
          label="Address"
          value={address}
          onChange={(event) => setAddress(event.target.value)}
        />
        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate(id ? ROUTES.studentDetail(id) : ROUTES.students)}
            className="rounded-lg border border-line px-4 py-2 font-semibold text-secondary hover:bg-background"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!isValid || isSaving}
            className="rounded-lg bg-primary px-4 py-2 font-semibold text-white hover:bg-primary-dark disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : isEdit ? 'Save changes' : 'Create student'}
          </button>
        </div>
      </form>
    </div>
  )
}
