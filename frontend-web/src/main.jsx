import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Suppress browser extension errors
window.addEventListener('error', (event) => {
  if (event.message && event.message.includes('message channel closed')) {
    event.preventDefault();
    return true;
  }
});

window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && event.reason.message.includes('message channel closed')) {
    event.preventDefault();
    return true;
  }
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)