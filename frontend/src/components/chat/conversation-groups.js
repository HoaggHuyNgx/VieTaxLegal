const dayInMilliseconds = 24 * 60 * 60 * 1000

function startOfDay(value) {
  const date = new Date(value)
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

// Returns stable ids, not labels: bucketing is language-independent and the
// caller translates via chat.groups.<id>.
export function groupConversations(conversations, now = new Date()) {
  const today = startOfDay(now)
  const groups = [
    { id: 'today', items: [] },
    { id: 'yesterday', items: [] },
    { id: 'last7Days', items: [] },
    { id: 'older', items: [] },
  ]

  for (const conversation of conversations) {
    const updatedAt = new Date(conversation.updatedAt || conversation.createdAt)
    const ageInDays = Math.floor((today - startOfDay(updatedAt)) / dayInMilliseconds)
    const groupIndex = ageInDays <= 0 ? 0 : ageInDays === 1 ? 1 : ageInDays <= 7 ? 2 : 3
    groups[groupIndex].items.push(conversation)
  }

  return groups.filter((group) => group.items.length > 0)
}
