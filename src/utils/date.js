const dayShort = ['ndz', 'pon', 'wt', 'śr', 'czw', 'pt', 'sob']

export function formatShortDate(date) {
  const day = dayShort[date.getDay()]
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = date.getFullYear()

  return `${day}, ${dd}.${mm}.${yyyy}`
}
