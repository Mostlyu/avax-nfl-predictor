import React from 'react'
import { createRoot } from 'react-dom/client'
import { createConfig, WagmiProvider, http } from 'wagmi'
import { avalanche } from 'wagmi/chains'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// Create wagmi config
const config = createConfig({
  chains: [avalanche],
  transports: {
    [avalanche.id]: http('https://api.avax.network/ext/bc/C/rpc')
  }
})

// Create a client
const queryClient = new QueryClient()

// Error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('React error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-red-600">
          <h1>Something went wrong.</h1>
          <pre>{String(this.state.error)}</pre>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <WagmiProvider config={config}>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </WagmiProvider>
    </ErrorBoundary>
  </React.StrictMode>
)