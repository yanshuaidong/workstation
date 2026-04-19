function formatDate(date) {
  return date.toISOString().slice(0, 10)
}

export function getDefaultSignalDate(now = new Date()) {
  const targetDate = new Date(now)
  const weekday = targetDate.getDay()

  if (weekday === 6) {
    targetDate.setDate(targetDate.getDate() - 1)
  } else if (weekday === 0) {
    targetDate.setDate(targetDate.getDate() - 2)
  }

  return formatDate(targetDate)
}

export function getFirstIndicatorValue(options = []) {
  return options?.[0]?.value || ''
}
