import { test } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StudentDetail from './StudentDetail'

test('renders without crashing', () => {
  render(
    <MemoryRouter>
      <StudentDetail />
    </MemoryRouter>,
  )
})
