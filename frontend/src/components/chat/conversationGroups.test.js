import { describe, expect, it } from 'vitest'
import { groupConversations } from './conversationGroups'

describe('groupConversations', () => {
  it('groups real history by its latest activity date', () => {
    const now = new Date(2026, 6, 15, 12)
    const groups = groupConversations(
      [
        { id: 'today', updatedAt: new Date(2026, 6, 15, 8).toISOString() },
        { id: 'yesterday', updatedAt: new Date(2026, 6, 14, 8).toISOString() },
        { id: 'week', updatedAt: new Date(2026, 6, 10, 8).toISOString() },
        { id: 'old', updatedAt: new Date(2026, 5, 20, 8).toISOString() },
      ],
      now
    )

    expect(groups.map((group) => [group.label, group.items.map((item) => item.id)])).toEqual([
      ['HÔM NAY', ['today']],
      ['HÔM QUA', ['yesterday']],
      ['7 NGÀY QUA', ['week']],
      ['CŨ HƠN', ['old']],
    ])
  })
})
