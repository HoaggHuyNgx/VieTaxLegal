// Vietnamese is the default locale and the source of truth for copy.
// Every key added here must also be added to en.js — catalog.test.js enforces it.
//
// Decorative capitalisation lives in CSS (.eyebrow has text-transform: uppercase),
// never in this file: all-caps text in the DOM is spelled out letter by letter by
// some screen readers.
const vi = {
  common: {
    languageLabel: 'Ngôn ngữ',
    localeVi: 'Tiếng Việt',
    localeEn: 'Tiếng Anh',
    brandName: 'VieTaxLegal',
    pageTitle: 'VieTaxLegal - AI pháp lý & thuế cho doanh nghiệp Việt Nam',
    pageDescription: 'VieTaxLegal — AI pháp lý và thuế cho doanh nghiệp Việt Nam',
  },

  landing: {
    hero: {
      tagline: 'Trợ lý tra cứu pháp luật cho doanh nghiệp Việt Nam',
      description:
        'Đặt câu hỏi, nhận phản hồi trực tiếp và lưu lại lịch sử trong một không gian riêng cho tài khoản của bạn.',
      benefits: [
        { id: 'ask', text: 'Đặt câu hỏi pháp luật bằng tiếng Việt.' },
        { id: 'live', text: 'Nhận câu trả lời trực tiếp trong thời gian thực.' },
        { id: 'history', text: 'Lưu và tìm lại lịch sử theo từng tài khoản.' },
        { id: 'privacy', text: 'Dữ liệu hội thoại chỉ được truy cập qua backend bảo vệ.' },
        { id: 'simple', text: 'Giao diện đơn giản, phù hợp để tra cứu ban đầu.' },
        { id: 'verify', text: 'Luôn nhắc kiểm tra hiệu lực văn bản trước khi áp dụng.' },
      ],
    },

    features: {
      eyebrow: 'Tại sao nên chọn VieTaxLegal',
      heading: 'Đặc điểm nổi bật của VieTaxLegal',
      illustrationAlt: 'Trợ lý tra cứu pháp luật',
      items: [
        {
          id: 'legalResearch',
          title: 'Hỏi đáp pháp luật bằng tiếng Việt',
          description: 'Mô tả tình huống và nhận câu trả lời theo ngữ cảnh cuộc hội thoại.',
        },
        {
          id: 'accountHistory',
          title: 'Lịch sử riêng theo tài khoản',
          description: 'Mỗi người dùng chỉ có thể xem và xóa các cuộc hội thoại của chính mình.',
        },
        {
          id: 'liveResponse',
          title: 'Phản hồi trực tiếp',
          description: 'Nội dung xuất hiện ngay khi trợ lý đang tạo câu trả lời, không phải chờ toàn bộ.',
        },
        {
          id: 'usageControl',
          title: 'Kiểm soát chi phí và lạm dụng',
          description: 'Giới hạn lượt hỏi và độ dài giúp bảo vệ tài khoản cũng như quota mô hình AI.',
        },
        {
          id: 'ragReady',
          title: 'Sẵn sàng mở rộng RAG',
          description: 'Kiến trúc đã tách lớp truy xuất để bổ sung nguồn luật được kiểm chứng sau này.',
        },
      ],
    },

    process: {
      eyebrow: 'Cách VieTaxLegal hỗ trợ bạn',
      heading: 'Quy trình hoạt động',
      items: [
        {
          id: 'ask',
          title: 'Đặt câu hỏi',
          description: 'Mô tả câu hỏi pháp luật và các dữ kiện quan trọng của tình huống.',
        },
        {
          id: 'analysis',
          title: 'Phân tích ngữ cảnh',
          description: 'Trợ lý sử dụng câu hỏi và lịch sử gần nhất để hiểu vấn đề.',
        },
        {
          id: 'research',
          title: 'Phản hồi trực tiếp',
          description: 'Câu trả lời được hiển thị từng phần ngay khi mô hình đang xử lý.',
        },
        {
          id: 'verify',
          title: 'Kiểm tra trước khi áp dụng',
          description: 'Đối chiếu văn bản hiện hành hoặc tham vấn chuyên gia cho quyết định quan trọng.',
        },
      ],
    },

    faq: {
      eyebrow: 'Câu hỏi thường gặp',
      items: [
        {
          id: 'trustworthy',
          question: 'VieTaxLegal có đáng tin cậy không?',
          answer:
            'Phiên bản Beta hỗ trợ tra cứu ban đầu bằng AI nhưng chưa có kho nguồn luật RAG. Cần kiểm tra hiệu lực văn bản hoặc tham vấn chuyên gia trước khi áp dụng.',
        },
        {
          id: 'benefits',
          question: 'Lợi ích của VieTaxLegal đối với doanh nghiệp là gì?',
          answer:
            'Giảm thời gian tra cứu, hỗ trợ phát hiện rủi ro và chuẩn bị thông tin trước khi làm việc với chuyên gia.',
        },
        {
          id: 'contracts',
          question: 'VieTaxLegal có hỗ trợ phân tích hợp đồng không?',
          answer:
            'Chưa. Phân tích hợp đồng là tính năng dự kiến cho giai đoạn sau và không xuất hiện trong bản Beta.',
        },
        {
          id: 'tax',
          question: 'VieTaxLegal có hỗ trợ câu hỏi về thuế không?',
          answer:
            'Bản Beta chưa có công cụ tính thuế chuyên biệt. Người dùng chỉ nên dùng khu vực chat để tra cứu pháp luật ở mức tham khảo.',
        },
        {
          id: 'lawyer',
          question: 'Khi nào nên tham khảo thêm luật sư?',
          answer: 'Khi vấn đề có giá trị lớn, tranh chấp, rủi ro cao hoặc cần ý kiến pháp lý chính thức.',
        },
        {
          id: 'english',
          question: 'VieTaxLegal có hỗ trợ tiếng Anh không?',
          answer:
            'Giao diện có cả tiếng Việt và tiếng Anh, chuyển đổi bằng nút VI/EN. Câu trả lời của trợ lý hiện vẫn bằng tiếng Việt, vì với văn bản pháp luật Việt Nam chỉ bản tiếng Việt mới có giá trị pháp lý.',
        },
        {
          id: 'security',
          question: 'Dữ liệu và tài liệu tải lên có được bảo mật không?',
          answer:
            'Bản Beta chưa hỗ trợ tải tài liệu. Hội thoại được phân quyền theo tài khoản và chỉ truy cập qua backend của ứng dụng.',
        },
        {
          id: 'audience',
          question: 'VieTaxLegal phù hợp với ai?',
          answer: 'Doanh nghiệp SME, kế toán, chuyên viên pháp chế, tư vấn thuế và startup.',
        },
      ],
    },

    footer: {
      tagline: 'Trợ lý tra cứu pháp luật cho doanh nghiệp Việt Nam',
      navAria: 'Điều hướng chân trang',
      backToTopAria: 'Lên đầu trang',
      emailLabel: 'Email: {{address}}',
      links: [
        { id: 'product', label: 'Sản phẩm' },
        { id: 'features', label: 'Tính năng' },
        { id: 'pricing', label: 'Bảng giá' },
        { id: 'contact', label: 'Liên hệ' },
        { id: 'privacy', label: 'Chính sách bảo mật' },
      ],
    },
  },

  // Keyed by the backend's stable error `code`, so no intermediate mapping table
  // can drift. Codes with two call-site meanings get a nested variant.
  errors: {
    byCode: {
      REQUEST_FAILED: 'Không thể kết nối đến máy chủ. Vui lòng thử lại.',
      INVALID_RESPONSE: 'Máy chủ trả về dữ liệu không hợp lệ.',
      INVALID_STREAM_EVENT: 'Không thể đọc phản hồi trực tiếp từ máy chủ.',
      EMPTY_STREAM: 'Máy chủ không trả về nội dung phản hồi.',
      TRUNCATED_STREAM: 'Phản hồi bị gián đoạn trước khi hoàn tất.',
      UNAUTHENTICATED: 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn.',
      INVALID_CREDENTIALS: 'Email/tên tài khoản hoặc mật khẩu không đúng.',
      EMAIL_TAKEN: 'Email này đã được sử dụng.',
      USERNAME_TAKEN: 'Tên tài khoản này đã được sử dụng.',
      REGISTRATION_CONFLICT: 'Không thể tạo tài khoản. Vui lòng thử lại.',
      VALIDATION_ERROR: 'Dữ liệu gửi lên chưa hợp lệ.',
      CONVERSATION_NOT_FOUND: 'Không tìm thấy cuộc hội thoại.',
      CHAT_RATE_LIMITED: 'Bạn gửi câu hỏi quá nhanh. Vui lòng thử lại sau ít phút.',
      CHAT_DAILY_LIMIT_REACHED: 'Bạn đã dùng hết lượt chat hôm nay. Vui lòng quay lại vào ngày mai.',
      CHAT_IN_PROGRESS: {
        general: 'Cuộc hội thoại này đang có một câu trả lời được xử lý.',
        delete: 'Hãy dừng câu trả lời trước khi xóa cuộc hội thoại này.',
      },
      CHAT_NOT_CONFIGURED: 'Dịch vụ chat chưa được cấu hình. Vui lòng liên hệ quản trị viên.',
      CHAT_PROVIDER_UNAVAILABLE: 'Dịch vụ trả lời đang tạm thời gián đoạn. Vui lòng thử lại sau.',
    },
  },

  auth: {
    cardAria: 'Đăng nhập hoặc đăng ký',
    tablistAria: 'Xác thực tài khoản',
    tabLogin: 'Đăng nhập',
    tabRegister: 'Đăng ký',
    loginHeading: 'Chào mừng bạn quay trở lại!',
    loginSubtitle: 'Đăng nhập để tiếp tục sử dụng VieTaxLegal',
    registerHeading: 'Đăng ký tài khoản',
    registerSubtitle: 'Tạo tài khoản để bắt đầu sử dụng VieTaxLegal',
    submitting: 'Đang xử lý…',
    submitLogin: 'Đăng nhập',
    submitRegister: 'Tạo tài khoản',
    divider: 'hoặc',
    googleLogin: 'Tiếp tục với Google',
    googleRegister: 'Đăng ký với Google',
    forgotPasswordNotice: 'Tính năng quên mật khẩu sẽ được triển khai ở phiên bản tiếp theo.',
    googleNotice: 'Đăng nhập Google chưa được hỗ trợ ở phiên bản này.',
    checkingSession: 'Đang kiểm tra phiên đăng nhập…',

    fields: {
      identifier: 'Tên tài khoản hoặc email',
      identifierPlaceholder: 'Nhập tên tài khoản hoặc email',
      password: 'Mật khẩu',
      passwordPlaceholder: 'Nhập mật khẩu',
      newPasswordPlaceholder: 'Tối thiểu 8 ký tự',
      confirmPassword: 'Nhập lại mật khẩu',
      confirmPasswordPlaceholder: 'Nhập lại mật khẩu',
      email: 'Email',
      emailPlaceholder: 'Nhập email của bạn',
      username: 'Tên tài khoản',
      usernamePlaceholder: 'Ví dụ: huy_legal',
      fullName: 'Họ và tên',
      fullNamePlaceholder: 'Nhập họ và tên',
      phone: 'Số điện thoại',
      phoneOptional: '(không bắt buộc)',
      phonePlaceholder: 'Ví dụ: 0901234567',
      rememberMe: 'Ghi nhớ đăng nhập',
      forgotPassword: 'Quên mật khẩu?',
      showPasswordAria: 'Hiện mật khẩu',
      hidePasswordAria: 'Ẩn mật khẩu',
      showConfirmPasswordAria: 'Hiện mật khẩu nhập lại',
      hideConfirmPasswordAria: 'Ẩn mật khẩu nhập lại',
    },

    // Split into fragments because t() returns strings, never JSX: the two
    // links are rendered by the component and joined around these pieces.
    terms: {
      prefix: 'Tôi đồng ý với ',
      termsLink: 'Điều khoản sử dụng',
      middle: ' và ',
      privacyLink: 'Chính sách bảo mật',
      suffix: '.',
    },

    validation: {
      identifierRequired: 'Vui lòng nhập tên tài khoản hoặc email.',
      passwordRequired: 'Vui lòng nhập mật khẩu.',
      emailInvalid: 'Vui lòng nhập email hợp lệ.',
      usernameInvalid: 'Tên tài khoản gồm 3–30 chữ thường, số hoặc dấu gạch dưới.',
      fullNameRequired: 'Vui lòng nhập họ và tên.',
      phoneInvalid: 'Số điện thoại chưa đúng định dạng.',
      passwordTooShort: 'Mật khẩu cần có ít nhất 8 ký tự.',
      confirmMismatch: 'Mật khẩu nhập lại chưa khớp.',
      termsRequired: 'Vui lòng đồng ý với Điều khoản sử dụng.',
      checkForm: 'Vui lòng kiểm tra lại thông tin đã nhập.',
    },
  },

  chat: {
    workspace: {
      toolsAria: 'Công cụ VieTaxLegal',
      toolLabel: 'Tra cứu pháp luật',
      loading: 'Đang tải cuộc trò chuyện…',
      emptyHeading: 'Bạn cần tra cứu vấn đề pháp luật nào?',
      emptyBody: 'Hãy mô tả tình huống và thông tin cần làm rõ để nhận câu trả lời phù hợp hơn.',
      composerPlaceholder: 'Nhập câu hỏi pháp luật của bạn…',
      composerAria: 'Câu hỏi của bạn',
      stop: 'Dừng trả lời',
      sendAria: 'Gửi câu hỏi',
      dismissErrorAria: 'Đóng thông báo lỗi',
      disclaimer:
        'Nội dung chỉ mang tính tham khảo. Hãy kiểm tra hiệu lực văn bản và tham vấn chuyên gia trước khi áp dụng.',
    },
    sidebar: {
      listAria: 'Danh sách cuộc hội thoại',
      brandSubtitle: 'Trợ lý tra cứu pháp luật',
      closeAria: 'Đóng danh sách cuộc hội thoại',
      openAria: 'Mở danh sách hội thoại',
      newChat: 'Cuộc trò chuyện mới',
      searchPlaceholder: 'Tìm kiếm hội thoại',
      loading: 'Đang tải lịch sử…',
      retry: 'Thử lại',
      noResults: 'Không tìm thấy hội thoại.',
      empty: 'Chưa có cuộc trò chuyện nào.',
      deleteAria: 'Xóa hội thoại {{title}}',
      confirmDelete: 'Xóa cuộc trò chuyện “{{title}}”?',
    },
    groups: {
      today: 'Hôm nay',
      yesterday: 'Hôm qua',
      last7Days: '7 ngày qua',
      older: 'Cũ hơn',
    },
    page: {
      titleBeta: 'Beta',
      title: 'Trợ lý AI VieTaxLegal',
      subtitle: 'Tra cứu thông tin pháp luật dành cho doanh nghiệp Việt Nam',
      accountFallback: 'Tài khoản',
      logout: 'Đăng xuất',
      historyLoadFailed: 'Không thể tải lịch sử trò chuyện.',
      conversationLoadFailed: 'Không thể tải cuộc trò chuyện.',
      deleteFailed: 'Không thể xóa cuộc trò chuyện.',
      sendFailed: 'Không thể nhận câu trả lời. Vui lòng thử lại.',
    },
    message: {
      justNow: 'Vừa xong',
      streamingAria: 'Trợ lý đang trả lời',
      failed: 'Phản hồi bị gián đoạn.',
      cancelled: 'Đã dừng trả lời.',
      copy: 'Sao chép',
      copied: 'Đã sao chép',
      copyAria: 'Sao chép câu trả lời',
      sources: 'Nguồn tham khảo',
    },
  },
}

export default vi
