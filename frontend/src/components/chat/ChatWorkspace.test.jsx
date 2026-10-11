// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { suggestedQuestions } from '../../data/chat'
import { I18nProvider } from '../../i18n/I18nProvider'
import ChatWorkspace from './ChatWorkspace'

beforeAll(() => {
  // jsdom does not implement Element.prototype.scrollTo; the thread auto-scroll
  // effect calls it on every render.
  Element.prototype.scrollTo = () => {}
})

// Vitest runs without `globals`, so testing-library never registers its own
// afterEach and renders would otherwise pile up in the same document.
afterEach(cleanup)

function renderWorkspace(props) {
  return render(
    <I18nProvider>
      <ChatWorkspace
        messages={[]}
        onSend={() => {}}
        onStop={() => {}}
        isStreaming={false}
        isLoading={false}
        error=""
        onClearError={() => {}}
        {...props}
      />
    </I18nProvider>
  )
}

describe('ChatWorkspace tool tabs', () => {
  // "Tính thuế" and "Scan hợp đồng" have no backend endpoint, so they must be
  // visibly and actually inert rather than a mocked-up feature.
  it('renders the unbuilt tools as disabled and labelled "Sắp có"', () => {
    renderWorkspace()
    const tax = screen.getByRole('button', { name: /Tính thuế/ })
    const scan = screen.getByRole('button', { name: /Scan hợp đồng/ })

    expect(tax.disabled).toBe(true)
    expect(scan.disabled).toBe(true)
    expect(tax.getAttribute('aria-disabled')).toBe('true')
    expect(screen.getAllByText('Sắp có')).toHaveLength(2)
  })

  it('leaves the composer untouched when an unbuilt tool is clicked', () => {
    renderWorkspace()
    const textarea = screen.getByRole('textbox')
    fireEvent.click(screen.getByRole('button', { name: /Tính thuế/ }))
    expect(textarea.value).toBe('')
  })

  it('keeps the attach buttons disabled while no upload endpoint exists', () => {
    renderWorkspace()
    expect(screen.getByRole('button', { name: /Đính kèm tệp/ }).disabled).toBe(true)
    expect(screen.getByRole('button', { name: /Chọn văn bản tham chiếu/ }).disabled).toBe(true)
  })
})

describe('ChatWorkspace composer', () => {
  it('fills the composer from a suggestion card', () => {
    renderWorkspace()
    const [first] = suggestedQuestions
    fireEvent.click(screen.getByRole('button', { name: `Dùng câu hỏi gợi ý: ${first.text}` }))
    expect(screen.getByRole('textbox').value).toBe(first.text)
  })

  it('sends on Enter but not while an IME composition is being committed', () => {
    const onSend = vi.fn()
    renderWorkspace({ onSend })
    const textarea = screen.getByRole('textbox')

    fireEvent.change(textarea, { target: { value: 'Câu hỏi' } })
    // Telex/VNI commits a syllable with Enter — that keypress must not send.
    fireEvent.keyDown(textarea, { key: 'Enter', isComposing: true })
    expect(onSend).not.toHaveBeenCalled()

    fireEvent.keyDown(textarea, { key: 'Enter' })
    expect(onSend).toHaveBeenCalledWith('Câu hỏi')
  })

  it('does not send on Shift+Enter', () => {
    const onSend = vi.fn()
    renderWorkspace({ onSend })
    const textarea = screen.getByRole('textbox')

    fireEvent.change(textarea, { target: { value: 'Câu hỏi' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })
})
