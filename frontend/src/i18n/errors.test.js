import { describe, expect, it } from 'vitest'
import { ApiError } from '../services/api'
import { translateApiError } from './errors'
import { createTranslator } from './translator'

const localeCases = [
  {
    locale: 'vi',
    conversationNotFound: 'Không tìm thấy cuộc hội thoại.',
    deleteInProgress: 'Hãy dừng câu trả lời trước khi xóa cuộc hội thoại này.',
    generalInProgress: 'Cuộc hội thoại này đang có một câu trả lời được xử lý.',
    requestFailed: 'Không thể kết nối đến máy chủ. Vui lòng thử lại.',
    sendFailed: 'Không thể nhận câu trả lời. Vui lòng thử lại.',
  },
  {
    locale: 'en',
    conversationNotFound: 'Conversation not found.',
    deleteInProgress: 'Stop the current answer before deleting this conversation.',
    generalInProgress: 'This conversation already has an answer in progress.',
    requestFailed: 'Could not reach the server. Please try again.',
    sendFailed: 'Could not get an answer. Please try again.',
  },
]

describe.each(localeCases)('translateApiError in $locale', (copy) => {
  const { t } = createTranslator(copy.locale)

  it('resolves a plain error code without leaking its developer-facing message', () => {
    const error = new ApiError({ status: 404, code: 'CONVERSATION_NOT_FOUND' })

    expect(error.message).toBe('CONVERSATION_NOT_FOUND')
    expect(translateApiError(t, error)).toBe(copy.conversationNotFound)
  })

  it('resolves a call-site variant', () => {
    expect(translateApiError(t, { code: 'CHAT_IN_PROGRESS' }, { variant: 'delete' })).toBe(
      copy.deleteInProgress
    )
  })

  it('falls back from an unknown variant to the general wording', () => {
    expect(translateApiError(t, { code: 'CHAT_IN_PROGRESS' }, { variant: 'bogus' })).toBe(
      copy.generalInProgress
    )
  })

  it('turns a nested catalog entry into copy when no variant is supplied', () => {
    const result = translateApiError(t, { code: 'CHAT_IN_PROGRESS' })

    expect(result).toBe(copy.generalInProgress)
    expect(result).not.toBe('errors.byCode.CHAT_IN_PROGRESS')
    expect(typeof result).toBe('string')
  })

  it('uses the server message for an unknown code', () => {
    expect(
      translateApiError(t, {
        code: 'NEW_SERVER_CODE',
        message: 'Chi tiết lỗi từ máy chủ.',
      })
    ).toBe('Chi tiết lỗi từ máy chủ.')
  })

  it('uses the requested or default fallback when an unknown code has no server message', () => {
    const error = new ApiError({ status: 500, code: 'NEW_SERVER_CODE' })

    expect(translateApiError(t, error, { fallbackKey: 'chat.page.sendFailed' })).toBe(copy.sendFailed)
    expect(translateApiError(t, error)).toBe(copy.requestFailed)
  })

  it('uses the default fallback when the error has no code', () => {
    expect(translateApiError(t, new Error('Network failure'))).toBe(copy.requestFailed)
  })
})
