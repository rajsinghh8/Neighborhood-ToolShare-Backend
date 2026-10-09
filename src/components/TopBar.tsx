export default function TopBar() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-line bg-surface px-8">
      <h1 className="text-lg font-semibold text-ink">Student Management System</h1>
      <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
        Classes 1–12
      </span>
    </header>
  )
}
