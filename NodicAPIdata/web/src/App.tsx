import { useEffect, useMemo, useState } from 'react'
import { MetricIcon } from './components/MetricIcon'
import referenceData from './data/iceland-reference.json'
import {
  asCompactISK,
  asCount,
  asDays,
  asISK,
  asMonths,
  calculateDays,
  calculateMonths,
} from './lib/calculations'
import { copy, interpolate } from './lib/i18n'
import type { Language } from './lib/i18n'
import './App.css'

const DEFAULT_AMOUNT = 23_000_000_000
const PRESETS = [1_000_000_000, DEFAULT_AMOUNT, 100_000_000_000]

type Flow = {
  id: string
  annualISK: number
  source: string
  table: string
  year?: number
}

type BadgeKind = 'official' | 'derived' | 'assumption'

function initialAmount() {
  const fromUrl = Number(new URLSearchParams(window.location.search).get('amount'))
  return Number.isFinite(fromUrl) && fromUrl > 0 ? Math.round(fromUrl) : DEFAULT_AMOUNT
}

function initialLanguage(): Language {
  const fromUrl = new URLSearchParams(window.location.search).get('lang')
  if (fromUrl === 'en' || fromUrl === 'is') return fromUrl
  const saved = window.localStorage.getItem('isk-scale-language')
  if (saved === 'en' || saved === 'is') return saved
  return navigator.language.toLowerCase().startsWith('is') ? 'is' : 'en'
}

function parseISK(value: string) {
  const digits = value.replace(/[^0-9]/g, '')
  return digits ? Number(digits) : 0
}

function Badge({ kind, language }: { kind: BadgeKind; language: Language }) {
  return <span className={`badge badge--${kind}`}>{copy[language].badges[kind]}</span>
}

