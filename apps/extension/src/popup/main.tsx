import React from 'react'
import ReactDOM from 'react-dom/client'
import App from '../App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <div className="w-[400px] h-[600px] bg-slate-50">
            <App />
        </div>
    </React.StrictMode>,
)
