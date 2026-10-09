export const ROUTES = {
  students: '/students',
  newStudent: '/students/new',
  studentDetail: (id: string) => `/students/${id}`,
  editStudent: (id: string) => `/students/${id}/edit`,
}

export const PAGE_SIZE = 8
