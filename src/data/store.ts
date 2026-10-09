import apiClient from '../api/client'
import { mockClasses, mockStudents } from './mockData'
import type { ClassLevel, Student, StudentInput } from '../types'

const STORAGE_KEY = 'students'

function loadStudents(): Student[] {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw) return JSON.parse(raw) as Student[]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(mockStudents))
  return mockStudents
}

function saveStudents(students: Student[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(students))
}

// MOCK: stands in for GET /api/v1/students returning all student records.
function localGetStudents(): Student[] {
  return loadStudents()
}

// MOCK: stands in for GET /api/v1/students/:id returning one student.
function localGetStudent(id: string): Student | undefined {
  return loadStudents().find((student) => student.id === id)
}

// MOCK: stands in for POST /api/v1/students returning the created student.
function localCreateStudent(input: StudentInput): Student {
  const all = loadStudents()
  const now = new Date().toISOString()
  const student: Student = { ...input, id: crypto.randomUUID(), createdAt: now, updatedAt: now }
  all.unshift(student)
  saveStudents(all)
  return student
}

// MOCK: stands in for PUT /api/v1/students/:id returning the updated student.
function localUpdateStudent(id: string, input: StudentInput): Student | undefined {
  const all = loadStudents()
  const index = all.findIndex((student) => student.id === id)
  if (index === -1) return undefined
  all[index] = { ...all[index], ...input, updatedAt: new Date().toISOString() }
  saveStudents(all)
  return all[index]
}

// MOCK: stands in for DELETE /api/v1/students/:id.
function localDeleteStudent(id: string): void {
  saveStudents(loadStudents().filter((student) => student.id !== id))
}

// TODO(USE_MOCK): verify path + response shape against the real
// backend's OpenAPI schema before flipping this to false.
export const USE_MOCK = true

export async function getStudents(): Promise<Student[]> {
  if (USE_MOCK) return localGetStudents()
  const res = await apiClient.get('/api/v1/students')
  return res.data
}

export async function getStudent(id: string): Promise<Student | undefined> {
  if (USE_MOCK) return localGetStudent(id)
  const res = await apiClient.get(`/api/v1/students/${id}`)
  return res.data
}

export async function createStudent(input: StudentInput): Promise<Student> {
  if (USE_MOCK) return localCreateStudent(input)
  const res = await apiClient.post('/api/v1/students', input)
  return res.data
}

export async function updateStudent(id: string, input: StudentInput): Promise<Student | undefined> {
  if (USE_MOCK) return localUpdateStudent(id, input)
  const res = await apiClient.put(`/api/v1/students/${id}`, input)
  return res.data
}

export async function deleteStudent(id: string): Promise<void> {
  if (USE_MOCK) {
    localDeleteStudent(id)
    return
  }
  await apiClient.delete(`/api/v1/students/${id}`)
}

// TODO(USE_MOCK): verify path + response shape against the real
// backend's OpenAPI schema before flipping this to false.
export const USE_MOCK_CLASSES = true

export async function getClasses(): Promise<ClassLevel[]> {
  // MOCK: stands in for GET /api/v1/classes returning levels 1-12.
  if (USE_MOCK_CLASSES) return mockClasses
  const res = await apiClient.get('/api/v1/classes')
  return res.data
}
