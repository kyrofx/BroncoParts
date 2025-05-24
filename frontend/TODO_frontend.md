# Frontend Development TODO List

## Core Components & Pages

- [x] `Home.js`: Basic home/landing page.
- [x] `Login.js`: User login form and logic.
- [x] `Register.js`: User registration form and logic.
- [x] `Projects.js`: List all projects, link to create new project, link to project details.
- [x] `ProjectDetails.js`: Display details of a single project, link to its parts, edit/delete project.
- [x] `CreateProject.js`: Form to create a new project.
- [x] `Parts.js`: List all parts (potentially filterable), link to create new part, link to part details.
- [x] `PartDetails.js`: Display details of a single part, edit/delete part.
- [x] `CreatePart.js`: Form to create a new part (including parent assembly selection).

## Services / API Integration

- [x] `api.js` (or similar): Centralized Axios instance and API call functions (e.g., `fetchProjects`, `loginUser`).

## Authentication & State Management

- [x] Implement token storage (localStorage/sessionStorage) - Handled in AuthContext & Login.
- [x] Context API or Redux/Zustand for global state (user auth status, etc.) - Implemented with AuthContext.
- [x] Protected Routes (redirect if not authenticated) - Implemented with ProtectedRoute component.

## UI/UX Enhancements

- [x] Navigation bar improvements (e.g., conditional links based on auth status) - Basic implementation in App.js.
- [ ] Consistent styling and layout.
- [ ] Loading indicators.
- [ ] Error handling and display.
- [ ] Forms validation.

## Specific Feature Components (from NEW_README.md)

- [x] Dashboard view (`/dashboards`)
- [x] Project-specific dashboard (`/projects/:id/dashboard`)
- [x] Dashboard parts view (`/projects/:id/dashboard/parts`)
- [ ] Order Management (listing, creation, details - if in scope for this phase)

## Completed Tasks

- Initial `App.js` structure with basic routing.
- Basic `App.css` styling.
- `react-router-dom` and `axios` installed.
