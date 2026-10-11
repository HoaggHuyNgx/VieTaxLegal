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

export default function SuggestionGrid({ onPick }) {
  const { t } = useI18n()

  return (
    <div className="suggestion-grid">
      {suggestedQuestions.map((question) => {
        const Icon = SUGGESTION_ICONS[question.icon]
        return (
          <button
            type="button"
            className="suggestion-card"
            key={question.id}
            aria-label={t('chat.workspace.suggestionAria', { question: question.text })}
            onClick={() => onPick(question.text)}
          >
            <span className={`suggestion-icon tint-${question.tint}`} aria-hidden="true">
              {Icon ? <Icon /> : null}
            </span>
            <span className="suggestion-text">{question.text}</span>
            <span className="suggestion-arrow" aria-hidden="true">
              <ArrowRightIcon />
            </span>
          </button>
        )
      })}
    </div>
  )
}
