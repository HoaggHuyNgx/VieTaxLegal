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
export function CloseIcon() {
  return (
    <Icon>
      <path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </Icon>
  )
}
export function ShieldIcon() {
  return (
    <Icon>
      <path
        d="M12 3.5 19 6v5.7c0 4.1-2.8 7.7-7 8.8-4.2-1.1-7-4.7-7-8.8V6l7-2.5Z"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path
        d="m9.2 12 1.9 1.9 3.8-4.2"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}
export function HistoryIcon() {
  return (
    <Icon>
      <path
        d="M4 12a8 8 0 1 0 2.1-5.4L4 9"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M4 4v5h5M12 7v5l3 2"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
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
export function CalculatorIcon() {
  return (
    <Icon>
      <rect x="5" y="3.5" width="14" height="17" rx="2" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M8.5 7.5h7M8.5 12h1M12 12h1M15.5 12h.1M8.5 15.5h1M12 15.5h1M15.5 15.5h.1"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </Icon>
  )
}
export function ScanIcon() {
  return (
    <Icon>
      <rect x="5" y="5" width="10" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M9 9h7.5A1.5 1.5 0 0 1 18 10.5v8A1.5 1.5 0 0 1 16.5 20H9M8 12h4M8 15h5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </Icon>
  )
}
export function AttachmentIcon() {
  return (
    <Icon>
      <path
        d="m8.2 12.7 5.1-5.1a3.1 3.1 0 0 1 4.4 4.4l-6.4 6.4a4.4 4.4 0 0 1-6.2-6.2l6-6"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
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
export function BookIcon() {
  return (
    <Icon>
      <path
        d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v16H7.5A2.5 2.5 0 0 0 5 21.5v-16Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M5 19a2.5 2.5 0 0 1 2.5-2.5H19" stroke="currentColor" strokeWidth="1.7" />
    </Icon>
  )
}
export function ExternalIcon() {
  return (
    <Icon size={17}>
      <path
        d="M14 5h5v5M11 13l8-8M19 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}
export function ThumbsUpIcon() {
  return (
    <Icon size={18}>
      <path
        d="M7.5 10v9H5.8A1.8 1.8 0 0 1 4 17.2v-5.4A1.8 1.8 0 0 1 5.8 10h1.7ZM7.5 19h8.1c1.1 0 2-.8 2.2-1.8l.9-5A1.9 1.9 0 0 0 16.8 10h-3l.5-2.4a2.5 2.5 0 0 0-1.1-2.5L12 4 7.5 10v9Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </Icon>
  )
}
export function ThumbsDownIcon() {
  return (
    <Icon size={18}>
      <g transform="rotate(180 12 12)">
        <path
          d="M7.5 10v9H5.8A1.8 1.8 0 0 1 4 17.2v-5.4A1.8 1.8 0 0 1 5.8 10h1.7ZM7.5 19h8.1c1.1 0 2-.8 2.2-1.8l.9-5A1.9 1.9 0 0 0 16.8 10h-3l.5-2.4a2.5 2.5 0 0 0-1.1-2.5L12 4 7.5 10v9Z"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </g>
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
export function BookmarkIcon() {
  return (
    <Icon size={18}>
      <path
        d="M6 4.5A1.5 1.5 0 0 1 7.5 3h9A1.5 1.5 0 0 1 18 4.5V21l-6-3.5L6 21V4.5Z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </Icon>
  )
}
export function ShareIcon() {
  return (
    <Icon size={18}>
      <path
        d="M13.5 6 18 10.5 13.5 15M18 10.5H9a5 5 0 0 0-5 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}
export function HelpIcon() {
  return (
    <Icon>
      <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M9.8 9a2.3 2.3 0 1 1 3.7 1.8c-.9.7-1.5 1.1-1.5 2.2M12 16.5h.01"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
    </Icon>
  )
}
export function SettingsIcon() {
  return (
    <Icon>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.7" />
      <path
        d="M19 13.5a1.7 1.7 0 0 0 .3 1.8l.1.1-2 2-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5v.2h-3v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1-2-2 .1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H5.3v-3h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1 2-2 .1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5v-.2h3v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1 2 2-.1.1a1.7 1.7 0 0 0-.3 1.8 1.7 1.7 0 0 0 1.5 1h.2v3h-.2a1.7 1.7 0 0 0-1.5 1Z"
        stroke="currentColor"
        strokeWidth="1.35"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Icon>
  )
}
