export interface Student {
  id: string
  name: string
  rollNumber: string
  classLevel: number
  email: string
  phone: string
  address: string
  dateOfBirth: string
  createdAt: string
  updatedAt: string
}

export type StudentInput = Omit<Student, 'id' | 'createdAt' | 'updatedAt'>

export interface ClassLevel {
  level: number
  name: string
}
