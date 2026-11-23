export type IconName =
  | 'people' | 'healthcare' | 'earnings' | 'student' | 'car' | 'gdp'
  | 'social-protection' | 'education' | 'culture' | 'public-order'
  | 'housing-community' | 'fish-catch' | 'household-food' | 'tourism'
  | 'housing-utilities' | 'household-total' | 'edit'

export function MetricIcon({ name, className = '' }: { name: IconName | string; className?: string }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  let content

  switch (name) {
    case 'people':
      content = <><circle cx="12" cy="8" r="3" {...common}/><path d="M5.5 20c.7-4 2.8-6 6.5-6s5.8 2 6.5 6" {...common}/><circle cx="4.5" cy="10" r="2" {...common}/><circle cx="19.5" cy="10" r="2" {...common}/></>
      break
    case 'healthcare':
      content = <><path d="M12 21s-8-4.7-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6.3-8 11-8 11Z" {...common}/><path d="M12 7.5v7M8.5 11h7" {...common}/></>
      break
    case 'earnings':
      content = <><ellipse cx="9" cy="7" rx="5" ry="2.5" {...common}/><path d="M4 7v4c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5V7M4 11v4c0 1.4 2.2 2.5 5 2.5 1.2 0 2.3-.2 3.2-.6" {...common}/><circle cx="17" cy="16" r="4" {...common}/><path d="M17 14v4M15.7 15h2" {...common}/></>
      break
    case 'student':
    case 'education':
      content = <><path d="M3.5 5.5c3.2-.7 6 .1 8.5 2.2v11c-2.5-2-5.3-2.8-8.5-2.1V5.5ZM20.5 5.5c-3.2-.7-6 .1-8.5 2.2v11c2.5-2 5.3-2.8 8.5-2.1V5.5Z" {...common}/></>
      break
    case 'car':
      content = <><path d="m4 15 1.8-5.5A2.2 2.2 0 0 1 8 8h8a2.2 2.2 0 0 1 2.2 1.5L20 15v3H4v-3Z" {...common}/><path d="M6 15h12M7 18v2M17 18v2" {...common}/><circle cx="7.5" cy="14.5" r="1" fill="currentColor"/><circle cx="16.5" cy="14.5" r="1" fill="currentColor"/></>
      break
    case 'gdp':
      content = <><circle cx="12" cy="12" r="9" {...common}/><path d="M12 7v5l3.5 2M8 4.2l1 2M16 4.2l-1 2" {...common}/></>
      break
    case 'social-protection':
      content = <><path d="M3 12a9 9 0 0 1 18 0H3ZM12 12v6a2 2 0 0 0 4 0" {...common}/><path d="M6 12c0-1.2 1-2 2-2s2 .8 2 2M14 12c0-1.2 1-2 2-2s2 .8 2 2" {...common}/></>
      break
    case 'culture':
      content = <><path d="M9 18V6l10-2v12" {...common}/><circle cx="6.5" cy="18" r="2.5" {...common}/><circle cx="16.5" cy="16" r="2.5" {...common}/><path d="M9 9l10-2" {...common}/></>
      break
    case 'public-order':
      content = <><path d="M12 3.5 20 7v5c0 4.8-3.3 7.5-8 9-4.7-1.5-8-4.2-8-9V7l8-3.5Z" {...common}/><path d="m8.5 12 2.2 2.2 4.8-5" {...common}/></>
      break
    case 'housing-community':
      content = <><path d="m3 11 9-7 9 7M5.5 10v10h13V10M9.5 20v-6h5v6" {...common}/></>
      break
    case 'fish-catch':
      content = <><path d="M4 12c3.3-4 7.5-5.5 12-3l4-3v12l-4-3c-4.5 2.5-8.7 1-12-3Z" {...common}/><circle cx="9" cy="11" r=".7" fill="currentColor"/><path d="M4 12H2" {...common}/></>
      break
    case 'household-food':
      content = <><path d="M4 10h16c-.5 5.5-3.2 9-8 9s-7.5-3.5-8-9Z" {...common}/><path d="M7 7c1-2 2.5-3 4.5-3M12 8c1-2 2.6-3 5-3" {...common}/></>
      break
    case 'tourism':
      content = <><path d="m3 13 8-2 5-7 2 1-3 6 6 1v2l-7 1-4 5-2-.5 2-5-7 .5v-2Z" {...common}/></>
      break
    case 'housing-utilities':
      content = <><path d="m3 11 9-7 9 7M5.5 10v10h13V10" {...common}/><path d="m13 10-3 5h3l-2 4" {...common}/></>
      break
    case 'household-total':
      content = <><path d="M5 8h14l-1 12H6L5 8ZM9 8V6a3 3 0 0 1 6 0v2" {...common}/></>
      break
    case 'edit':
      content = <><path d="m4 20 4.2-1 10.7-10.7a2.2 2.2 0 0 0-3.2-3.2L5 15.8 4 20Z" {...common}/><path d="m14.5 6.5 3 3" {...common}/></>
      break
    default:
      content = <circle cx="12" cy="12" r="8" {...common}/>
  }

  return <svg className={className} viewBox="0 0 24 24" aria-hidden="true">{content}</svg>
}
