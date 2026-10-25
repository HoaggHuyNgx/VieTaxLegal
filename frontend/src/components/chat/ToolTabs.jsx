import { useI18n } from '../../i18n/useI18n'
import { CalculatorIcon, LegalIcon, ScanIcon } from './ChatIcons'

// The tax calculator and contract scan have no backend endpoint yet, so they
// render disabled with a "coming soon" badge instead of faking a feature that
// does not exist.
const TOOL_TABS = [
  { id: 'legal', labelKey: 'chat.workspace.toolLabel', Icon: LegalIcon, available: true },
  { id: 'tax', labelKey: 'chat.workspace.toolTax', Icon: CalculatorIcon, available: false },
  { id: 'scan', labelKey: 'chat.workspace.toolScan', Icon: ScanIcon, available: false },
]

const TAB =
  'flex min-h-[40px] items-center gap-2 rounded-chat-sm border-0 px-4 whitespace-nowrap lte-760:min-h-[34px] lte-760:gap-[5px] lte-760:px-[10px] [&_svg]:size-[18px] [&_svg]:flex-none lte-760:[&_svg]:size-[15px]'
const TAB_ACTIVE = 'bg-chat-tab-active text-[12px] font-[650] text-chat-blue lte-760:text-[10.5px]'
// Shared "not available yet" look for every control without a backend (see also ChatWorkspace).
const TAB_SOON = 'bg-transparent opacity-[0.62]'

export default function ToolTabs() {
  const { t } = useI18n()

  return (
    <div
      className="mx-auto mt-1 mb-[22px] flex items-center gap-[6px] rounded-chat border border-chat-border bg-chat-surface p-[5px] shadow-chat-soft lte-760:mb-3 lte-760:max-w-full lte-760:overflow-x-auto lte-760:p-1"
      role="group"
      aria-label={t('chat.workspace.toolsAria')}
    >
      {TOOL_TABS.map(({ id, labelKey, Icon, available }) =>
        available ? (
          <span className={`${TAB} ${TAB_ACTIVE}`} key={id}>
            <Icon />
            {t(labelKey)}
          </span>
        ) : (
          <button type="button" className={`${TAB} ${TAB_SOON}`} key={id} disabled aria-disabled="true">
            <Icon />
            {t(labelKey)}
            <span className="rounded-chat-pill bg-chat-border-soft px-[7px] py-[2px] text-[9px] font-[650] tracking-[0.1px] text-chat-badge">
              {t('chat.workspace.comingSoon')}
            </span>
          </button>
        )
      )}
    </div>
  )
}
