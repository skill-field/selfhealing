import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  Home,
  Eye,
  Brain,
  Wrench,
  Shield,
  Sparkles,
  FileText,
  Presentation,
  ChevronLeft,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home, color: 'text-gray-400' },
  { to: '/watch', label: 'Watch', icon: Eye, color: 'text-cyan-500' },
  { to: '/think', label: 'Think', icon: Brain, color: 'text-purple-500' },
  { to: '/heal', label: 'Heal', icon: Wrench, color: 'text-green-500' },
  { to: '/verify', label: 'Verify', icon: Shield, color: 'text-blue-500' },
  { to: '/evolve', label: 'Evolve', icon: Sparkles, color: 'text-amber-500' },
  { to: '/audit', label: 'Audit Log', icon: FileText, color: 'text-gray-400' },
  { to: '/presentation', label: 'Presentation', icon: Presentation, color: 'text-gray-400' },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={clsx(
        'flex flex-col border-r border-gray-800 bg-gray-950 transition-all duration-200',
        collapsed ? 'w-16' : 'w-56',
      )}
    >
      <div className="flex items-center justify-end p-3">
        <button
          onClick={onToggle}
          className="rounded-md p-1.5 text-gray-500 hover:bg-gray-800 hover:text-gray-300 transition-colors"
        >
          <ChevronLeft
            size={18}
            className={clsx('transition-transform', collapsed && 'rotate-180')}
          />
        </button>
      </div>

      <nav className="flex-1 space-y-1 px-2">
        {navItems.map(({ to, label, icon: Icon, color }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200',
              )
            }
          >
            <Icon size={20} className={color} />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
