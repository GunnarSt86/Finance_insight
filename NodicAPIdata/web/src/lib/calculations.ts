const DAYS_PER_YEAR = 365.2425

const integerFormatter = new Intl.NumberFormat('is-IS', {
  maximumFractionDigits: 0,
})

const oneDecimalFormatter = new Intl.NumberFormat('is-IS', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

export function calculateDays(amountISK: number, annualISK: number) {
  return annualISK > 0 ? (amountISK / annualISK) * DAYS_PER_YEAR : 0
}

export function calculateMonths(amountISK: number, annualISK: number) {
  return annualISK > 0 ? (amountISK / annualISK) * 12 : 0
}

export function asISK(value: number) {
  return integerFormatter.format(Math.round(value))
}

export function asCount(value: number) {
  return integerFormatter.format(Math.round(value))
}

export function asCompactISK(value: number) {
  const absolute = Math.abs(value)
  if (absolute >= 1_000_000_000_000) return `${oneDecimalFormatter.format(value / 1_000_000_000_000)} trillion kr`
  if (absolute >= 1_000_000_000) return `${oneDecimalFormatter.format(value / 1_000_000_000)} billion kr`
  if (absolute >= 1_000_000) return `${oneDecimalFormatter.format(value / 1_000_000)} million kr`
  return `${asISK(value)} kr`
}

export function asDays(value: number) {
  if (value < 1) return `${oneDecimalFormatter.format(value * 24)} hours`
  if (value < 2) {
    const wholeDays = Math.floor(value)
    const hours = Math.round((value - wholeDays) * 24)
    return `${wholeDays} day ${hours} hours`
  }
  return `${oneDecimalFormatter.format(value)} days`
}

export function asMonths(value: number) {
  if (value < 1) return `${oneDecimalFormatter.format(value)} months · ${asDays((value / 12) * DAYS_PER_YEAR)}`
  return `${oneDecimalFormatter.format(value)} months`
}
