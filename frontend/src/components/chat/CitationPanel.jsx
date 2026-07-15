import { useState } from 'react'
import { assistantSources } from '../../data/chat'
import { ChevronDownIcon, CloseIcon, ExternalIcon } from './ChatIcons'

export default function CitationPanel({ selectedSource, onSelectSource, onClose, isOpen }) {
  const [expandedSource, setExpandedSource] = useState(2)
  const source = assistantSources.find((item) => item.id === selectedSource) ?? assistantSources[0]

  return (
    <aside className={`citation-panel ${isOpen ? 'is-open' : ''}`} aria-label="Thông tin trích dẫn">
      <header className="citation-header">
        <h2>Thông tin trích dẫn</h2>
        <button type="button" aria-label="Đóng thông tin trích dẫn" onClick={onClose}>
          <CloseIcon />
        </button>
      </header>
      <div className="citation-content">
        <div className="citation-title">
          <span className="source-number">{source.id}</span>
          <h3>{source.title}</h3>
        </div>
        <dl className="citation-meta">
          <div>
            <dt>Điều khoản</dt>
            <dd>{source.article}</dd>
          </div>
          <div>
            <dt>Hiệu lực</dt>
            <dd>{source.date}</dd>
          </div>
          <div>
            <dt>Loại văn bản</dt>
            <dd>{source.type}</dd>
          </div>
          <div>
            <dt>Cơ quan ban hành</dt>
            <dd>Quốc hội</dd>
          </div>
        </dl>
        <button type="button" className="original-document-button">
          Xem văn bản gốc <ExternalIcon />
        </button>
      </div>
      <section className="document-preview">
        <h3>Xem trước văn bản</h3>
        <div className="document-toolbar">
          <button type="button">−</button>
          <span>105%</span>
          <button type="button">+</button>
          <i />
          <button type="button">1</button>
          <span>12</span>
          <button type="button">+</button>
        </div>
        <article className="legal-document">
          <p>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</p>
          <small>Độc lập - Tự do - Hạnh phúc</small>
          <hr />
          <h4>
            LUẬT
            <br />
            THUẾ GIÁ TRỊ GIA TĂNG
          </h4>
          <em>Số 13/2008/QH12</em>
          <p className="document-section">Điều 12. Khấu trừ thuế giá trị gia tăng đầu vào</p>
          <ol>
            <li>Người nộp thuế được khấu trừ thuế giá trị gia tăng đầu vào nếu có đủ các điều kiện sau:</li>
            <li>Có hóa đơn giá trị gia tăng hợp pháp của hàng hóa, dịch vụ mua vào.</li>
            <li>
              Hàng hóa, dịch vụ mua vào dùng cho sản xuất, kinh doanh hàng hóa chịu thuế giá trị gia tăng.
            </li>
          </ol>
          <footer>Trang 1 / 12</footer>
        </article>
      </section>
      <div className="source-accordions">
        {assistantSources.slice(1).map((item) => (
          <section key={item.id} className="source-accordion">
            <button
              type="button"
              aria-expanded={expandedSource === item.id}
              onClick={() => {
                setExpandedSource((current) => (current === item.id ? null : item.id))
                onSelectSource(item.id)
              }}
            >
              <span className="source-number">{item.id}</span>
              <span>{item.title}</span>
              <ChevronDownIcon />
            </button>
            {expandedSource === item.id ? (
              <p>
                {item.article} · {item.date}
              </p>
            ) : null}
          </section>
        ))}
        <button type="button" className="all-sources-button">
          Mở tất cả nguồn (3)
        </button>
      </div>
    </aside>
  )
}
