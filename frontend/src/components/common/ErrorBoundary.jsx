import { Component } from 'react'
import ErrorFallback from './ErrorFallback'

// A class because React has no hook for catching render errors (including a failed lazy chunk).
export default class ErrorBoundary extends Component {
  state = { hasFailed: false }

  static getDerivedStateFromError() {
    return { hasFailed: true }
  }

  render() {
    const { children } = this.props
    return this.state.hasFailed ? <ErrorFallback /> : children
  }
}
