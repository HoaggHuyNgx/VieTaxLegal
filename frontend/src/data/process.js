import askIcon from '../assets/images/icons/process-ask-icon.svg'
import analysisIcon from '../assets/images/icons/process-analysis-icon.svg'
import researchIcon from '../assets/images/icons/process-research-icon.svg'
import answerIcon from '../assets/images/icons/process-answer-icon.svg'

export const processSteps = [
  {
    number: 1,
    icon: askIcon,
    title: 'Đặt câu hỏi',
    description: 'Mô tả câu hỏi pháp luật và các dữ kiện quan trọng của tình huống.',
  },
  {
    number: 2,
    icon: analysisIcon,
    title: 'Phân tích ngữ cảnh',
    description: 'Trợ lý sử dụng câu hỏi và lịch sử gần nhất để hiểu vấn đề.',
  },
  {
    number: 3,
    icon: researchIcon,
    title: 'Phản hồi trực tiếp',
    description: 'Câu trả lời được hiển thị từng phần ngay khi mô hình đang xử lý.',
  },
  {
    number: 4,
    icon: answerIcon,
    title: 'Kiểm tra trước khi áp dụng',
    description: 'Đối chiếu văn bản hiện hành hoặc tham vấn chuyên gia cho quyết định quan trọng.',
  },
]
