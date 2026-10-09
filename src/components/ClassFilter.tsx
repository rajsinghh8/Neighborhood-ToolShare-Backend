import type { ClassLevel } from '../types'

interface ClassFilterProps {
  classes: ClassLevel[]
  value: number | 'all'
  onChange: (value: number | 'all') => void
}

export default function ClassFilter({ classes, value, onChange }: ClassFilterProps) {
  return (
    <select
      aria-label="Filter by class"
      value={value}
      onChange={(event) =>
        onChange(event.target.value === 'all' ? 'all' : Number(event.target.value))
      }
      className="rounded-lg border border-line bg-surface px-3 py-2 outline-none focus:border-primary"
    >
      <option value="all">All classes</option>
      {classes.map((item) => (
        <option key={item.level} value={item.level}>
          {item.name}
        </option>
      ))}
    </select>
  )
}
