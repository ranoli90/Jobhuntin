import { useEffect, useState } from 'react'
import { Briefcase, LogOut } from 'lucide-react'
import { supabase } from './lib/supabase'
import { Login } from './popup/Login'
import type { Session } from '@supabase/supabase-js'

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    // Listen for SYNC_SESSION storage changes from the background script
    // and hydrate the Supabase client so getSession() returns the synced session
    const storageListener = (changes: Record<string, chrome.storage.StorageChange>, area: string) => {
      if (area === 'local' && changes.session?.newValue) {
        const synced = changes.session.newValue as { access_token?: string; refresh_token?: string }
        if (synced.access_token && synced.refresh_token) {
          supabase.auth.setSession({
            access_token: synced.access_token,
            refresh_token: synced.refresh_token,
          }).then(({ data }) => {
            if (data.session) {
              setSession(data.session)
            }
          }).catch(() => {
            // If setSession fails, fall back to raw session object
            setSession(synced as any)
          })
        }
      }
    }
    chrome.storage.onChanged.addListener(storageListener)

    return () => {
      subscription.unsubscribe()
      chrome.storage.onChanged.removeListener(storageListener)
    }
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
  }

  if (loading) {
    return <div className="p-10 flex justify-center"><div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full" /></div>
  }

  if (!session) {
    return <Login onLogin={() => {
      // Re-check session from the Supabase client when Login detects a sync
      supabase.auth.getSession().then(({ data: { session: s } }) => {
        if (s) setSession(s)
      })
    }} />
  }

  return (
    <div className="p-4">
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 text-white p-2 rounded-lg">
            <Briefcase size={20} />
          </div>
          <h1 className="text-xl font-bold text-slate-900">Sorce</h1>
        </div>
        <button onClick={handleLogout} className="text-slate-400 hover:text-slate-600">
          <LogOut size={18} />
        </button>
      </header>

      <main>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 text-center">
          <div className="mb-4">
            <div className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded inline-block">
              Connected as {session.user.email}
            </div>
          </div>
          <p className="text-slate-600 mb-4">Navigate to a supported job site (LinkedIn, Indeed) to capture jobs.</p>

        </div>
      </main>
    </div>
  )
}

export default App
