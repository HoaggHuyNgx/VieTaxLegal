# VieTaxLegal - Frontend

React application for VieTaxLegal AI chatbot landing page.

## Tech Stack

- React 18
- Vite
- React Router DOM

## Setup

```bash
cd frontend
npm install
npm run dev
```

## Structure

```
src/
├── components/     # Reusable components
│   ├── Hero.jsx
│   ├── Features.jsx
│   ├── Process.jsx
│   ├── FAQ.jsx
│   └── Footer.jsx
├── pages/          # Page components
│   ├── LandingPage.jsx
│   └── ChatPage.jsx
├── styles/         # Global styles
└── App.jsx         # Main app component
```

## Available Routes

- `/` - Landing page
- `/chat` - Chat interface (coming soon)

## Development

- Dev server: `npm run dev` (http://localhost:3000)
- Build: `npm run build`
- Preview: `npm run preview`
