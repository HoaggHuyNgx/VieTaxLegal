// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
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
afterEach(() => {
  cleanup()
  sessionStorage.clear() // the composer restores a draft, which would leak between tests
})

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

describe('ChatWorkspace composer tools', () => {
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
    expect(onSend).toHaveBeenCalledWith('Câu hỏi', expect.any(Object))
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

describe('ChatWorkspace daily quota', () => {
  it('shows the remaining daily messages and flags when none are left', () => {
    renderWorkspace({ usage: { dailyLimit: 100, dailyUsed: 7, dailyRemaining: 93 } })
    expect(screen.getByText('Còn 93/100 lượt hôm nay').className).toContain('text-chat-limit')
    cleanup()

    renderWorkspace({ usage: { dailyLimit: 100, dailyUsed: 100, dailyRemaining: 0 } })
    expect(screen.getByText('Còn 0/100 lượt hôm nay').className).toContain('text-chat-error-text')
  })

  it('shows nothing until the usage has loaded', () => {
    renderWorkspace()
    expect(screen.queryByText(/lượt hôm nay/)).toBeNull()
  })
})

describe('ChatWorkspace draft', () => {
  const typeAndSend = async (text) => {
    fireEvent.change(screen.getByRole('textbox'), { target: { value: text } })
    await act(async () => {
      fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' })
    })
  }

  it('gives the question back when the server did not take it', async () => {
    renderWorkspace({ onSend: vi.fn().mockResolvedValue(false), draftOwner: 'u1' })

    await typeAndSend('Câu hỏi dài')

    expect(screen.getByRole('textbox').value).toBe('Câu hỏi dài')
  })

  it('keeps an unaccepted question across a reload, for the same account only', async () => {
    renderWorkspace({ onSend: () => new Promise(() => {}), draftOwner: 'u1' })
    await typeAndSend('Câu hỏi đang gửi')
    cleanup()

    renderWorkspace({ draftOwner: 'u2' })
    expect(screen.getByRole('textbox').value).toBe('')
    cleanup()
    renderWorkspace({ draftOwner: 'u1' })
    expect(screen.getByRole('textbox').value).toBe('Câu hỏi đang gửi')
  })

  it('forgets the draft once the server accepted it', async () => {
    const onSend = vi.fn(async (_text, { onAccepted }) => {
      onAccepted()
      return true
    })
    renderWorkspace({ onSend, draftOwner: 'u1' })
    await typeAndSend('Đã gửi')
    cleanup()

    renderWorkspace({ draftOwner: 'u1' })

    expect(screen.getByRole('textbox').value).toBe('')
  })
})

describe('ChatWorkspace scrolling', () => {
  const messages = (count) =>
    Array.from({ length: count }, (_, i) => ({ id: `m${i}`, role: 'user', content: `Tin ${i}` }))
  const workspace = (items) => (
    <I18nProvider>
      <ChatWorkspace
        messages={items}
        onSend={() => {}}
        onStop={() => {}}
        onClearError={() => {}}
        isStreaming
      />
    </I18nProvider>
  )
  // A 300px window on 1000px of thread: the bottom is at scrollTop 700.
  const move = (element, top, height = 1000) => {
    Object.defineProperty(element, 'scrollHeight', { configurable: true, value: height })
    Object.defineProperty(element, 'clientHeight', { configurable: true, value: 300 })
    element.scrollTop = top
  }
  const scrollTo = (element, top, height) => {
    move(element, top, height)
    fireEvent.scroll(element)
  }
  const openAtBottom = () => {
    const follow = vi.fn()
    Element.prototype.scrollTo = follow
    const { container, rerender } = render(workspace(messages(1)))
    const thread = container.querySelector('.thread-scroll')
    scrollTo(thread, 700)
    follow.mockClear()
    return { follow, thread, update: (count) => rerender(workspace(messages(count))) }
  }

  it('follows new text only while the reader is at the bottom', () => {
    const { follow, thread, update } = openAtBottom()

    scrollTo(thread, 100) // reading further up
    update(2)
    expect(follow).not.toHaveBeenCalled()

    scrollTo(thread, 680) // back within reach of the bottom
    update(3)
    expect(follow).toHaveBeenCalledTimes(1)
  })

  // Text arrives faster than the browser fires scroll events.
  it('does not pull the reader back when their scroll has not been reported yet', () => {
    const { follow, thread, update } = openAtBottom()

    move(thread, 100)
    update(2)

    expect(follow).not.toHaveBeenCalled()
  })

  it('keeps following when a long chunk, not the reader, opened the gap', () => {
    const { follow, thread, update } = openAtBottom()

    scrollTo(thread, 700, 1600) // our own scroll reported after much more text had landed
    update(2)

    expect(follow).toHaveBeenCalledTimes(1)
  })
})
