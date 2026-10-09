# student management system

A frontend for managing students in classes 1–12: list, search, filter by class, sort, view profiles, create, edit and delete records (with confirmation). Roll numbers are validated as unique within a class.

## Tech stack
React + TypeScript, Vite, Tailwind CSS, React Router, axios.

## Getting started
```
npm install --legacy-peer-deps
cp .env.example .env
npm run dev
```
Then open http://localhost:40361

## Environment variables
See .env.example. VITE_API_URL is optional — every entity runs on local
mock data (USE_MOCK = true in src/data/store.ts) until it's set and each
entity's flag is flipped to false.

## Project structure
- src/pages — Student list, detail, form and NotFound screens
- src/components — Sidebar, TopBar, StudentTable, ClassFilter, FormInput, ConfirmDialog
- src/data — mock data and the localStorage-backed, USE_MOCK-gated store
- src/api — shared axios client with toast error interceptor
- src/routes — router configuration
- src/constants — route paths and page size
- src/validation — shared field validators
- src/utils — date and initials helpers
- src/types — TypeScript types
