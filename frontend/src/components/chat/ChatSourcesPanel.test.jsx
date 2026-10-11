// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { I18nProvider } from '../../i18n/I18nProvider'
import ChatSourcesPanel from './ChatSourcesPanel'

// Vitest runs without `globals`, so testing-library never registers its own
// afterEach and renders would otherwise pile up in the same document.
afterEach(cleanup)

function renderPanel(props) {
  return render(
    <I18nProvider>
      <ChatSourcesPanel citations={[]} isStreaming={false} isOpen onToggle={() => {}} {...props} />
    </I18nProvider>
  )
}

function citation(id, extra = {}) {
  return { id, title: `Nguồn ${id}`, ...extra }
}

describe('ChatSourcesPanel', () => {
  // NullRetriever means this is the state every real user sees today.
  it('shows the empty state and no links when there are no citations', () => {
    renderPanel()
    expect(screen.getByText('Chưa có nguồn tham khảo')).toBeTruthy()
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('waits instead of claiming there are no sources while streaming', () => {
    renderPanel({ isStreaming: true })
    expect(screen.queryByText('Chưa có nguồn tham khảo')).toBeNull()
    expect(screen.getByText('Đang chờ nguồn cho câu trả lời này…')).toBeTruthy()
  })

  it('links a citation only when its url is http(s)', () => {
    const { container } = renderPanel({
      citations: [
        citation('a', { url: 'https://vanban.chinhphu.vn/a' }),
        citation('b', { url: 'javascript:alert(1)' }),
        citation('c'),
      ],
    })
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(1)
    expect(links[0].getAttribute('href')).toBe('https://vanban.chinhphu.vn/a')
    // All three still render; the unsafe and the url-less one as plain text.
    expect(container.querySelectorAll('.source-card')).toHaveLength(3)
    expect([...container.querySelectorAll('.source-card-title')].map((node) => node.textContent)).toEqual([
      'Nguồn b',
      'Nguồn c',
    ])
  })

  it('renders an excerpt only when the backend sent one', () => {
    const { container } = renderPanel({
      citations: [citation('a', { excerpt: 'Trích dẫn' }), citation('b')],
    })
    const excerpts = container.querySelectorAll('.source-card-body p')
    expect(excerpts).toHaveLength(1)
    expect(excerpts[0].textContent).toBe('Trích dẫn')
    expect(screen.queryByText('undefined')).toBeNull()
  })

  it('collapses past three sources behind a real count', () => {
    const { container } = renderPanel({ citations: ['a', 'b', 'c', 'd'].map((id) => citation(id)) })
    expect(container.querySelectorAll('.source-card')).toHaveLength(3)
    expect(screen.getByRole('button', { name: 'Xem tất cả nguồn (4)' })).toBeTruthy()
  })

  it('does not offer a show-all button for three or fewer sources', () => {
    const { container } = renderPanel({ citations: ['a', 'b', 'c'].map((id) => citation(id)) })
    expect(container.querySelectorAll('.source-card')).toHaveLength(3)
    expect(screen.queryByRole('button', { name: /Xem tất cả nguồn/ })).toBeNull()
  })
})
