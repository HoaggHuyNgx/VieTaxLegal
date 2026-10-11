// Mirror of vi.js. The structure must match key for key — catalog.test.js fails
// the build when the two drift apart.
const en = {
  common: {
    languageLabel: 'Language',
    localeVi: 'Vietnamese',
    localeEn: 'English',
    brandName: 'VieTaxLegal',
    pageTitle: 'VieTaxLegal - AI legal and tax assistant for Vietnamese businesses',
    pageDescription: 'VieTaxLegal — AI legal and tax assistant for Vietnamese businesses',
  },

  landing: {
    hero: {
      tagline: 'Legal research assistant for Vietnamese businesses',
      description:
        'Ask a question, watch the answer arrive live, and keep your history in a space that belongs to your account alone.',
      benefits: [
        { id: 'ask', text: 'Ask legal questions in Vietnamese.' },
        { id: 'live', text: 'Get answers streamed back in real time.' },
        { id: 'history', text: 'Save and revisit your history, per account.' },
        { id: 'privacy', text: 'Conversation data is reachable only through a protected backend.' },
        { id: 'simple', text: 'A simple interface built for first-pass research.' },
        { id: 'verify', text: 'Always reminds you to check a document is still in force.' },
      ],
    },

    features: {
      eyebrow: 'Why choose VieTaxLegal',
      heading: 'What VieTaxLegal does well',
      illustrationAlt: 'Legal research assistant',
      items: [
        {
          id: 'legalResearch',
          title: 'Legal Q&A in Vietnamese',
          description:
            'Describe your situation and get an answer that follows the thread of the conversation.',
        },
        {
          id: 'accountHistory',
          title: 'History scoped to your account',
          description: 'Each user can only view and delete their own conversations.',
        },
        {
          id: 'liveResponse',
          title: 'Live responses',
          description:
            'Text appears as the assistant writes it, instead of making you wait for the whole answer.',
        },
        {
          id: 'usageControl',
          title: 'Cost and abuse controls',
          description: 'Limits on message count and length protect both your account and the AI model quota.',
        },
        {
          id: 'ragReady',
          title: 'Ready for RAG',
          description:
            'The retrieval layer is already separated, so verified legal sources can be added later.',
        },
      ],
    },

    process: {
      eyebrow: 'How VieTaxLegal helps',
      heading: 'How it works',
      items: [
        {
          id: 'ask',
          title: 'Ask',
          description: 'Describe your legal question and the facts that matter to your situation.',
        },
        {
          id: 'analysis',
          title: 'Read the context',
          description: 'The assistant uses your question and recent history to understand the problem.',
        },
        {
          id: 'research',
          title: 'Answer live',
          description: 'The reply appears piece by piece while the model is still working.',
        },
        {
          id: 'verify',
          title: 'Verify before acting',
          description:
            'Check the current text of the law, or consult a professional for decisions that matter.',
        },
      ],
    },

    faq: {
      eyebrow: 'Frequently asked questions',
      items: [
        {
          id: 'trustworthy',
          question: 'Is VieTaxLegal reliable?',
          answer:
            'The Beta supports first-pass research with AI but has no RAG corpus of legal sources yet. Check that a document is still in force, or consult a professional, before you act on anything.',
        },
        {
          id: 'benefits',
          question: 'What does VieTaxLegal offer a business?',
          answer:
            'Less time spent searching, help spotting risks, and better-prepared information before you sit down with a professional.',
        },
        {
          id: 'contracts',
          question: 'Does VieTaxLegal analyse contracts?',
          answer: 'Not yet. Contract analysis is planned for a later stage and is not part of the Beta.',
        },
        {
          id: 'tax',
          question: 'Does VieTaxLegal handle tax questions?',
          answer:
            'The Beta has no dedicated tax calculator. Use the chat area for legal research at a reference level only.',
        },
        {
          id: 'lawyer',
          question: 'When should I still consult a lawyer?',
          answer:
            'When the amount at stake is large, when there is a dispute or high risk, or when you need a formal legal opinion.',
        },
        {
          id: 'english',
          question: 'Does VieTaxLegal support English?',
          answer:
            'The interface is available in both Vietnamese and English — switch with the VI/EN control. The assistant still answers in Vietnamese, because for Vietnamese legal documents only the Vietnamese text carries legal force.',
        },
        {
          id: 'security',
          question: 'Is my data secure?',
          answer:
            'The Beta does not support file uploads. Conversations are scoped per account and reachable only through the application backend.',
        },
        {
          id: 'audience',
          question: 'Who is VieTaxLegal for?',
          answer: 'SMEs, accountants, legal and compliance staff, tax advisers, and startups.',
        },
      ],
    },

    footer: {
      tagline: 'Legal research assistant for Vietnamese businesses',
      navAria: 'Footer navigation',
      backToTopAria: 'Back to top',
      emailLabel: 'Email: {{address}}',
      links: [
        { id: 'product', label: 'Product' },
        { id: 'features', label: 'Features' },
        { id: 'pricing', label: 'Pricing' },
        { id: 'contact', label: 'Contact' },
        { id: 'privacy', label: 'Privacy policy' },
      ],
    },
  },

  errors: {
    byCode: {
      REQUEST_FAILED: 'Could not reach the server. Please try again.',
      INVALID_RESPONSE: 'The server returned invalid data.',
      INVALID_STREAM_EVENT: 'Could not read the live response from the server.',
      EMPTY_STREAM: 'The server returned no response content.',
      TRUNCATED_STREAM: 'The response was cut off before it finished.',
      UNAUTHENTICATED: 'Your session is invalid or has expired.',
      INVALID_CREDENTIALS: 'That email/username or password is incorrect.',
      EMAIL_TAKEN: 'That email is already in use.',
      USERNAME_TAKEN: 'That username is already taken.',
      REGISTRATION_CONFLICT: 'Could not create the account. Please try again.',
      VALIDATION_ERROR: 'Some of the submitted data is not valid.',
      CONVERSATION_NOT_FOUND: 'Conversation not found.',
      CHAT_RATE_LIMITED: 'You are sending questions too quickly. Please try again in a few minutes.',
      CHAT_DAILY_LIMIT_REACHED: 'You have used all of today’s messages. Please come back tomorrow.',
      CHAT_IN_PROGRESS: {
        general: 'This conversation already has an answer in progress.',
        delete: 'Stop the current answer before deleting this conversation.',
      },
      CHAT_NOT_CONFIGURED: 'The chat service is not configured. Please contact an administrator.',
      CHAT_PROVIDER_UNAVAILABLE: 'The answering service is temporarily unavailable. Please try again later.',
    },
  },

  auth: {
    cardAria: 'Sign in or create an account',
    tablistAria: 'Account access',
    tabLogin: 'Sign in',
    tabRegister: 'Sign up',
    loginHeading: 'Welcome back!',
    loginSubtitle: 'Sign in to continue using VieTaxLegal',
    registerHeading: 'Create an account',
    registerSubtitle: 'Create an account to start using VieTaxLegal',
    submitting: 'Working…',
    submitLogin: 'Sign in',
    submitRegister: 'Create account',
    divider: 'or',
    googleLogin: 'Continue with Google',
    googleRegister: 'Sign up with Google',
    forgotPasswordNotice: 'Password recovery is coming in a future release.',
    googleNotice: 'Google sign-in is not supported in this release.',
    checkingSession: 'Checking your session…',

    fields: {
      identifier: 'Username or email',
      identifierPlaceholder: 'Enter your username or email',
      password: 'Password',
      passwordPlaceholder: 'Enter your password',
      newPasswordPlaceholder: 'At least 8 characters',
      confirmPassword: 'Confirm password',
      confirmPasswordPlaceholder: 'Re-enter your password',
      email: 'Email',
      emailPlaceholder: 'Enter your email',
      username: 'Username',
      usernamePlaceholder: 'For example: huy_legal',
      fullName: 'Full name',
      fullNamePlaceholder: 'Enter your full name',
      phone: 'Phone number',
      phoneOptional: '(optional)',
      phonePlaceholder: 'For example: 0901234567',
      rememberMe: 'Remember me',
      forgotPassword: 'Forgot password?',
      showPasswordAria: 'Show password',
      hidePasswordAria: 'Hide password',
      showConfirmPasswordAria: 'Show confirmation password',
      hideConfirmPasswordAria: 'Hide confirmation password',
    },

    terms: {
      prefix: 'I agree to the ',
      termsLink: 'Terms of Use',
      middle: ' and the ',
      privacyLink: 'Privacy Policy',
      suffix: '.',
    },

    validation: {
      identifierRequired: 'Please enter your username or email.',
      passwordRequired: 'Please enter your password.',
      emailInvalid: 'Please enter a valid email address.',
      usernameInvalid: 'Username must be 3–30 lowercase letters, digits or underscores.',
      fullNameRequired: 'Please enter your full name.',
      phoneInvalid: 'That phone number format is not valid.',
      passwordTooShort: 'Password must be at least 8 characters.',
      confirmMismatch: 'The two passwords do not match.',
      termsRequired: 'Please accept the Terms of Use.',
      checkForm: 'Please check the information you entered.',
    },
  },

  chat: {
    workspace: {
      toolsAria: 'VieTaxLegal tools',
      toolLabel: 'Legal research',
      toolTax: 'Tax calculator',
      toolScan: 'Contract scan',
      comingSoon: 'Coming soon',
      comingSoonAria: '{{name}} — coming soon',
      attachFile: 'Attach file',
      attachDocument: 'Pick a reference document',
      suggestionAria: 'Use suggested question: {{question}}',
      loading: 'Loading conversation…',
      emptyHeading: 'What legal question can I look up for you?',
      emptyBody: 'Describe the situation and what you need clarified so the answer fits your case.',
      composerPlaceholder: 'Type your legal question…',
      composerAria: 'Your question',
      stop: 'Stop',
      sendAria: 'Send question',
      dismissErrorAria: 'Dismiss error',
      disclaimer:
        'For reference only. Check that the document is still in force and consult a professional before acting on it.',
    },
    sidebar: {
      listAria: 'Conversation list',
      brandSubtitle: 'Legal research assistant',
      closeAria: 'Close conversation list',
      openAria: 'Open conversation list',
      newChat: 'New chat',
      searchPlaceholder: 'Search conversations',
      searchShortcutAria: 'Press Ctrl + K to search',
      conversationsLabel: 'Conversations',
      sortAria: 'Change conversation order',
      sortNewest: 'Newest first',
      sortOldest: 'Oldest first',
      loading: 'Loading history…',
      retry: 'Try again',
      noResults: 'No conversations found.',
      empty: 'No conversations yet',
      emptyBody: 'Start a new conversation to get help from VieTaxLegal AI.',
      deleteAria: 'Delete conversation {{title}}',
      confirmDelete: 'Delete the conversation “{{title}}”?',
    },
    groups: {
      today: 'Today',
      yesterday: 'Yesterday',
      last7Days: 'Previous 7 days',
      older: 'Older',
    },
    page: {
      titleBeta: 'Beta',
      title: 'VieTaxLegal AI assistant',
      subtitle: 'Legal research for Vietnamese businesses',
      accountFallback: 'Account',
      logout: 'Sign out',
      historyLoadFailed: 'Could not load your chat history.',
      conversationLoadFailed: 'Could not load the conversation.',
      deleteFailed: 'Could not delete the conversation.',
      sendFailed: 'Could not get an answer. Please try again.',
    },
    message: {
      justNow: 'Just now',
      streamingAria: 'Assistant is replying',
      failed: 'The response was interrupted.',
      cancelled: 'Response stopped.',
      copy: 'Copy',
      copied: 'Copied',
      copyAria: 'Copy answer',
      sources: 'Sources',
    },
    sources: {
      title: 'Reference sources',
      subtitle: 'Legal documents that may relate to your question.',
      emptyTitle: 'No sources yet',
      emptyBody:
        'The assistant has not cited any document for this answer. Sources are only shown for answers received in the current session.',
      pending: 'Waiting for sources for this answer…',
      showAll: 'View all sources ({{count}})',
      showLess: 'Show less',
      collapseAria: 'Collapse the sources panel',
      expandAria: 'Expand the sources panel',
      openSourceAria: 'Open source {{title}}',
    },
  },
}

export default en
