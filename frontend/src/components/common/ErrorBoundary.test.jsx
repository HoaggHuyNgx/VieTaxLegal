// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '../../i18n/I18nProvider'
import ErrorBoundary from './ErrorBoundary'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function Broken() {
  throw new Error('render failed')
}

const renderInside = (child) =>
  render(
    <I18nProvider>
      <ErrorBoundary>{child}</ErrorBoundary>
    </I18nProvider>
  )

describe('ErrorBoundary', () => {
  it('shows a message and a reload button instead of a blank page', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {}) // React logs the caught error

    renderInside(<Broken />)

    expect(screen.getByRole('alert').textContent).toContain('Trang gặp lỗi')
    expect(screen.getByRole('button', { name: 'Tải lại trang' })).toBeTruthy()
  })

  it('renders its children when nothing fails', () => {
    renderInside(<p>Nội dung</p>)

    expect(screen.getByText('Nội dung')).toBeTruthy()
  })
})
