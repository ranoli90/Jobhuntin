import { ExternalLink } from 'lucide-react'
import { useEffect } from 'react'

export function Login({ onLogin }: { onLogin: () => void }) {
    // Poll for session in case it syncs while popup is open
    useEffect(() => {
        const checkSession = async () => {
            const data = await chrome.storage.local.get(['session']);
            if (data.session) {
                onLogin();
            }
        };
        const interval = setInterval(checkSession, 1000);
        return () => clearInterval(interval);
    }, [onLogin]);

    const openWebApp = () => {
        chrome.tabs.create({ url: 'http://localhost:5173/login' });
        // In prod: chrome.tabs.create({ url: 'https://jobhuntin.com/login' });
    };

    return (
        <div className="flex flex-col items-center justify-center p-6 text-center space-y-6">
            <div className="space-y-2">
                <h2 className="text-xl font-bold text-slate-900">Sign in to Sorce</h2>
                <p className="text-sm text-slate-500">
                    Connect your account to sync jobs to your dashboard.
                </p>
            </div>

            <div className="w-full space-y-4">
                <button
                    onClick={openWebApp}
                    className="w-full bg-blue-600 text-white py-3 rounded-xl text-sm font-bold hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all flex items-center justify-center gap-2"
                >
                    Open Dashboard to Login
                    <ExternalLink size={16} />
                </button>

                <p className="text-xs text-slate-400">
                    Once you log in on the web app, this extension will automatically connect.
                </p>
            </div>
        </div>
    )
}
