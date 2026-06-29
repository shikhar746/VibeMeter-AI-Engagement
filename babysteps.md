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