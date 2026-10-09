import { test } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StudentForm from './StudentForm'

test('renders without crashing', () => {
  render(
    <MemoryRouter>
      <StudentForm />
    </MemoryRouter>,
  )
})
