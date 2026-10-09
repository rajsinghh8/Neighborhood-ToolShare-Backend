// MOCK DATA — placeholder records for local development only.
// Replace with real API data before production use.
import type { ClassLevel, Student } from '../types'

export const mockClasses: ClassLevel[] = Array.from({ length: 12 }, (_, index) => ({
  level: index + 1,
  name: `Class ${index + 1}`,
}))

const names = [
  'Aarav Sharma', 'Isha Patel', 'Liam Johnson', 'Sofia Garcia', 'Noah Williams',
  'Mei Chen', 'Omar Hassan', 'Emma Brown', 'Arjun Singh', 'Olivia Davis',
  'Lucas Martin', 'Zara Khan', 'Ethan Wilson', 'Priya Nair', 'Mia Anderson',
  'Kabir Mehta', 'Ava Thomas', 'Daniel Lee', 'Fatima Ali', 'Jack Taylor',
]

export const mockStudents: Student[] = names.map((name, index) => {
  const classLevel = (index % 12) + 1
  const first = name.split(' ')[0].toLowerCase()
  return {
    id: `s${index + 1}`,
    name,
    rollNumber: String(100 + index + 1),
    classLevel,
    email: `${first}@school.example`,
    phone: `+1 555 01${String(index).padStart(2, '0')}`,
    address: `${10 + index} Maple Street, Springfield`,
    dateOfBirth: `${2018 - classLevel - 5}-0${(index % 9) + 1}-1${index % 9}`,
    createdAt: '2024-06-01T09:00:00.000Z',
    updatedAt: '2024-06-01T09:00:00.000Z',
  }
})
