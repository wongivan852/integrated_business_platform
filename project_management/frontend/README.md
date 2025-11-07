
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