function ComparisonBar({
  id,
  label,
  value,
  maximum,
  display,
  tone,
}: {
  id: string
  label: string
  value: number
  maximum: number
  display: string
  tone: 'blue' | 'rust'
}) {
  const width = maximum > 0 ? Math.max(2, (value / maximum) * 100) : 0

  return (
    <div className="comparison-row">
      <div className="comparison-row__label">
        <span className="comparison-row__name">
          <MetricIcon name={id} className="comparison-row__icon" />
          {label}
        </span>
        <strong>{display}</strong>
      </div>
      <div className="comparison-row__track" aria-hidden="true">
        <span
          className={`comparison-row__fill comparison-row__fill--${tone}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

function App() {
  const [language, setLanguage] = useState<Language>(initialLanguage)
  const [amount, setAmount] = useState(initialAmount)
  const [inputValue, setInputValue] = useState(() => asISK(initialAmount(), initialLanguage()))
  const [carPrice, setCarPrice] = useState(() => {
    const saved = Number(window.localStorage.getItem('isk-scale-car-price'))
    return Number.isFinite(saved) && saved > 0 ? saved : referenceData.assumptions.carPriceISK
  })
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')
  const t = copy[language]

  useEffect(() => {
    const url = new URL(window.location.href)
    url.searchParams.set('amount', String(amount))
    url.searchParams.set('lang', language)
    window.history.replaceState({}, '', url)
    window.localStorage.setItem('isk-scale-language', language)
    document.documentElement.lang = language
    document.title = t.pageTitle
  }, [amount, language, t.pageTitle])

  useEffect(() => {
    window.localStorage.setItem('isk-scale-car-price', String(carPrice))
  }, [carPrice])

  const serviceResults = useMemo(
    () =>
      (referenceData.publicServices as Flow[])
        .map((item) => ({ ...item, equivalent: calculateMonths(amount, item.annualISK) }))
        .sort((a, b) => b.equivalent - a.equivalent),
    [amount],
  )

  const economyResults = useMemo(
    () =>
      (referenceData.economicFlows as Flow[])
        .map((item) => ({ ...item, equivalent: calculateDays(amount, item.annualISK) }))
        .sort((a, b) => b.equivalent - a.equivalent),
    [amount],
  )

  const maxService = Math.max(...serviceResults.map((item) => item.equivalent))
  const maxEconomy = Math.max(...economyResults.map((item) => item.equivalent))
  const perResident = amount / referenceData.population.value
  const healthAnnualISK = referenceData.publicServices.find((item) => item.id === 'healthcare')?.annualISK ?? 0
  const gdpAnnualISK = referenceData.economicFlows.find((item) => item.id === 'gdp')?.annualISK ?? 0
  const healthDays = calculateDays(amount, healthAnnualISK)
  const workerYears = amount / (referenceData.earnings.meanMonthlyISK * 12)
  const studentYears = amount / referenceData.education.primaryStudentAnnualCostISK
  const cars = amount / carPrice
  const gdpDays = calculateDays(amount, gdpAnnualISK)
  const digitCount = inputValue.replace(/[^0-9]/g, '').length
  const amountClass = digitCount > 15 ? 'amount-field--very-long' : digitCount > 11 ? 'amount-field--long' : ''
  const metricLabel = (id: string) => (t.metrics as Record<string, string>)[id] ?? id
  const dateLocale = language === 'is' ? 'is-IS' : 'en-GB'
  const snapshotDate = new Intl.DateTimeFormat(dateLocale, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date(`${referenceData.snapshotDate}T12:00:00Z`))

  function setNewAmount(nextAmount: number) {
    const safeAmount = Math.max(0, Math.round(nextAmount))
    setAmount(safeAmount)
    setInputValue(asISK(safeAmount, language))
  }

  function changeLanguage(nextLanguage: Language) {
    setLanguage(nextLanguage)
    setInputValue(asISK(amount, nextLanguage))
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopyState('copied')
      window.setTimeout(() => setCopyState('idle'), 1800)
    } catch {
      setCopyState('failed')
    }
  }

  const copyButton = copyState === 'copied' ? t.linkCopied : copyState === 'failed' ? t.copyFailed : t.copyLink

  return (
    <div className="site-shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label={t.homeLabel}>
          <span className="wordmark__mark">kr</span>
          <span>{t.wordmark}</span>
        </a>
        <div className="topbar__actions">
          <div className="language-toggle" role="group" aria-label={t.languageLabel}>
            <button type="button" aria-pressed={language === 'is'} onClick={() => changeLanguage('is')}>IS</button>
            <button type="button" aria-pressed={language === 'en'} onClick={() => changeLanguage('en')}>EN</button>
          </div>
          <button className="quiet-button" type="button" onClick={copyLink}>{copyButton}</button>
        </div>
      </header>

      <main id="top">
        <section className="hero-section" aria-labelledby="page-title">
          <div className="hero-copy">
            <p className="eyebrow">{t.heroEyebrow}</p>
            <h1 id="page-title">{t.heroTitle}</h1>
            <p className="hero-copy__intro">{t.heroIntro}</p>
          </div>

          <div className="amount-panel">
            <label htmlFor="amount">{t.amountLabel}</label>
            <div className={`amount-field ${amountClass}`}>
              <MetricIcon name="edit" className="amount-field__edit" />
              <input
                id="amount"
                inputMode="numeric"
                value={inputValue}
                placeholder={t.amountPlaceholder}
                onChange={(event) => {
                  setInputValue(event.target.value)
                  setAmount(parseISK(event.target.value))
                }}
                onBlur={() => setInputValue(asISK(amount, language))}
                aria-describedby="amount-callout amount-help"
              />
              <span className="amount-field__unit" aria-hidden="true">{language === 'is' ? 'kr.' : 'ISK'}</span>
            </div>
            <p id="amount-callout" className="amount-callout">
              <MetricIcon name="edit" className="amount-callout__icon" />
              {t.amountCallout}
            </p>
            <p id="amount-help">{t.amountHelp}</p>
            <div className="preset-list" aria-label={t.presetsLabel}>
              {PRESETS.map((preset) => (
                <button
                  type="button"
                  key={preset}
                  className={amount === preset ? 'is-active' : ''}
                  onClick={() => setNewAmount(preset)}
                >
                  {asCompactISK(preset, language)}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="answer-section" aria-labelledby="answer-title">
          <div className="section-heading section-heading--light">
            <p className="eyebrow">{t.firstEyebrow}</p>
            <h2 id="answer-title" aria-live="polite">{asCompactISK(amount, language)} {t.equivalentTo}</h2>
          </div>
          <div className="answer-grid">
            <article className="answer-card answer-card--ice">
              <div className="answer-card__topline"><span>{t.sharedIceland}</span><Badge kind="derived" language={language} /></div>
              <MetricIcon name="people" className="answer-card__icon" />
              <strong>{asISK(perResident, language)}</strong>
              <p>{t.everyResident}</p>
              <small>{interpolate(t.populationBasis, { year: referenceData.population.year, value: asCount(referenceData.population.value, language) })}</small>
            </article>
            <article className="answer-card answer-card--blue">
              <div className="answer-card__topline"><span>{t.publicHealthcare}</span><Badge kind="official" language={language} /></div>
              <MetricIcon name="healthcare" className="answer-card__icon" />
              <strong>{asDays(healthDays, language)}</strong>
              <p>{t.annualRate}</p>
              <small>{t.healthcareCaveat}</small>
            </article>
            <article className="answer-card answer-card--moss">
              <div className="answer-card__topline"><span>{t.fullTimeEarnings}</span><Badge kind="official" language={language} /></div>
              <MetricIcon name="earnings" className="answer-card__icon" />
              <strong>{asCount(workerYears, language)}</strong>
              <p>{t.workerYears}</p>
              <small>{t.earningsCaveat}</small>
            </article>
          </div>
        </section>

        <section className="content-section split-section" aria-labelledby="people-title">
          <div className="section-heading">
            <p className="eyebrow">{t.peopleEyebrow}</p>
            <h2 id="people-title">{t.peopleTitle}</h2>
            <p>{t.peopleIntro}</p>
          </div>
          <div className="fact-list">
            <article className="fact-row">
              <div>
                <Badge kind="official" language={language} />
                <h3>{asCount(studentYears, language)} {t.studentYears}</h3>
                <p>{interpolate(t.studentNote, { year: referenceData.education.year })}</p>
              </div>
              <MetricIcon name="student" className="fact-row__icon" />
            </article>
            <article className="fact-row">
              <div>
                <Badge kind="assumption" language={language} />
                <h3>{asCount(cars, language)} {t.cars}</h3>
                <p>{t.carsNote}</p>
                <label className="inline-input" htmlFor="car-price">
                  {t.carPrice}
                  <span>
                    <input id="car-price" type="number" min="1" step="100000" value={carPrice} onChange={(event) => setCarPrice(Math.max(1, Number(event.target.value)))} />
                    {language === 'is' ? 'kr.' : 'ISK'}
                  </span>
                </label>
              </div>
              <MetricIcon name="car" className="fact-row__icon" />
            </article>
            <article className="fact-row">
              <div>
                <Badge kind="derived" language={language} />
                <h3>{asDays(gdpDays, language)}</h3>
                <p>{interpolate(t.gdpNote, { year: referenceData.latestYear })}</p>
              </div>
              <MetricIcon name="gdp" className="fact-row__icon" />
            </article>
          </div>
        </section>

        <section className="content-section chart-section" aria-labelledby="services-title">
          <div className="section-heading">
            <p className="eyebrow">{t.servicesEyebrow}</p>
            <h2 id="services-title">{t.servicesTitle}</h2>
            <p>{t.servicesIntro}</p>
          </div>
          <div className="bar-card">
            {serviceResults.map((item) => (
              <ComparisonBar key={item.id} id={item.id} label={metricLabel(item.id)} value={item.equivalent} maximum={maxService} display={asMonths(item.equivalent, language)} tone="blue" />
            ))}
          </div>
          <p className="chart-note">{t.servicesCaveat}</p>
        </section>

        <section className="content-section chart-section chart-section--cool" aria-labelledby="economy-title">
          <div className="section-heading">
            <p className="eyebrow">{t.economyEyebrow}</p>
            <h2 id="economy-title">{t.economyTitle}</h2>
            <p>{t.economyIntro}</p>
          </div>
          <div className="bar-card bar-card--dark">
            {economyResults.map((item) => (
              <ComparisonBar key={item.id} id={item.id} label={metricLabel(item.id)} value={item.equivalent} maximum={maxEconomy} display={asDays(item.equivalent, language)} tone="rust" />
            ))}
          </div>
          <p className="chart-note chart-note--dark">{t.economyCaveat}</p>
        </section>

        <section className="method-section" aria-labelledby="method-title">
          <div className="section-heading">
            <p className="eyebrow">{t.methodEyebrow}</p>
            <h2 id="method-title">{t.methodTitle}</h2>
            <p>{t.methodIntro}</p>
          </div>
          <div className="method-grid">
            <div className="method-legend">
              <p><Badge kind="official" language={language} /> {t.officialMeaning}</p>
              <p><Badge kind="derived" language={language} /> {t.derivedMeaning}</p>
              <p><Badge kind="assumption" language={language} /> {t.assumptionMeaning}</p>
            </div>
            <div className="source-list">
              <details>
                <summary>{t.serviceTables}</summary>
                <ul>{referenceData.publicServices.map((item) => <li key={item.id}><a href={item.source} target="_blank" rel="noreferrer">{metricLabel(item.id)}</a><span>{item.table} · {item.year}</span></li>)}</ul>
              </details>
              <details>
                <summary>{t.peopleTables}</summary>
                <ul>
                  <li><a href={referenceData.population.source} target="_blank" rel="noreferrer">{t.populationLink}</a><span>{referenceData.population.table} · {referenceData.population.year}</span></li>
                  <li><a href={referenceData.earnings.source} target="_blank" rel="noreferrer">{t.earningsLink}</a><span>{referenceData.earnings.table} · {referenceData.earnings.year}</span></li>
                  <li><a href={referenceData.education.source} target="_blank" rel="noreferrer">{t.studentLink}</a><span>{referenceData.education.table} · {referenceData.education.year}</span></li>
                </ul>
              </details>
              <details>
                <summary>{t.economyTables}</summary>
                <ul>{referenceData.economicFlows.map((item) => <li key={item.id}><a href={item.source} target="_blank" rel="noreferrer">{metricLabel(item.id)}</a><span>{item.table} · {item.year}</span></li>)}</ul>
              </details>
              <details>
                <summary>{t.calculationMethod}</summary>
                <p>{t.calculationText}</p>
              </details>
            </div>
          </div>
          <p className="data-date">{interpolate(t.dataDate, { date: snapshotDate, year: referenceData.latestYear })}</p>
        </section>
      </main>

      <footer><p>{t.footer}</p><a href="#top">{t.back}</a></footer>
    </div>
  )
}

export default App
