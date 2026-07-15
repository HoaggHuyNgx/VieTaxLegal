import { useState } from 'react'
import { suggestedQuestions } from '../../data/chat'
import {
  AttachmentIcon,
  BookmarkIcon,
  CalculatorIcon,
  ChevronDownIcon,
  CopyIcon,
  LegalIcon,
  LogoMark,
  ScanIcon,
  SendIcon,
  ShareIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
} from './ChatIcons'

const toolTabs = [
  { id: 'legal', label: 'Tra cứu pháp luật', icon: LegalIcon },
  { id: 'tax', label: 'Tính thuế', icon: CalculatorIcon },
  { id: 'contract', label: 'Scan hợp đồng', icon: ScanIcon },
]

function Citation({ id, onSelect }) {
  return (
    <button
      type="button"
      className="inline-citation"
      onClick={() => onSelect(id)}
      aria-label={`Xem nguồn trích dẫn ${id}`}
    >
      {id}
    </button>
  )
}

function AssistantReply({ onSelectSource }) {
  return (
    <article className="assistant-message">
      <div className="assistant-avatar">
        <LogoMark size={25} />
      </div>
      <div className="assistant-bubble">
        <p>
          Doanh nghiệp được khấu trừ thuế GTGT và tính vào chi phí được trừ khi chi hộ cho nhân viên nếu đáp
          ứng đầy đủ các điều kiện sau:
        </p>
        <ol className="answer-list">
          <li>
            <strong>Khấu trừ thuế GTGT:</strong> Doanh nghiệp được khấu trừ thuế GTGT đầu vào nếu có hóa đơn
            GTGT hợp pháp tên và mã số thuế của doanh nghiệp; hàng hóa/dịch vụ phục vụ cho hoạt động sản xuất
            kinh doanh chịu thuế GTGT. <Citation id={1} onSelect={onSelectSource} />
          </li>
          <li>
            <strong>Tính vào chi phí được trừ khi xác định thuế TNDN:</strong> Khoản chi hộ được tính vào chi
            phí được trừ nếu đáp ứng đồng thời các điều kiện:
          </li>
        </ol>
        <ul className="check-list">
          <li>Khoản chi thực tế phát sinh liên quan đến hoạt động sản xuất kinh doanh.</li>
          <li>Có đủ hóa đơn, chứng từ hợp pháp theo quy định.</li>
          <li>Có chứng từ thanh toán không dùng tiền mặt đối với khoản chi từ 5 triệu đồng trở lên.</li>
          <li>
            Có quyết định cử đi công tác, chương trình công tác và các chứng từ liên quan khác.{' '}
            <Citation id={2} onSelect={onSelectSource} />
          </li>
        </ul>
        <p className="answer-note">
          Lưu ý: Trường hợp hóa đơn dịch vụ (vé máy bay, khách sạn) không thể hiện tên doanh nghiệp, cần có
          thêm chứng từ bổ sung chứng minh việc chi hộ như xác nhận của nhân viên, bảng kê chi hộ, chứng từ
          thanh toán để đảm bảo tính hợp lệ. <Citation id={3} onSelect={onSelectSource} />
        </p>
        <div className="answer-actions">
          <button type="button" aria-label="Câu trả lời hữu ích">
            <ThumbsUpIcon />
          </button>
          <button type="button" aria-label="Câu trả lời chưa hữu ích">
            <ThumbsDownIcon />
          </button>
          <button type="button" aria-label="Sao chép câu trả lời">
            <CopyIcon />
          </button>
          <button type="button" aria-label="Lưu câu trả lời">
            <BookmarkIcon />
          </button>
          <button type="button" aria-label="Chia sẻ câu trả lời">
            <ShareIcon />
          </button>
        </div>
        <div className="answer-sources">
          <h3>Trích dẫn nguồn</h3>
          <div className="answer-source-row">
            <Citation id={1} onSelect={onSelectSource} />
            <span>Luật Thuế GTGT 2008 (sửa đổi 2013)</span>
            <i /> <span>Điều 12, Khoản 1</span>
          </div>
          <div className="answer-source-row">
            <Citation id={2} onSelect={onSelectSource} />
            <span>Thông tư 78/2014/TT-BTC</span>
            <i /> <span>Điều 6, Khoản 2.6</span>
          </div>
          <div className="answer-source-row">
            <Citation id={3} onSelect={onSelectSource} />
            <span>Công văn 5260/TCT-DNL</span>
            <i /> <span>Ngày 30/12/2016</span>
          </div>
          <button type="button" onClick={() => onSelectSource(1)}>
            Xem thêm nguồn (2)
          </button>
        </div>
      </div>
    </article>
  )
}

export default function ChatWorkspace({ activeTool, onChangeTool, onSelectSource, messages, onSend }) {
  const [message, setMessage] = useState('')

  const submitMessage = (event) => {
    event.preventDefault()
    const trimmedMessage = message.trim()
    if (!trimmedMessage) return
    onSend(trimmedMessage)
    setMessage('')
  }

  return (
    <main className="chat-workspace">
      <div className="chat-tabs" role="tablist" aria-label="Công cụ VieTaxLegal">
        {toolTabs.map((tab) => {
          const TabIcon = tab.icon
          return (
            <button
              type="button"
              key={tab.id}
              role="tab"
              aria-selected={activeTool === tab.id}
              className={activeTool === tab.id ? 'active' : ''}
              onClick={() => onChangeTool(tab.id)}
            >
              <TabIcon />
              {tab.label}
            </button>
          )
        })}
      </div>
      <div className="chat-scroll-area">
        <div className="chat-thread">
          <article className="user-message">
            <p>
              Khi doanh nghiệp chi hộ cho nhân viên (ví dụ: mua vé máy bay công tác, đặt phòng khách sạn),
              doanh nghiệp có được khấu trừ thuế GTGT và tính vào chi phí được trừ khi xác định thuế TNDN
              không?
            </p>
            <time>10:24</time>
          </article>
          <AssistantReply onSelectSource={onSelectSource} />
          {messages.map((item) => (
            <article className="user-message additional-message" key={item.id}>
              <p>{item.text}</p>
              <time>Vừa xong</time>
            </article>
          ))}
        </div>
      </div>
      <div className="chat-composer-area">
        <div className="suggestion-list">
          {suggestedQuestions.map((question) => (
            <button type="button" key={question} onClick={() => setMessage(question)}>
              {question}
            </button>
          ))}
        </div>
        <form className="chat-composer" onSubmit={submitMessage}>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Nhập câu hỏi pháp lý hoặc thuế của bạn..."
            rows="2"
            aria-label="Câu hỏi của bạn"
          />
          <div className="composer-actions">
            <button type="button">
              <AttachmentIcon />
              Đính kèm tệp
            </button>
            <button type="button">
              Chọn phạm vi trả lời <ChevronDownIcon />
            </button>
            <button type="submit" className="send-button" disabled={!message.trim()} aria-label="Gửi câu hỏi">
              <SendIcon />
            </button>
          </div>
        </form>
        <p className="chat-disclaimer">
          VieTaxLegal có thể mắc sai sót. Vui lòng kiểm tra lại thông tin trước khi áp dụng.
        </p>
      </div>
    </main>
  )
}
