# Deloitte VibeMeter
> **Agentic AI HR Middleware & Predictive Sentiment Pipeline**

Deloitte VibeMeter is an enterprise-grade AI-driven agentic middleware solution designed to close the loop between predictive employee analytics and organizational retention. Rather than relying on backward-looking, aggregate annual surveys, VibeMeter extracts fine-grained individual disengagement drivers from machine learning models via **SHAP (SHapley Additive exPlanations) values**, instantly instantiates an isolated **LangGraph agentic state machine**, and conducts contextualized, highly empathetic outreach dialogues over FastAPI.

---

## 🛠️ Tech Stack & Core Ecosystem
* **Frameworks:** FastAPI, LangGraph, LangChain Core
* **Core Model Engine:** Llama-3.3-70B-Versatile (Hosted on Groq Cloud Architecture)
* **Data Ingestion & Extraction:** Pandas, Regular Expression (`re`) Engine
* **Type Validation & Execution:** Pydantic v2, Standard Contextlib, Asyncio Threading Utilities

---

## 📁 Architecture & Codebase Blueprint
The repository features a highly modular layout optimized for asynchronous scalability and complete separation of concerns:
* `main.py`: The core ASGI application layer orchestration. Manages stateful server lifecycle routines, non-blocking ThreadPool threading abstractions for long-running synchronous inference operations, and hosts the endpoint schema layout.
* `agent.py`: Defines the internal topological design of the LangGraph execution layout. Dictates state types via `TypedDict` primitives, instantiates LLM hyperparameters, and specifies branching graph conditional paths.
* `question_bank.py`: Acts as the isolated structural configuration context mapping repository. Maps primary data-driven organizational features to personalized conversational hooks.
* `engagement_results.csv`: Localized tabular storage containing workforce historical records, downstream classification criteria flags (`is_selected`), and localized feature contribution strings.

---

## ⚙️ Detailed System Execution Flow
1. **Data Hydration:** Upon lifecycle startup, the pandas parser scans the workspace for `engagement_results.csv`, isolates rows where `is_selected == True`, and targets the employee's raw SHAP value attribution strings.
2. **Regex Parsing & Mapping:** A regular expression engine translates standard vector text mappings (`feature(impact_score)`) into native sorted float dictionaries based on absolute algorithmic impact: $I_{feat} = | \text{SHAP Value} |$.
3. **Context Hook Generation:** The maximum impact key maps directly to the targeted question matrix in `question_bank.py`, generating a natural, custom baseline interaction hook.
4. **Agent Processing Core:** Incoming multi-turn communication loops through LangGraph nodes, validating risk assessment before either formulating an empathetic response or issuing an automated escalation notice.

---

## 📡 API Specifications & REST Endpoints

### 1. Trigger Administrative Outreach
* **Endpoint:** `GET /trigger_outreach`
* Exposes all targeted cohorts flagged by predictive retention metrics for administrative tracking dashboard rendering.

### 2. Start Chat Session
* **Endpoint:** `POST /start_chat/{employee_id}`
* Generates an isolated in-memory conversational context array inside the active memory repository, drawing out the relevant primary text hook.

### 3. Stateful Converse Routing
* **Endpoint:** `POST /chat`
* Feeds user responses into the LangGraph state orchestration framework. Long-running API threads are processed over `run_in_threadpool` to bypass runtime event loop starvation.

### 4. Analytical Reporting Compilation
* **Endpoint:** `GET /generate_daily_report`
* Aggregates dialogue blocks across active threads, processes text context to yield individual mood evaluations via separate LLM prompts, generates action summaries, and preserves an audit log JSON file to disk (`hr_daily_report.json`).

---

## 💻 Setup & Local Installation

```bash
# 1. Clone your project structure and initialize virtual environment
python -m venv .venv
source .venv/bin/activate  # Or use .venv\Scripts\activate on Windows

# 2. Configure environment specifications
echo "GROQ_API_KEY=gsk_your_validated_secret_api_key_here" > .env

# 3. Spin up the ASGI server infrastructure locally using Uvicorn
uvicorn main:app --reload --port 8000

