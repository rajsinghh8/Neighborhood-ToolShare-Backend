import { GraduationCap, UserPlus, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { ROUTES } from '../constants'

const navItems = [
  { label: 'Students', to: ROUTES.students, icon: Users },
  { label: 'Add Student', to: ROUTES.newStudent, icon: UserPlus },
]

export default function Sidebar() {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-surface">
      <div className="flex h-16 items-center gap-2 border-b border-line px-6">
        <GraduationCap className="h-6 w-6 text-primary" />
        <span className="text-base font-bold text-ink">EduManage</span>
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 font-medium transition-colors ${
                isActive ? 'bg-primary text-white' : 'text-secondary hover:bg-background'
              }`
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
