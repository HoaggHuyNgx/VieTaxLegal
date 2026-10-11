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

export function SortIcon() {
  return (
    <Icon size={16}>
      <path d="M4 6h16M6 12h12M9 18h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </Icon>
  )
}

export function MinusIcon() {
  return (
    <Icon size={16}>
      <path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </Icon>
  )
}

export function ArrowRightIcon() {
  return (
    <Icon size={16}>
      <path
        d="M5 12h13m-5-5 5 5-5 5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}

export function SparkleIcon({ size = 16 }) {
  return (
    <Icon size={size}>
      <path d="M12 3.5 13.7 9l5.5 1.7-5.5 1.7L12 18l-1.7-5.6L4.8 10.7 10.3 9 12 3.5Z" fill="currentColor" />
    </Icon>
  )
}

export function ChatBubbleIcon({ size = 26 }) {
  return (
    <Icon size={size}>
      <path
        d="M20 12.5a7 7 0 0 1-7 7H8.6L5 21.5l.9-3.4A7 7 0 0 1 11 5h2a7 7 0 0 1 7 7v.5Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M9.5 12.2h5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </Icon>
  )
}

export function CalculatorIcon() {
  return (
    <Icon>
      <rect x="5" y="3.5" width="14" height="17" rx="2.2" stroke="currentColor" strokeWidth="1.7" />
      <rect x="8" y="6.5" width="8" height="3" rx="1" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M9 13h.01M12 13h.01M15 13h.01M9 16.5h.01M12 16.5h.01M15 16.5h.01"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </Icon>
  )
}

export function ScanIcon() {
  return (
    <Icon>
      <path
        d="M4 8.5V6a2 2 0 0 1 2-2h2.5M20 8.5V6a2 2 0 0 0-2-2h-2.5M4 15.5V18a2 2 0 0 0 2 2h2.5M20 15.5V18a2 2 0 0 1-2 2h-2.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
      <path d="M4 12h16" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </Icon>
  )
}

export function PaperclipIcon() {
  return (
    <Icon size={18}>
      <path
        d="M18 11.5 12.2 17.3a3.9 3.9 0 0 1-5.5-5.5l6.4-6.4a2.6 2.6 0 0 1 3.7 3.7l-6.4 6.4a1.3 1.3 0 0 1-1.9-1.8l5.6-5.6"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}

export function DocumentIcon({ size = 18 }) {
  return (
    <Icon size={size}>
      <path
        d="M13.5 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9l-5.5-5.5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path d="M13.5 3.5V9H19" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </Icon>
  )
}

export function ShieldIcon({ size = 13 }) {
  return (
    <Icon size={size}>
      <path
        d="M12 3.2 5.5 6v5.3c0 4 2.7 7.5 6.5 8.5 3.8-1 6.5-4.5 6.5-8.5V6L12 3.2Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path
        d="m9.3 11.8 1.9 1.9 3.5-3.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}

export function ReceiptIcon() {
  return (
    <Icon>
      <path
        d="M6 3.5h12v17l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4-2 1.4v-17Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M12 7v8m2-6.4c-.5-.5-1.2-.8-2-.8-1.1 0-2 .6-2 1.5S10.9 11 12 11s2 .6 2 1.5-.9 1.5-2 1.5c-.8 0-1.5-.3-2-.8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </Icon>
  )
}

export function PeopleIcon() {
  return (
    <Icon>
      <circle cx="9.5" cy="8.5" r="3" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M3.8 19c0-2.8 2.6-5 5.7-5s5.7 2.2 5.7 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path
        d="M16 6.2a2.9 2.9 0 0 1 0 5.6M17.2 14.4c1.8.6 3 2 3 3.9"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </Icon>
  )
}

export function DocumentCheckIcon() {
  return (
    <Icon>
      <path
        d="M13.5 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9l-5.5-5.5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path d="M13.5 3.5V9H19" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path
        d="m8.8 14.3 2 2 4-4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}

export function BuildingIcon() {
  return (
    <Icon>
      <path
        d="M4 20.5h16M6 20.5V5a1.5 1.5 0 0 1 1.5-1.5h6A1.5 1.5 0 0 1 15 5v15.5M15 9.5h2.5A1.5 1.5 0 0 1 19 11v9.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path
        d="M8.8 7h3.4M8.8 10.5h3.4M8.8 14h3.4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </Icon>
  )
}
