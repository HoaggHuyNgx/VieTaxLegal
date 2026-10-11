import { describe, expect, it } from 'vitest'
import { latestCitations, safeExternalUrl } from './chat-sources'

describe('safeExternalUrl', () => {
  it('keeps http and https urls', () => {
    expect(safeExternalUrl('https://vanban.chinhphu.vn/abc')).toBe('https://vanban.chinhphu.vn/abc')
    expect(safeExternalUrl('http://example.test')).toBe('http://example.test')
    expect(safeExternalUrl('HTTPS://EXAMPLE.TEST')).toBe('HTTPS://EXAMPLE.TEST')
  })

  // Citation text comes from the model, so anything that is not plainly http(s)
  // must never become a live link.
  it('drops every other scheme', () => {
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
    expect(safeExternalUrl('data:text/html,<script>')).toBeNull()
    expect(safeExternalUrl('//evil.test')).toBeNull()
    expect(safeExternalUrl('vanban.chinhphu.vn')).toBeNull()
  })

  it('tolerates a missing url', () => {
    expect(safeExternalUrl('')).toBeNull()
    expect(safeExternalUrl(undefined)).toBeNull()
    expect(safeExternalUrl(null)).toBeNull()
  })
})

describe('latestCitations', () => {
  const withCitations = {
    role: 'assistant',
    citations: [{ id: 'c1', title: 'Luật Doanh nghiệp' }],
  }

  it('returns nothing when there is no assistant turn', () => {
    expect(latestCitations([])).toEqual([])
    expect(latestCitations([{ role: 'user', content: 'Câu hỏi' }])).toEqual([])
  })

  it('reads the citations of the newest assistant turn', () => {
    expect(latestCitations([{ role: 'user' }, withCitations])).toEqual(withCitations.citations)
  })

  // Provenance regression guard: carrying an older turn's citations forward would
  // attach real legal documents to an answer that never cited them.
  it('empties when the newest assistant turn has no citations', () => {
    expect(latestCitations([withCitations, { role: 'user' }, { role: 'assistant', citations: [] }])).toEqual(
      []
    )
  })

  it('tolerates an assistant turn with no citations key', () => {
    expect(latestCitations([withCitations, { role: 'assistant', content: 'Đang trả lời' }])).toEqual([])
  })
})
