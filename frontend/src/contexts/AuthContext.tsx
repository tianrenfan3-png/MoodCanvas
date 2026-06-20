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
      // GitHub Pages only serves a 200 for the base URL (e.g. /MoodCanvas/).
      // Every other path (e.g. /MoodCanvas/login) returns 404. Firebase's auth
      // handler at firebaseapp.com makes a verification GET to the redirect-back
      // URL before completing OAuth — if that GET returns 404 it aborts the flow.
      //
      // To work around this, signInWithGoogle() stores a flag in sessionStorage
      // and navigates the browser to the base URL (200). This effect then detects
      // that flag and fires signInWithRedirect from the base URL so Firebase will
      // redirect back to a URL that actually returns 200.
      if (sessionStorage.getItem('__mc_signin_pending')) {
        sessionStorage.removeItem('__mc_signin_pending')
        // Fire and forget — the browser will navigate away immediately.
        signInWithRedirect(auth, googleProvider)
        return
      }

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
    // We cannot call signInWithRedirect from /login because GitHub Pages returns
    // 404 for that path, and Firebase's handler verifies the redirect-back URL
    // returns 200 before completing OAuth (if it gets 404 it aborts).
    // Solution: set a flag, navigate to the base URL (which returns 200), and
    // let the AuthProvider's useEffect pick up the flag and fire signInWithRedirect
    // from there so Firebase redirects back to a URL that returns 200.
    sessionStorage.setItem('__mc_signin_pending', '1')
    window.location.replace(import.meta.env.BASE_URL || '/')
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
