import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  onAuthStateChanged,
  signInWithRedirect,
  getRedirectResult,
  signOut,
  type User,
} from 'firebase/auth'
import { auth, googleProvider, isFirebaseConfigured } from '../lib/firebase'

interface AuthContextValue {
  user: User | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  logout: () => Promise<void>
  isConfigured: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(isFirebaseConfigured)

  useEffect(() => {
    if (!isFirebaseConfigured) return

    let unsubscribeAuth: (() => void) | undefined
    let cancelled = false

    async function init() {
      // Await the redirect result FIRST so Firebase has time to exchange the
      // OAuth code and update the auth state before we start listening.
      // Without this await, onAuthStateChanged fires with null immediately
      // (before the credential is processed), loading goes false, and the
      // login page flashes before the user is recognised.
      try {
        await getRedirectResult(auth)
      } catch (err) {
        console.error('Redirect sign-in error:', err)
      }

      if (cancelled) return

      unsubscribeAuth = onAuthStateChanged(auth, (u) => {
        setUser(u)
        setLoading(false)
      })
    }

    init()

    return () => {
      cancelled = true
      unsubscribeAuth?.()
    }
  }, [])

  const signInWithGoogle = async () => {
    // Use redirect instead of popup — GitHub Pages sets COOP: same-origin
    // which severs the popup's postMessage channel, breaking signInWithPopup.
    await signInWithRedirect(auth, googleProvider)
  }

  const logout = async () => {
    await signOut(auth)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signInWithGoogle,
        logout,
        isConfigured: isFirebaseConfigured,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
