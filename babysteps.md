1. Database Integration (MongoDB)

Replace all in-memory Python dictionaries with MongoDB collections.

Create an employees collection to store employee IDs, SHAP values, and engagement data.

Create a conversations collection to persist LangGraph chat states and message histories. Read and write directly to the database without worrying about concurrent locking.

2. Employee Access & Validation

Implement a simple login/entry screen for employees on the frontend.

The system must validate that the entered roll number strictly follows the format EMPXXXX (where X is a digit, e.g., EMP1234). Use regex (e.g., ^EMP\d+$) on both the frontend input and backend route validation.

If the ID is valid, fetch their specific state from the database and initialize/resume the chat.

3. HR Panel & Dashboard

Create a separate HR login route (e.g., /hr/login). For this milestone, use a simple static password check against an environment variable. No complex auth.

Build a React view for the HR Dashboard.

The dashboard must fetch data from the MongoDB backend and display a data table containing all employees who have interacted with the bot.

The table columns should include: Employee ID, Top SHAP Feature (Primary Issue), Chat Status, and a highlighted column showing specific "Issues Raised" (synthesized by the LLM during the chat).

Implementation Rules (Strict):
Do not write all the code at once. We are going to build this incrementally to ensure everything remains stable.

First, output the complete, updated Directory / File Structure for both the frontend and backend.

Second, break the entire implementation into a numbered list of "Baby Steps" (e.g., Step 1: MongoDB Setup, Step 2: Employee Login Route, etc.).

Wait for my approval on the plan. Once I say "proceed," give me the code for Step 1 ONLY. Do not move to the next step until I confirm Step 1 works.


2. Baby Steps Roadmap
Step 1 — MongoDB Setup

Add database.py, install motor (async Mongo driver) + pymongo, define connection logic, wire into main.py lifespan (connect on startup, close on shutdown), confirm a test ping works. No collections/schemas yet — just plumbing.

Step 2 — Pydantic Schemas & Collection Design

Add models/schemas.py: Employee, ConversationState, EmployeeLoginRequest, HrLoginRequest, ChatRequest/ChatResponse, etc. Define the exact shape of the employees and conversations collections (fields, indexes — e.g. unique index on employee_id).
Step 3 — Migrate Engagement Data Load (CSV → MongoDB)

One-time/startup seed script (or lifespan step) that reads engagement_results.csv and upserts rows into the employees collection, replacing cached_engagement_data. Add a small idempotent seeding guard so re-running doesn't duplicate.
Step 4 — Employee Auth Route (EMPXXXX validation)

Add auth_utils.py regex validator + routers/auth.py → POST /auth/employee/login. Looks up employee in DB, returns a minimal session payload (e.g. signed token or simple session id) frontend can hold onto. No JWT complexity yet unless you want it — can start with a simple opaque token stored server-side, upgrade later.
Step 5 — Migrate Chat Logic to MongoDB (conversations collection)

Rewrite agent.py + routers/chat.py so ChatState is loaded from/saved to conversations instead of the active_chats dict. This is the biggest step — LangGraph nodes stay the same logically, just the persistence layer changes.
Step 6 — HR Auth Route (static password via env)

Add POST /auth/hr/login in routers/auth.py, checks against HR_PASSWORD env var, issues an HR-scoped session/token. Add require_hr_auth dependency for protecting future routes.
Step 7 — HR Dashboard API

Add routers/dashboard.py → GET /dashboard/employees, protected by require_hr_auth. Aggregates data from employees + conversations collections into the table shape: Employee ID, Top SHAP Feature, Chat Status, Issues Raised (LLM-synthesized summary, pulled from conversations.vibe_summary or similar field — may need to also persist that per-conversation rather than only in the on-demand report).
Step 8 — Frontend: Routing & Auth Context

Add react-router-dom, set up App.jsx routes, build AuthContext.jsx, wire services/api.js.
Step 9 — Frontend: Employee Login Screen

Build EmployeeLogin.jsx with EMPXXXX regex validation client-side, calls Step 4's endpoint, redirects into ChatInterface on success.
Step 10 — Frontend: HR Login + Protected Dashboard Route

Build HrLogin.jsx, ProtectedRoute.jsx, wire /hr/login → /hr/dashboard flow.
Step 11 — Frontend: HR Dashboard Table

Build HrDashboard.jsx consuming Step 7's endpoint, render the table with the four required columns, highlight "Issues Raised."
Step 12 — Integration Pass & Cleanup

Remove dead code (active_chats, cached_engagement_data dicts), update readme.md and requirements.txt, sanity-check full flow end-to-end (employee chat → escalation → HR sees it on dashboard).