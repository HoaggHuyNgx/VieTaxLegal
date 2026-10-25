import { suggestedQuestions } from '../../data/chat'
import { useI18n } from '../../i18n/useI18n'
import { ArrowRightIcon, BuildingIcon, DocumentCheckIcon, PeopleIcon, ReceiptIcon } from './ChatIcons'

// Kept local and unexported: ChatIcons.jsx exports only components, and adding a
// non-component const there would trip react-refresh/only-export-components.
// ESLint runs with --max-warnings 0, so that warning would fail the build.
const SUGGESTION_ICONS = {
  receipt: ReceiptIcon,
  people: PeopleIcon,
  documentCheck: DocumentCheckIcon,
  building: BuildingIcon,
}

// Full literals, not `tint-${x}`: Tailwind only sees class names it can read in the source.
const TINT_CLASSES = {
  blue: 'bg-tint-blue-bg text-tint-blue-fg',
  violet: 'bg-tint-violet-bg text-tint-violet-fg',
  green: 'bg-tint-green-bg text-tint-green-fg',
  orange: 'bg-tint-orange-bg text-tint-orange-fg',
}

const GRID =
  'mb-[18px] grid grid-cols-[repeat(4,minmax(0,1fr))] gap-[13px] lte-1100:grid-cols-[repeat(2,minmax(0,1fr))] lte-760:mb-3 lte-760:grid-cols-[minmax(0,1fr)] lte-760:gap-2'
const CARD =
  'group relative flex min-h-[148px] flex-col rounded-chat-lg border border-chat-border bg-chat-surface p-[16px_15px_46px] text-left shadow-chat-soft transition-[border-color,box-shadow] duration-150 ease-[ease] hover:border-chat-search-focus hover:shadow-chat-suggestion-hover motion-reduce:transition-none lte-1220:min-h-[158px] lte-1220:p-[14px_13px_44px] lte-1100:min-h-[120px] lte-760:min-h-0 lte-760:flex-row lte-760:items-center lte-760:gap-[11px] lte-760:p-[11px_42px_11px_12px]'
const ICON =
  'mb-[13px] grid size-[38px] place-items-center rounded-chat lte-760:mb-0 lte-760:size-8 lte-760:flex-none lte-760:[&_svg]:size-[17px]'
const ARROW =
  'absolute right-[14px] bottom-[14px] grid size-[26px] place-items-center rounded-[50%] bg-chat-panel text-chat-muted [.group:hover_&]:bg-chat-blue [.group:hover_&]:text-white lte-760:top-1/2 lte-760:right-[11px] lte-760:bottom-auto lte-760:size-[22px] lte-760:[transform:translateY(-50%)]'

export default function SuggestionGrid({ onPick }) {
  const { t } = useI18n()

  return (
    <div className={GRID}>
      {suggestedQuestions.map((question) => {
        const Icon = SUGGESTION_ICONS[question.icon]
        return (
          <button
            type="button"
            className={CARD}
            key={question.id}
            aria-label={t('chat.workspace.suggestionAria', { question: question.text })}
            onClick={() => onPick(question.text)}
          >
            <span className={`${ICON} ${TINT_CLASSES[question.tint]}`} aria-hidden="true">
              {Icon ? <Icon /> : null}
            </span>
            {/* Vietnamese does not break between syllables; long accented words overflow the narrow 4th column. */}
            <span className="text-[11.5px] leading-[1.55] font-semibold text-chat-ink-soft [overflow-wrap:anywhere]">
              {question.text}
            </span>
            <span className={ARROW} aria-hidden="true">
              <ArrowRightIcon />
            </span>
          </button>
        )
      })}
    </div>
  )
}
