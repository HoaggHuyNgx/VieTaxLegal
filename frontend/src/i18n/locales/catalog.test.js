import { describe, expect, it } from 'vitest'
import { SUPPORTED_LOCALES, catalogFor } from '../catalogs'
import vi from './vi'

// Walks a catalog and yields every leaf as [dottedPath, value]. Arrays keep
// their index in the path so list content is compared element by element.
function walk(node, prefix = '') {
  if (typeof node === 'string') return [[prefix, node]]
  if (Array.isArray(node)) return node.flatMap((item, index) => walk(item, `${prefix}[${index}]`))
  if (node && typeof node === 'object') {
    return Object.entries(node).flatMap(([key, value]) => walk(value, prefix ? `${prefix}.${key}` : key))
  }
  return [[prefix, node]]
}

function placeholdersIn(value) {
  return [...value.matchAll(/\{\{(\w+)\}\}/g)].map((match) => match[1]).sort()
}

const referenceEntries = walk(vi)
const referenceKeys = referenceEntries.map(([key]) => key).sort()
const referenceIds = referenceEntries.filter(([key]) => key.split('.').at(-1) === 'id')

describe.each(SUPPORTED_LOCALES)('catalog "%s"', (locale) => {
  const entries = walk(catalogFor(locale))
  const byKey = new Map(entries)

  it('has exactly the same keys as the Vietnamese catalog', () => {
    // Compared both directions: a missing translation and a stale leftover key
    // are both build failures.
    expect(entries.map(([key]) => key).sort()).toEqual(referenceKeys)
  })

  it('has no empty or non-string values', () => {
    for (const [key, value] of entries) {
      expect(typeof value, `key "${key}"`).toBe('string')
      expect(value.trim(), `key "${key}"`).not.toBe('')
    }
  })

  it('uses the same placeholders as the Vietnamese catalog', () => {
    // A translator dropping {{title}} would silently break interpolation.
    for (const [key, reference] of referenceEntries) {
      const value = byKey.get(key)
      if (typeof value !== 'string') continue
      expect(placeholdersIn(value), `key "${key}"`).toEqual(placeholdersIn(reference))
    }
  })

  it('uses the Vietnamese reference values for data identifiers', () => {
    for (const [key, reference] of referenceIds) {
      expect(byKey.get(key), `key "${key}"`).toBe(reference)
    }
  })
})
