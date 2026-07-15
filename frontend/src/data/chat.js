export const conversationGroups = [
  {
    label: 'HÔM NAY',
    items: [
      { id: 'invoice-staff', title: 'Hóa đơn điện tử khi chi hộ cho nhân viên', time: '10:24' },
      { id: 'meal-tax', title: 'Khấu trừ thuế GTGT dịch vụ ăn uống', time: '09:18' },
      { id: 'vat-refund', title: 'Quy định về hoàn thuế GTGT', time: '08:47' },
    ],
  },
  {
    label: 'HÔM QUA',
    items: [
      { id: 'corporate-tax', title: 'Ưu đãi thuế TNDN cho doanh nghiệp...', time: '16:20' },
      { id: 'software-policy', title: 'Chính sách thuế đối với phần mềm...', time: '14:05' },
    ],
  },
  {
    label: '7 NGÀY QUA',
    items: [
      { id: 'loan-costs', title: 'Hạch toán chi phí lãi vay', time: '11:33' },
      { id: 'tax-id', title: 'Thủ tục đăng ký MST cho CN', time: '10:02' },
      { id: 'contract', title: 'Quy định về lập HĐĐT', time: '09:11' },
    ],
  },
]

export const assistantSources = [
  {
    id: 1,
    title: 'Luật Thuế GTGT 2008 (sửa đổi 2013)',
    article: 'Điều 12, Khoản 1',
    type: 'Luật',
    date: '01/01/2014 - Hiện hành',
  },
  {
    id: 2,
    title: 'Thông tư 78/2014/TT-BTC',
    article: 'Điều 6, Khoản 2.6',
    type: 'Thông tư',
    date: '10/08/2014 - Hiện hành',
  },
  {
    id: 3,
    title: 'Công văn 5260/TCT-DNL',
    article: 'Hướng dẫn chi phí công tác',
    type: 'Công văn',
    date: '30/12/2016',
  },
]

export const suggestedQuestions = [
  'Chi hộ cho người thân có được tính chi phí không?',
  'Chi hộ bằng tiền mặt có được tính chi phí không?',
  'Mẫu bảng kê chi hộ cho nhân viên gồm những nội dung gì?',
]
