import { test } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StudentList from './StudentList'

test('renders without crashing', () => {
  render(
    <MemoryRouter>
      <StudentList />
    </MemoryRouter>,
  )
})
