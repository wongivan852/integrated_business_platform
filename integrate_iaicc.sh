#!/bin/bash

# IAICC 2025 TSX Integration Script

# Integrates project plan and procurement components into project_management app

 

set -e

 

echo "╔═══════════════════════════════════════════════════════════╗"

echo "║   IAICC 2025 Project Management Integration Script        ║"

echo "╚═══════════════════════════════════════════════════════════╝"

echo ""

 

# Define paths

PROJECT_ROOT="$HOME/Desktop/integrated_business_platform"

PM_DIR="$PROJECT_ROOT/project_management"

DOWNLOADS="$HOME/Downloads"

FRONTEND_DIR="$PM_DIR/frontend"

 

cd "$PROJECT_ROOT"

 

echo "📁 Step 1: Creating frontend directory structure..."

mkdir -p "$FRONTEND_DIR/src/components"

mkdir -p "$FRONTEND_DIR/src/pages"

mkdir -p "$FRONTEND_DIR/src/assets"

mkdir -p "$FRONTEND_DIR/public"

echo "✅ Created directory structure"

echo ""

 

echo "📋 Step 2: Copying TSX files from Downloads..."

if [ -f "$DOWNLOADS/iaicc-2025-project-plan.tsx" ]; then

    cp "$DOWNLOADS/iaicc-2025-project-plan.tsx" "$FRONTEND_DIR/src/pages/"

    echo "✅ Copied iaicc-2025-project-plan.tsx"

else

    echo "❌ iaicc-2025-project-plan.tsx not found!"

fi

 

if [ -f "$DOWNLOADS/iaicc-procurement-list.tsx" ]; then

    cp "$DOWNLOADS/iaicc-procurement-list.tsx" "$FRONTEND_DIR/src/components/"

    echo "✅ Copied iaicc-procurement-list.tsx"

else

    echo "❌ iaicc-procurement-list.tsx not found!"

fi

echo ""

 

echo "📦 Step 3: Creating package.json..."

cat > "$FRONTEND_DIR/package.json" << 'PACKAGE_EOF'

{

  "name": "iaicc-project-management-frontend",

  "version": "1.0.0",

  "description": "IAICC 2025 Conference Project Management - Frontend",

  "private": true,

  "type": "module",

  "scripts": {

    "dev": "vite",

    "build": "tsc && vite build",

    "preview": "vite preview",

    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"

  },

  "dependencies": {

    "react": "^18.2.0",

    "react-dom": "^18.2.0",

    "react-router-dom": "^6.20.0",

    "lucide-react": "^0.292.0",

    "axios": "^1.6.2"

  },

  "devDependencies": {

    "@types/react": "^18.2.37",

    "@types/react-dom": "^18.2.15",

    "@vitejs/plugin-react": "^4.2.0",

    "typescript": "^5.3.2",

    "vite": "^5.0.2",

    "tailwindcss": "^3.3.5",

    "postcss": "^8.4.32",

    "autoprefixer": "^10.4.16"

  }

}

PACKAGE_EOF

echo "✅ Created package.json"

echo ""

 

echo "⚙️  Step 4: Creating Vite configuration..."

cat > "$FRONTEND_DIR/vite.config.ts" << 'VITE_EOF'

import { defineConfig } from 'vite'

import react from '@vitejs/plugin-react'

 

export default defineConfig({

  plugins: [react()],

  server: {

    port: 3000,

    proxy: {

      '/api': {

        target: 'http://localhost:8000',

        changeOrigin: true,

        rewrite: (path) => path.replace(/^\/api/, '')

      }

    }

  },

  build: {

    outDir: '../static/project_management/frontend',

    emptyOutDir: true

  }

})

VITE_EOF

echo "✅ Created vite.config.ts"

echo ""

 

echo "📝 Step 5: Creating TypeScript configuration..."

cat > "$FRONTEND_DIR/tsconfig.json" << 'TSCONFIG_EOF'

