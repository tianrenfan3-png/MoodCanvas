import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from '../pages/LoginPage'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    signInWithGoogle: vi.fn(),
    logout: vi.fn(),
    isConfigured: true,
  }),
}))

vi.mock('../contexts/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

describe('LoginPage', () => {
  it('shows sign-in and privacy note', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.getByText('MoodCanvas')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
    expect(screen.getByText(/sent to our server/i)).toBeInTheDocument()
  })
})

describe('Dashboard flow (types)', () => {
  it('defines mood categories for analysis results', async () => {
    const { MOODS } = await import('../types')
    expect(MOODS).toContain('Calm')
    expect(MOODS).toHaveLength(6)
  })
})
