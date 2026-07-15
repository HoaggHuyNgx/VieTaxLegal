import askIcon from '../assets/images/icons/process-ask-icon.svg'
import analysisIcon from '../assets/images/icons/process-analysis-icon.svg'
import researchIcon from '../assets/images/icons/process-research-icon.svg'
import answerIcon from '../assets/images/icons/process-answer-icon.svg'

export const processSteps = [
  {
    number: 1,
    icon: askIcon,
    title: 'Đặt câu hỏi',
    description: 'Nhập câu hỏi pháp lý, thuế hoặc tải tài liệu cần phân tích.',
  },
  {
    number: 2,
    icon: analysisIcon,
    title: 'Phân tích ngữ cảnh',
    description: 'AI hiểu nội dung và xác định vấn đề cốt lõi.',
  },
  {
    number: 3,
    icon: researchIcon,
    title: 'Đối chiếu căn cứ',
    description: 'Hệ thống truy xuất văn bản, điều khoản và nguồn liên quan.',
  },
  {
    number: 4,
    icon: answerIcon,
    title: 'Trả lời rõ ràng',
    description: 'Nhận câu trả lời dễ hiểu, có trích dẫn và gợi ý hành động.',
  },
]