{

  "compilerOptions": {

    "target": "ES2020",

    "useDefineForClassFields": true,

    "lib": ["ES2020", "DOM", "DOM.Iterable"],

    "module": "ESNext",

    "skipLibCheck": true,

    "moduleResolution": "bundler",

    "allowImportingTsExtensions": true,

    "resolveJsonModule": true,

    "isolatedModules": true,

    "noEmit": true,

    "jsx": "react-jsx",

    "strict": true,

    "noUnusedLocals": true,

    "noUnusedParameters": true,

    "noFallthroughCasesInSwitch": true

  },

  "include": ["src"],

  "references": [{ "path": "./tsconfig.node.json" }]

}

TSCONFIG_EOF

 

cat > "$FRONTEND_DIR/tsconfig.node.json" << 'TSCONFIG_NODE_EOF'

{

  "compilerOptions": {

    "composite": true,

    "skipLibCheck": true,

    "module": "ESNext",

    "moduleResolution": "bundler",

    "allowSyntheticDefaultImports": true

  },

  "include": ["vite.config.ts"]

}

TSCONFIG_NODE_EOF

echo "✅ Created TypeScript configurations"

echo ""

 

echo "🎨 Step 6: Setting up Tailwind CSS..."

cat > "$FRONTEND_DIR/tailwind.config.js" << 'TAILWIND_EOF'

/** @type {import('tailwindcss').Config} */

export default {

  content: [

    "./index.html",

    "./src/**/*.{js,ts,jsx,tsx}",

  ],

  theme: {

    extend: {},

  },

  plugins: [],

}

TAILWIND_EOF

 

cat > "$FRONTEND_DIR/postcss.config.js" << 'POSTCSS_EOF'

export default {

  plugins: {

    tailwindcss: {},

    autoprefixer: {},

  },

}

POSTCSS_EOF

echo "✅ Created Tailwind CSS configuration"

echo ""

 

echo "📄 Step 7: Creating main HTML file..."

cat > "$FRONTEND_DIR/index.html" << 'HTML_EOF'

<!doctype html>

<html lang="en">

  <head>

    <meta charset="UTF-8" />

    <link rel="icon" type="image/svg+xml" href="/vite.svg" />

    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <title>IAICC 2025 Project Management</title>

  </head>

  <body>

    <div id="root"></div>

    <script type="module" src="/src/main.tsx"></script>

  </body>

</html>

HTML_EOF

echo "✅ Created index.html"

echo ""

 

echo "🎨 Step 8: Creating global styles..."

cat > "$FRONTEND_DIR/src/index.css" << 'CSS_EOF'

@tailwind base;

@tailwind components;

@tailwind utilities;

 

* {

  margin: 0;

  padding: 0;

  box-sizing: border-box;

}

 

body {

  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',

    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',

    sans-serif;

  -webkit-font-smoothing: antialiased;

  -moz-osx-font-smoothing: grayscale;

  background-color: #f9fafb;

}

 

code {

  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',

    monospace;

}

 

#root {

  min-height: 100vh;

}

CSS_EOF

echo "✅ Created global CSS"

echo ""

 

echo "⚛️  Step 9: Creating React App component..."

cat > "$FRONTEND_DIR/src/App.tsx" << 'APP_EOF'

import React from 'react';

import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

import IAICCProjectPlan from './pages/iaicc-2025-project-plan';

import { Calendar, Home } from 'lucide-react';

 

function App() {

  return (

    <Router>

      <div className="min-h-screen bg-gray-50">

        <nav className="bg-white shadow-md sticky top-0 z-50">

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

            <div className="flex justify-between items-center h-16">

              <div className="flex items-center">

                <Link to="/" className="flex items-center space-x-2 text-xl font-bold text-blue-600 hover:text-blue-700">

                  <Calendar className="h-6 w-6" />

                  <span>IAICC 2025 Project Management</span>

                </Link>

              </div>

              <div className="flex items-center space-x-4">

                <Link

                  to="/"

                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-100"

                >

                  <Home className="h-4 w-4" />

                  <span>Dashboard</span>

                </Link>

              </div>

            </div>

          </div>

        </nav>

 

        <main>

          <Routes>

            <Route path="/" element={<IAICCProjectPlan />} />

            <Route path="/project" element={<IAICCProjectPlan />} />

          </Routes>

        </main>

      </div>

    </Router>

  );

}

 

