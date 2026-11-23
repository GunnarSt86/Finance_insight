import { useEffect, useMemo, useState } from 'react'
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
import './App.css'

const DEFAULT_AMOUNT = 23_000_000_000
const PRESETS = [1_000_000_000, DEFAULT_AMOUNT, 100_000_000_000]

type Flow = {
  id: string
  label: string
  annualISK: number
  source: string
  table: string
  note: string
}

function initialAmount() {
  const fromUrl = Number(new URLSearchParams(window.location.search).get('amount'))
  return Number.isFinite(fromUrl) && fromUrl > 0 ? Math.round(fromUrl) : DEFAULT_AMOUNT
}

function parseISK(value: string) {
  const digits = value.replace(/[^0-9]/g, '')
  return digits ? Number(digits) : 0
}

function Badge({ kind }: { kind: 'official' | 'derived' | 'assumption' }) {
  return <span className={`badge badge--${kind}`}>{kind}</span>
}

function ComparisonBar({
  label,
  value,
  maximum,
  display,
  tone,
}: {
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
        <span>{label}</span>
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
  const [amount, setAmount] = useState(initialAmount)
  const [inputValue, setInputValue] = useState(() => asISK(initialAmount()))
  const [carPrice, setCarPrice] = useState(() => {
    const saved = Number(window.localStorage.getItem('isk-scale-car-price'))
    return Number.isFinite(saved) && saved > 0
      ? saved
      : referenceData.assumptions.carPriceISK
  })
  const [copyState, setCopyState] = useState('Copy link')

  useEffect(() => {
    const url = new URL(window.location.href)
    url.searchParams.set('amount', String(amount))
    window.history.replaceState({}, '', url)
  }, [amount])

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

  function setNewAmount(nextAmount: number) {
    const safeAmount = Math.max(0, Math.round(nextAmount))
    setAmount(safeAmount)
    setInputValue(asISK(safeAmount))
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopyState('Link copied')
      window.setTimeout(() => setCopyState('Copy link'), 1800)
    } catch {
      setCopyState('Copy failed')
    }
  }

  return (
    <div className="site-shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="Krónur in context, home">
          <span className="wordmark__mark">kr</span>
          <span>Krónur in context</span>
        </a>
        <button className="quiet-button" type="button" onClick={copyLink}>
          {copyState}
        </button>
      </header>

      <main id="top">
        <section className="hero-section" aria-labelledby="page-title">
          <div className="hero-copy">
            <p className="eyebrow">An Icelandic scale explorer</p>
            <h1 id="page-title">Make a large number feel human.</h1>
            <p className="hero-copy__intro">
              Enter an amount from the news and compare it with everyday life,
              public services and the Icelandic economy.
            </p>
          </div>

          <div className="amount-panel">
            <label htmlFor="amount">Amount in Icelandic krónur</label>
            <div className="amount-field">
              <span aria-hidden="true">kr</span>
              <input
                id="amount"
                inputMode="numeric"
                value={inputValue}
                onChange={(event) => {
                  setInputValue(event.target.value)
                  setAmount(parseISK(event.target.value))
                }}
                onBlur={() => setInputValue(asISK(amount))}
                aria-describedby="amount-help"
              />
            </div>
            <p id="amount-help">Spaces, commas and periods are all accepted.</p>
            <div className="preset-list" aria-label="Example amounts">
              {PRESETS.map((preset) => (
                <button
                  type="button"
                  key={preset}
                  className={amount === preset ? 'is-active' : ''}
                  onClick={() => setNewAmount(preset)}
                >
                  {asCompactISK(preset)}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="answer-section" aria-labelledby="answer-title">
          <div className="section-heading section-heading--light">
            <p className="eyebrow">First, three ways to see it</p>
            <h2 id="answer-title" aria-live="polite">{asCompactISK(amount)} is equivalent to…</h2>
          </div>
          <div className="answer-grid">
            <article className="answer-card answer-card--ice">
              <div className="answer-card__topline">
                <span>Shared across Iceland</span>
                <Badge kind="derived" />
              </div>
              <strong>{asISK(perResident)}</strong>
              <p>for every resident</p>
              <small>Using the {referenceData.population.year} population of {asCount(referenceData.population.value)}.</small>
            </article>
            <article className="answer-card answer-card--blue">
              <div className="answer-card__topline">
                <span>Public healthcare</span>
                <Badge kind="official" />
              </div>
              <strong>{asDays(healthDays)}</strong>
              <p>at the annual-average spending rate</p>
              <small>Equivalent scale, not a claim that services can literally be purchased by the day.</small>
            </article>
            <article className="answer-card answer-card--moss">
              <div className="answer-card__topline">
                <span>Full-time earnings</span>
                <Badge kind="official" />
              </div>
              <strong>{asCount(workerYears)}</strong>
              <p>worker-years of mean gross earnings</p>
              <small>Gross earnings are not the full cost of employing someone.</small>
            </article>
          </div>
        </section>

        <section className="content-section split-section" aria-labelledby="people-title">
          <div className="section-heading">
            <p className="eyebrow">Bring it closer</p>
            <h2 id="people-title">People and everyday scale</h2>
            <p>Concrete comparisons are memorable, but not all are equally official.</p>
          </div>
          <div className="fact-list">
            <article className="fact-row">
              <div>
                <Badge kind="official" />
                <h3>{asCount(studentYears)} student-years</h3>
                <p>Average primary-school operating cost per student in {referenceData.education.year}.</p>
              </div>
              <span className="fact-row__symbol" aria-hidden="true">01</span>
            </article>
            <article className="fact-row">
              <div>
                <Badge kind="assumption" />
                <h3>{asCount(cars)} cars</h3>
                <p>Based on the editable example price below—not an official vehicle-price statistic.</p>
                <label className="inline-input" htmlFor="car-price">
                  Assumed car price
                  <span>
                    <input
                      id="car-price"
                      type="number"
                      min="1"
                      step="100000"
                      value={carPrice}
                      onChange={(event) => setCarPrice(Math.max(1, Number(event.target.value)))}
                    />
                    kr
                  </span>
                </label>
              </div>
              <span className="fact-row__symbol" aria-hidden="true">02</span>
            </article>
            <article className="fact-row">
              <div>
                <Badge kind="derived" />
                <h3>{asDays(gdpDays)}</h3>
                <p>Equivalent to this much time in Iceland’s {referenceData.latestYear} GDP.</p>
              </div>
              <span className="fact-row__symbol" aria-hidden="true">03</span>
            </article>
          </div>
        </section>

        <section className="content-section chart-section" aria-labelledby="services-title">
          <div className="section-heading">
            <p className="eyebrow">Public services</p>
            <h2 id="services-title">How many months of annual spending?</h2>
            <p>
              Each bar compares the amount with one year of public expenditure at an
              annual-average rate. Longer bars represent more months.
            </p>
          </div>
          <div className="bar-card">
            {serviceResults.map((item) => (
              <ComparisonBar
                key={item.id}
                label={item.label}
                value={item.equivalent}
                maximum={maxService}
                display={asMonths(item.equivalent)}
                tone="blue"
              />
            ))}
          </div>
          <p className="chart-note">
            These comparisons express scale. Government programmes do not spend evenly
            through the year and cannot literally be switched on for a fraction of a month.
          </p>
        </section>

        <section className="content-section chart-section chart-section--cool" aria-labelledby="economy-title">
          <div className="section-heading">
            <p className="eyebrow">The national clock</p>
            <h2 id="economy-title">How many days of economic activity?</h2>
            <p>Annual flows translated into time make very different scales easier to compare.</p>
          </div>
          <div className="bar-card bar-card--dark">
            {economyResults.map((item) => (
              <ComparisonBar
                key={item.id}
                label={item.label}
                value={item.equivalent}
                maximum={maxEconomy}
                display={asDays(item.equivalent)}
                tone="rust"
              />
            ))}
          </div>
          <p className="chart-note chart-note--dark">
            GDP and consumption are measures of activity, not pools of money available to spend.
          </p>
        </section>

        <section className="method-section" aria-labelledby="method-title">
          <div className="section-heading">
            <p className="eyebrow">Trust the comparison</p>
            <h2 id="method-title">Sources, method and limits</h2>
            <p>
              The website calculates comparisons in your browser from a small snapshot of
              official {referenceData.provider} data.
            </p>
          </div>
          <div className="method-grid">
            <div className="method-legend">
              <p><Badge kind="official" /> Input taken from an official statistical table.</p>
              <p><Badge kind="derived" /> Result calculated from official inputs.</p>
              <p><Badge kind="assumption" /> A transparent, editable example value.</p>
            </div>
            <div className="source-list">
              <details>
                <summary>Public-service tables</summary>
                <ul>
                  {referenceData.publicServices.map((item) => (
                    <li key={item.id}>
                      <a href={item.source} target="_blank" rel="noreferrer">{item.label}</a>
                      <span>{item.table} · {item.year}</span>
                    </li>
                  ))}
                </ul>
              </details>
              <details>
                <summary>People and earnings tables</summary>
                <ul>
                  <li>
                    <a href={referenceData.population.source} target="_blank" rel="noreferrer">Population of Iceland</a>
                    <span>{referenceData.population.table} · {referenceData.population.year}</span>
                  </li>
                  <li>
                    <a href={referenceData.earnings.source} target="_blank" rel="noreferrer">Mean full-time earnings</a>
                    <span>{referenceData.earnings.table} · {referenceData.earnings.year}</span>
                  </li>
                  <li>
                    <a href={referenceData.education.source} target="_blank" rel="noreferrer">Primary student operating cost</a>
                    <span>{referenceData.education.table} · {referenceData.education.year}</span>
                  </li>
                </ul>
              </details>
              <details>
                <summary>Economy and household tables</summary>
                <ul>
                  {referenceData.economicFlows.map((item) => (
                    <li key={item.id}>
                      <a href={item.source} target="_blank" rel="noreferrer">{item.label}</a>
                      <span>{item.table} · {item.year}</span>
                    </li>
                  ))}
                </ul>
              </details>
              <details>
                <summary>Calculation method</summary>
                <p>
                  Days = entered amount ÷ annual value × 365.2425. Months = entered amount
                  ÷ annual value × 12. Results are rounded for readability while calculations
                  use the unrounded values.
                </p>
              </details>
            </div>
          </div>
          <p className="data-date">Reference data snapshot: {referenceData.snapshotDate}. Values for {referenceData.latestYear} may be preliminary or revised.</p>
        </section>
      </main>

      <footer>
        <p>A local prototype for understanding large Icelandic króna amounts.</p>
        <a href="#top">Back to the amount</a>
      </footer>
    </div>
  )
}

export default App
