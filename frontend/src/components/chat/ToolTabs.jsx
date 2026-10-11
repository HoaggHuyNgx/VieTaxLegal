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

export default function ToolTabs() {
  const { t } = useI18n()

  return (
    <div className="chat-tool-tabs" role="group" aria-label={t('chat.workspace.toolsAria')}>
      {TOOL_TABS.map(({ id, labelKey, Icon, available }) =>
        available ? (
          <span className="tool-tab is-active" key={id}>
            <Icon />
            {t(labelKey)}
          </span>
        ) : (
          <button type="button" className="tool-tab is-coming-soon" key={id} disabled aria-disabled="true">
            <Icon />
            {t(labelKey)}
            <span className="coming-soon-badge">{t('chat.workspace.comingSoon')}</span>
          </button>
        )
      )}
    </div>
  )
}
