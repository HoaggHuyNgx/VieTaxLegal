// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { I18nProvider } from '../../i18n/I18nProvider'
import AssistantMessage from './AssistantMessage'

afterEach(cleanup)

function renderAnswer(citation) {
  const message = { id: 'a', role: 'assistant', status: 'completed', content: 'Theo [1].' }
  return render(
    <I18nProvider>
      <AssistantMessage message={{ ...message, citations: [{ id: '1', title: 'Luật A', ...citation }] }} />
    </I18nProvider>
  )
}

// The side panel is hidden below 1100px, so the inline list is then the only place that can
// say which article an answer relied on.
describe('AssistantMessage sources', () => {
  it('names the article, document number and issue date of each source', () => {
    renderAnswer({ locator: 'Điều 5 khoản 2', documentNumber: '45/2019/QH14', issuedOn: '2019-11-20' })

    expect(screen.getByText('Điều 5 khoản 2 · 45/2019/QH14 · Ban hành 2019-11-20')).toBeTruthy()
  })

  it('adds no detail line, and invents nothing, when the source has none', () => {
    const { container } = renderAnswer({})

    expect(container.querySelector('.source-meta')).toBeNull()
  })
})

describe('AssistantMessage markdown', () => {
  const renderContent = (content) =>
    render(
      <I18nProvider>
        <AssistantMessage message={{ id: 'a', role: 'assistant', status: 'completed', content }} />
      </I18nProvider>
    )

  it('renders a table instead of showing its pipes', () => {
    const { container } = renderContent('| Mức | Thuế suất |\n|---|---|\n| A | B |')

    expect(container.querySelectorAll('table td')).toHaveLength(2)
  })

  // Vietnamese answers use "~" for "about": two of them must not strike out the text between.
  it('does not read single tildes as strikethrough', () => {
    const { container } = renderContent('Khoảng ~5 đến ~10 ngày.')

    expect(container.querySelector('del')).toBeNull()
    expect(container.textContent).toContain('~5 đến ~10')
  })
})
