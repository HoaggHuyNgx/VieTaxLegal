function Icon({ children, size = 20, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true" {...props}>
      {children}
    </svg>
  )
}

export function LogoMark({ size = 38 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 36" fill="none" aria-hidden="true">
      <path d="M3 4h11.2L20 17.1 25.8 4H37L20 33 3 4Z" fill="url(#logo-gradient)" />
      <defs>
        <linearGradient id="logo-gradient" x1="5" y1="4" x2="31" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#12C7FF" />
          <stop offset="1" stopColor="#1648E6" />
        </linearGradient>
      </defs>
    </svg>
  )
}

export function PlusIcon() {
  return (
    <Icon>
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </Icon>
  )
}

export function SearchIcon() {
  return (
    <Icon>
      <circle cx="10.8" cy="10.8" r="5.8" stroke="currentColor" strokeWidth="1.8" />
      <path d="m16 16 4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </Icon>
  )
}

export function MenuIcon() {
  return (
    <Icon>
      <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </Icon>
  )
}

export function ChevronDownIcon() {
  return (
    <Icon size={16}>
      <path
        d="m6 9 6 6 6-6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}

export function LegalIcon() {
  return (
    <Icon>
      <rect x="5" y="4" width="14" height="16" rx="2" stroke="currentColor" strokeWidth="1.7" />
      <path d="M9 9h6M9 13h6M9 17h3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </Icon>
  )
}

export function SendIcon() {
  return (
    <Icon>
      <path
        d="m20 4-7.8 16-2.1-6-6.1-2L20 4Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="m10.2 13.8 4-4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </Icon>
  )
}

export function CopyIcon() {
  return (
    <Icon size={18}>
      <rect x="8" y="8" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"
        stroke="currentColor"
        strokeWidth="1.6"
      />
    </Icon>
  )
}