export default App;

APP_EOF

echo "✅ Created App.tsx"

echo ""

 

echo "🚀 Step 10: Creating main entry point..."

cat > "$FRONTEND_DIR/src/main.tsx" << 'MAIN_EOF'

import React from 'react';

import ReactDOM from 'react-dom/client';

import App from './App';

import './index.css';

 

ReactDOM.createRoot(document.getElementById('root')!).render(

  <React.StrictMode>

    <App />

  </React.StrictMode>,

);

MAIN_EOF

echo "✅ Created main.tsx"

echo ""

 

echo "📖 Step 11: Creating README..."

cat > "$FRONTEND_DIR/README.md" << 'README_EOF'

# IAICC 2025 Project Management Frontend

 

React + TypeScript + Vite frontend for IAICC 2025 Conference project management.

 

## Components

 

- **iaicc-2025-project-plan.tsx**: Main project plan with Gantt chart, WBS, deliverables, milestones, financial management, risk management, quality control, and resource management

- **iaicc-procurement-list.tsx**: Procurement tracking component

 

## Installation

 

```bash

cd project_management/frontend

npm install

```

 

## Development

 

```bash

# Start development server (runs on http://localhost:3000)

npm run dev

```

 

## Build for Production

 

```bash

# Build for Django integration

npm run build

```

 

This will output files to `../static/project_management/frontend/`

 

## Django Integration

 

The built files will be served by Django from the static directory.

 

Access the app at: http://localhost:8000/project-management/

 

## Features

 

- **Gantt Chart**: Visual project timeline

- **WBS**: Work Breakdown Structure

- **Deliverables**: Track project deliverables

- **Milestones**: Key project milestones

- **Financial Management**: Budget tracking

- **Risk Management**: Risk assessment and mitigation

- **Quality Management**: Quality control processes

- **Resource Management**: Team and resource allocation

- **Procurement**: Procurement item tracking

 

## Tech Stack

 

- React 18

- TypeScript

- Vite

- Tailwind CSS

- Lucide React (icons)

- React Router

README_EOF

echo "✅ Created README.md"

echo ""

 

echo "✅ Step 12: Creating .gitignore..."

cat > "$FRONTEND_DIR/.gitignore" << 'GITIGNORE_EOF'

# Logs

logs

*.log

npm-debug.log*

yarn-debug.log*

yarn-error.log*

pnpm-debug.log*

lerna-debug.log*

 

node_modules

dist

dist-ssr

*.local

 

# Editor directories and files

.vscode/*

!.vscode/extensions.json

.idea

.DS_Store

*.suo

*.ntvs*

*.njsproj

*.sln

*.sw?

GITIGNORE_EOF

echo "✅ Created .gitignore"

echo ""

 

echo "╔═══════════════════════════════════════════════════════════╗"

echo "║              Integration Complete! 🎉                     ║"

echo "╚═══════════════════════════════════════════════════════════╝"

echo ""

echo "📍 Frontend Location: $FRONTEND_DIR"

echo ""

echo "📝 Next Steps:"

echo ""

echo "1. Install dependencies:"

echo "   cd $FRONTEND_DIR"

echo "   npm install"

echo ""

echo "2. Start development server:"

echo "   npm run dev"

echo "   → Opens at http://localhost:3000"

echo ""

echo "3. Build for production:"

echo "   npm run build"

echo "   → Outputs to project_management/static/"

echo ""

echo "4. Your Django backend is running on:"

echo "   http://192.168.0.104:8000"

echo ""

echo "🔗 The React frontend will proxy API calls to Django backend"

echo ""

echo "✅ Files created:"

echo "   - package.json (dependencies)"

echo "   - vite.config.ts (build configuration)"

echo "   - tsconfig.json (TypeScript config)"

echo "   - tailwind.config.js (Tailwind CSS)"

echo "   - src/App.tsx (main app)"

echo "   - src/main.tsx (entry point)"

echo "   - src/index.css (global styles)"

echo "   - src/pages/iaicc-2025-project-plan.tsx"

echo "   - src/components/iaicc-procurement-list.tsx"

echo ""

echo "🚀 Happy coding!"

 