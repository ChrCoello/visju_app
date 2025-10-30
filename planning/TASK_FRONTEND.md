# Frontend Refactoring: Static HTML to React

This document outlines the tasks required to refactor the frontend from a static HTML/CSS/JS application to a modern React application.

## 1. Project Setup

-   [ ] **Initialize React Project:** Set up a new React project using a modern build tool like Vite or Create React App.
    -   `npm create vite@latest frontend-react -- --template react-ts`
-   [ ] **Install Dependencies:**
    -   [ ] `react-router-dom` for routing.
    -   [ ] `axios` or `fetch` for API communication.
    -   [ ] A UI library like Material-UI or Chakra UI for a consistent look and feel.
    -   [ ] State management library if needed (e.g., Redux Toolkit, Zustand).
-   [ ] **Project Structure:** Define a clear and scalable project structure for components, pages, services, etc.

## 2. Component Development

-   [ ] **Create Layout Component:** Develop a `Layout` component to replace `base.html`, including the header, footer, and navigation.
-   [ ] **Create Page Components:**
    -   [ ] `HomePage.tsx` (replaces `index.html`)
    -   [ ] `SessionsPage.tsx` (replaces `sessions.html`)
    -   [ ] `SessionDetailPage.tsx` (replaces `session_detail.html`)
-   [ ] **Create Reusable Components:**
    -   [ ] `SessionList.tsx`
    -   [ ] `SessionListItem.tsx`
    -   [ ] `TranscriptionViewer.tsx`
    -   [ ] `AudioPlayer.tsx`

## 3. Routing

-   [ ] **Configure Router:** Set up `react-router-dom` to handle navigation between the pages.
    -   `/` -> `HomePage`
    -   `/sessions` -> `SessionsPage`
    -   `/sessions/:id` -> `SessionDetailPage`

## 4. API Integration

-   [ ] **Create API Service:** Implement a service to handle all communication with the backend API.
    -   `getSessions()`
    -   `getSession(id)`
    -   `getTranscription(id)`
-   [ ] **Integrate API calls:** Use the API service in the components to fetch and display data.

## 5. Styling

-   [ ] **Choose a Styling Solution:** Decide on a styling approach (e.g., CSS Modules, Styled Components, Tailwind CSS).
-   [ ] **Migrate Styles:** Migrate the existing styles from `style.css` to the new styling solution.
-   [ ] **Ensure Responsiveness:** Make sure the new UI is responsive and works well on different screen sizes.

## 6. State Management

-   [ ] **Identify State Needs:** Determine what application state needs to be managed (e.g., sessions list, current session, user info).
-   [ ] **Implement State Management:** Use `useState`, `useContext`, or a dedicated library to manage the application state.

## 7. Build and Deployment

-   [ ] **Configure Build Process:** Set up the build process to generate optimized static assets.
-   [ ] **Integrate with Backend:**
    -   Option 1: Serve the React app from the FastAPI backend.
    -   Option 2: Deploy the React app separately (e.g., on Netlify, Vercel) and configure CORS on the backend.
-   [ ] **Update Documentation:** Update the `README.md` with instructions on how to build and run the new frontend.

## 8. Cleanup

-   [ ] **Remove Old Frontend:** Once the new React frontend is complete and tested, remove the old `frontend/static` and `frontend/templates` directories.
