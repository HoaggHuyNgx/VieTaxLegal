// Tailwind class strings shared by AuthCard, LoginForm and RegisterForm. Kept as full
// literals (never built from fragments at runtime) so Tailwind's scanner sees them.

export const FOCUS_RING =
  'focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-auth-focus-ring'

export const TAB_BASE = `flex-1 -mb-0.5 cursor-pointer border-0 border-b-2 bg-transparent px-4 py-3 text-[1rem] font-medium transition-[color,border-color] duration-200 ease-[ease] ${FOCUS_RING}`
export const TAB_ACTIVE = 'border-b-blue-primary text-blue-primary'
export const TAB_IDLE = 'border-b-transparent text-gray-700'

export const FIELD_GROUP = 'mb-[1.1rem]'
export const LABEL = 'mb-[0.45rem] block text-[0.875rem] font-medium text-gray-700'
export const INPUT =
  'min-h-[2.85rem] w-full rounded-xl border border-gray-300 py-[0.7rem] [font-family:inherit] [line-height:inherit] text-[0.95rem] text-gray-900 transition-[border-color,box-shadow] duration-200 ease-[ease] placeholder:text-auth-placeholder focus:border-blue-primary focus:shadow-auth-focus focus:outline-none aria-invalid:border-auth-danger'
// Horizontal padding is separate so a password field can swap it without two
// competing padding-right utilities on one element.
export const INPUT_PADDING = 'px-[0.9rem]'
export const INPUT_PADDING_PASSWORD = 'pr-12 pl-[0.9rem]'

export const REQUIRED_MARK = 'text-auth-danger'
export const OPTIONAL_MARK = 'text-[0.78rem] font-normal text-auth-muted'
export const FIELD_ERROR = 'mt-[0.35rem] text-[0.78rem] leading-[1.35] text-auth-error'

export const TOGGLE_PASSWORD = `absolute top-1/2 right-[0.65rem] inline-flex size-8 cursor-pointer items-center justify-center border-none bg-transparent p-0 text-auth-muted [transform:translateY(-50%)] ${FOCUS_RING}`

export const CHECKBOX_LABEL =
  'flex cursor-pointer items-start gap-2 text-[0.85rem] leading-[1.45] text-gray-700'
export const CHECKBOX_INPUT = 'mt-[0.15rem] size-4 accent-blue-primary'
export const TERMS_LABEL = '-mt-[0.1rem] mb-4'
export const TERMS_LINK = `font-medium text-blue-primary no-underline hover:underline ${FOCUS_RING}`
// `font: inherit` here also resets weight to the inherited value, so no font-medium.
export const FORGOT_LINK = `cursor-pointer border-none bg-transparent p-0 [font:inherit] text-blue-primary no-underline hover:underline ${FOCUS_RING}`

export const FEEDBACK = 'mb-4 rounded-[0.65rem] px-[0.85rem] py-[0.7rem] text-[0.84rem] leading-[1.45]'
export const FEEDBACK_TONE = {
  error: 'bg-feedback-error-bg text-feedback-error-fg',
  success: 'bg-feedback-success-bg text-feedback-success-fg',
  info: 'bg-feedback-info-bg text-feedback-info-fg',
}

const BUTTON_BASE = `flex min-h-[2.95rem] w-full cursor-pointer items-center justify-center rounded-xl [font-family:inherit] [line-height:inherit] text-[0.95rem] font-semibold transition-[background,border-color,box-shadow,transform] duration-200 ease-[ease] ${FOCUS_RING}`
export const PRIMARY_BUTTON = `${BUTTON_BASE} border border-blue-primary bg-blue-primary px-5 py-[0.8rem] text-white hover:not-disabled:border-blue-bright hover:not-disabled:bg-blue-bright hover:not-disabled:shadow-auth-primary-hover hover:not-disabled:[transform:translateY(-1px)] disabled:cursor-wait disabled:opacity-[0.72]`
export const GOOGLE_BUTTON = `${BUTTON_BASE} gap-[0.7rem] border border-gray-300 bg-white px-5 py-[0.8rem] text-gray-700 hover:border-gray-400 hover:bg-gray-50 hover:shadow-auth-google-hover`

export const SECONDARY_BUTTON = `cursor-pointer rounded-xl border border-blue-primary bg-white px-4 py-[0.6rem] [font-family:inherit] text-[0.85rem] font-semibold whitespace-nowrap text-blue-primary transition-[background] duration-200 ease-[ease] hover:not-disabled:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 ${FOCUS_RING}`

export const DIVIDER =
  'my-5 flex items-center text-[0.85rem] text-gray-700 before:h-px before:flex-1 before:bg-gray-300 after:h-px after:flex-1 after:bg-gray-300'
