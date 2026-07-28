import { describe, expect, it } from 'vitest'
import { interpolate, readList, resolveKey, translate } from './translate'

const catalog = {
  common: { greeting: 'Xin chào', farewell: 'Tạm biệt {{name}}' },
  nested: { deep: { value: 'sâu' } },
  landing: { items: [{ id: 'a' }, { id: 'b' }] },
}

describe('resolveKey', () => {
  it('walks a dotted path', () => {
    expect(resolveKey(catalog, 'nested.deep.value')).toBe('sâu')
  })

  it('returns undefined instead of throwing on a broken path', () => {
    expect(resolveKey(catalog, 'nested.missing.value')).toBeUndefined()
  })
})

describe('translate', () => {
  it('resolves a dotted key', () => {
    expect(translate(catalog, 'common.greeting')).toBe('Xin chào')
  })

  it('returns undefined for a missing key so callers can fall back', () => {
    expect(translate(catalog, 'common.missing')).toBeUndefined()
    expect(translate(catalog, 'does.not.exist')).toBeUndefined()
  })

  it('returns undefined when the key resolves to a branch, not a string', () => {
    expect(translate(catalog, 'common')).toBeUndefined()
  })

  it('fills placeholders from params', () => {
    expect(translate(catalog, 'common.farewell', { name: 'An' })).toBe('Tạm biệt An')
  })

  it('leaves unknown placeholders untouched', () => {
    expect(translate(catalog, 'common.farewell', { other: 'An' })).toBe('Tạm biệt {{name}}')
  })

  it('returns the raw template when no params are given', () => {
    expect(translate(catalog, 'common.farewell')).toBe('Tạm biệt {{name}}')
  })
})

describe('interpolate', () => {
  // Conversation titles are user-supplied, so a value containing a replacement
  // pattern must be inserted literally rather than read as a capture reference.
  it('inserts values containing $& and $1 literally', () => {
    expect(interpolate('Xóa {{title}}', { title: '$& $1 $$' })).toBe('Xóa $& $1 $$')
  })

  it('coerces non-string values', () => {
    expect(interpolate('Có {{count}} mục', { count: 3 })).toBe('Có 3 mục')
  })
})

describe('readList', () => {
  it('returns array content', () => {
    expect(readList(catalog, 'landing.items')).toHaveLength(2)
  })

  it('returns undefined when the key is not an array', () => {
    expect(readList(catalog, 'common.greeting')).toBeUndefined()
    expect(readList(catalog, 'nope')).toBeUndefined()
  })
})
