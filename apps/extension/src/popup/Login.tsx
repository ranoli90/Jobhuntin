import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { Loader2 } from 'lucide-react'

export function Login({ onLogin }: { onLogin: () => void }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        })

        if (error) {
            setError(error.message)
            setLoading(false)
        } else {
            onLogin()
        }
    }

    return (
        <div className="flex flex-col items-center justify-center p-6 text-center space-y-6">
            <div>
                <h2 className="text-lg font-bold text-slate-900">Sign in to Sorce</h2>
                <p className="text-sm text-slate-500">Access your job dashboard</p>
            </div>

            <form onSubmit={handleLogin} className="w-full space-y-4">
                <div className="space-y-2">
                    <input
                        type="email"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                </div>

                {error && <div className="text-xs text-red-500">{error}</div>}

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                    {loading && <Loader2 className="animate-spin h-4 w-4" />}
                    Sign In
                </button>
            </form>
        </div>
    )
}
