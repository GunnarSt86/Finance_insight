import type { Language } from './i18n'

const DAYS_PER_YEAR = 365.2425

function locale(language: Language) {
  return language === 'is' ? 'is-IS' : 'en-US'
}

function integerFormatter(language: Language) {
  return new Intl.NumberFormat(locale(language), { maximumFractionDigits: 0 })
}

function oneDecimalFormatter(language: Language) {
  return new Intl.NumberFormat(locale(language), {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}

export function calculateDays(amountISK: number, annualISK: number) {
  return annualISK > 0 ? (amountISK / annualISK) * DAYS_PER_YEAR : 0
}

export function calculateMonths(amountISK: number, annualISK: number) {
  return annualISK > 0 ? (amountISK / annualISK) * 12 : 0
}

export function asISK(value: number, language: Language) {
  return integerFormatter(language).format(Math.round(value))
}

export function asCount(value: number, language: Language) {
  return integerFormatter(language).format(Math.round(value))
}

export function asCompactISK(value: number, language: Language) {
  const formatter = oneDecimalFormatter(language)
  const absolute = Math.abs(value)
  const unit = language === 'is' ? 'kr.' : 'ISK'
  if (absolute >= 1_000_000_000_000) {
    const label = language === 'is' ? 'billjónir' : 'trillion'
    return `${formatter.format(value / 1_000_000_000_000)} ${label} ${unit}`
  }
  if (absolute >= 1_000_000_000) {
    const label = language === 'is' ? 'milljarðar' : 'billion'
    return `${formatter.format(value / 1_000_000_000)} ${label} ${unit}`
  }
  if (absolute >= 1_000_000) {
    const label = language === 'is' ? 'milljónir' : 'million'
    return `${formatter.format(value / 1_000_000)} ${label} ${unit}`
  }
  return `${asISK(value, language)} ${unit}`
}

export function asDays(value: number, language: Language) {
  const formatter = oneDecimalFormatter(language)
  if (value < 1) {
    return language === 'is'
      ? `${formatter.format(value * 24)} klst.`
      : `${formatter.format(value * 24)} hours`
  }
  if (value < 2) {
    const wholeDays = Math.floor(value)
    const hours = Math.round((value - wholeDays) * 24)
    return language === 'is'
      ? `${wholeDays} dagur og ${hours} klst.`
      : `${wholeDays} day ${hours} hours`
  }
  return language === 'is'
    ? `${formatter.format(value)} dagar`
    : `${formatter.format(value)} days`
}

export function asMonths(value: number, language: Language) {
  const formatter = oneDecimalFormatter(language)
  const months = language === 'is' ? 'mánuðir' : 'months'
  if (value < 1) {
    return `${formatter.format(value)} ${months} · ${asDays((value / 12) * DAYS_PER_YEAR, language)}`
  }
  return `${formatter.format(value)} ${months}`
}
