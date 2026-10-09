import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3">
      <h1 className="text-5xl font-bold text-primary">404</h1>
      <p className="text-secondary">This page could not be found.</p>
      <Link to="/" className="rounded-lg bg-primary px-4 py-2 font-semibold text-white">
        Go Home
      </Link>
    </div>
  )
}
