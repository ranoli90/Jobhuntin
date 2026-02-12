import { useEffect, useState } from 'react'
import { Briefcase, LogOut } from 'lucide-react'
import { Login } from './popup/Login'

function App() {
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Initial check
    chrome.storage.local.get(['auth_token'], (data) => {
      setToken(data.auth_token || null)
      setLoading(false)
    })

    // Listen for SYNC_SESSION storage changes from the background/content script
    const storageListener = (changes: Record<string, chrome.storage.StorageChange>, area: string) => {
      if (area === 'local' && changes.auth_token) {
        setToken(changes.auth_token.newValue || null)
      }
    }
    chrome.storage.onChanged.addListener(storageListener)

    return () => {
      chrome.storage.onChanged.removeListener(storageListener)
    }
  }, [])

  const handleLogout = async () => {
    await chrome.storage.local.remove(['auth_token', 'session_active'])
    setToken(null)
  }

  if (loading) {
    return <div className="p-10 flex justify-center"><div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full" /></div>
  }

  if (!token) {
    return <Login onLogin={() => {
      chrome.storage.local.get(['auth_token'], (data) => {
        setToken(data.auth_token || null)
      })
    }} />
  }

  return (
    <div className="p-4 w-80">
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 text-white p-2 rounded-lg">
            <Briefcase size={20} />
          </div>
          <h1 className="text-xl font-bold text-slate-900">Sorce</h1>
        </div>
        <button onClick={handleLogout} className="text-slate-400 hover:text-slate-600 p-1 hover:bg-slate-100 rounded-lg transition-colors">
          <LogOut size={18} />
        </button>
      </header>

      <main>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 text-center">
          <div className="mb-4">
            <div className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded inline-block">
              Connected
            </div>
          </div>
          <p className="text-slate-600 mb-4">Navigate to a supported job site (LinkedIn, Indeed) to capture jobs.</p>
        </div>
      </main>
    </div>
  )
}

export default App
