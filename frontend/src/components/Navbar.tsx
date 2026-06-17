import { Link, useLocation } from 'react-router-dom'
import { Moon, Sun, LogOut, Palette, History, Settings } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

export function Navbar() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()

  const navLink = (to: string, label: string, Icon: typeof Palette) => {
    const active = location.pathname === to
    return (
      <Link
        to={to}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
          active
            ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300'
            : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
        }`}
        aria-current={active ? 'page' : undefined}
      >
        <Icon size={16} aria-hidden />
        {label}
      </Link>
    )
  }

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 dark:border-slate-700 bg-[var(--color-surface)]/90 backdrop-blur-sm">
      <nav className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between" aria-label="Main">
        <Link to="/" className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Palette size={20} className="text-indigo-500" aria-hidden />
          MoodCanvas
        </Link>

        <div className="flex items-center gap-1">
          {navLink('/', 'Draw', Palette)}
          {navLink('/history', 'History', History)}
          {navLink('/settings', 'Settings', Settings)}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {user && (
            <>
              {user.photoURL && (
                <img
                  src={user.photoURL}
                  alt=""
                  className="w-7 h-7 rounded-full"
                  aria-hidden
                />
              )}
              <button
                onClick={() => logout()}
                className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                aria-label="Sign out"
              >
                <LogOut size={18} />
              </button>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
