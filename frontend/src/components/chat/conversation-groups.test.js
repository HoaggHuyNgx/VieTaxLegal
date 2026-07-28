import { describe, expect, it } from 'vitest'
import { groupConversations } from './conversation-groups'

const now = new Date(2026, 6, 15, 12)

function idsByGroup(conversations) {
  return groupConversations(conversations, now).map((group) => [group.id, group.items.map((item) => item.id)])
}

describe('groupConversations', () => {
  // Asserting ids, not labels, keeps this test independent of the UI language.
  it('groups real history by its latest activity date', () => {
    expect(
      idsByGroup([
        { id: 'today', updatedAt: new Date(2026, 6, 15, 8).toISOString() },
        { id: 'yesterday', updatedAt: new Date(2026, 6, 14, 8).toISOString() },
        { id: 'week', updatedAt: new Date(2026, 6, 10, 8).toISOString() },
        { id: 'old', updatedAt: new Date(2026, 5, 20, 8).toISOString() },
      ])
    ).toEqual([
      ['today', ['today']],
      ['yesterday', ['yesterday']],
      ['last7Days', ['week']],
      ['older', ['old']],
    ])
  })

  it('puts day 7 in last7Days and day 8 in older', () => {
    expect(
      idsByGroup([
        { id: 'day7', updatedAt: new Date(2026, 6, 8, 8).toISOString() },
        { id: 'day8', updatedAt: new Date(2026, 6, 7, 8).toISOString() },
      ])
    ).toEqual([
      ['last7Days', ['day7']],
      ['older', ['day8']],
    ])
  })

  it('falls back to createdAt when updatedAt is absent', () => {
    expect(idsByGroup([{ id: 'only-created', createdAt: new Date(2026, 6, 15, 9).toISOString() }])).toEqual([
      ['today', ['only-created']],
    ])
  })

  it('drops empty groups and keeps input order within a group', () => {
    expect(
      idsByGroup([
        { id: 'first', updatedAt: new Date(2026, 6, 15, 7).toISOString() },
        { id: 'second', updatedAt: new Date(2026, 6, 15, 9).toISOString() },
      ])
    ).toEqual([['today', ['first', 'second']]])
  })

  it('returns nothing for an empty history', () => {
    expect(groupConversations([], now)).toEqual([])
  })
})
