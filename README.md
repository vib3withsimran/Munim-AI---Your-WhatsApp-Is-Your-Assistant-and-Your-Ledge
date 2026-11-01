# Munim AI 🧾🤖

> **Your WhatsApp is your Assistant, your Cashier, and your Khata.**  
> Munim AI turns an Indian small seller's existing WhatsApp into an automated AI business operations system: it answers customer inquiries, takes orders, matches UPI payment screenshots, recalls past customer purchases via long-term memory, and maintains a self-updating ledger in Supabase — with zero new apps for buyers or sellers to learn.

---

## 🌟 Key Highlights

- 💬 **Multilingual & Hinglish First**: Speaks natural Hindi, Hinglish, and English buyer chats (*"2 anarkali kurti pack kar do XXL size mein"*).
- 🎙️ **Voice Note to Ledger**: Native multimodal audio understanding transcribes spoken Hindi/English voice notes and extracts order items in one shot.
- 📸 **UPI Screenshot & Handwritten OCR**: Automatically detects PhonePe, Google Pay, and Paytm receipts, extracts the 12-digit UTR and ₹ amount, and deciphers paper order lists.
- ⚡ **Sub-5ms Fast-Path & Sub-1s Inference**: In-memory zero-latency routing for pure greetings (*"hi"*, *"kaise ho"*, *"namaste"*, *"hi am i talking to munim ai"*) and ultra-fast Groq LPU inference for business messages.
- 🧠 **Autonomous Multi-Agent Architecture**: Dedicated deterministic agents for **Customer Relations**, **Order & Inventory Management**, and **Finance/Ledger Reconciliation** guarded by deterministic Rule Zero.
- 💾 **Meko Long-Term Memory (4 Datapacks)**: Integrates persistent customer preferences, repeat order intelligence, financial patterns, and build specs across 4 isolated datapacks with non-blocking background writes and a 120-second TTL cache.
- 📦 **Durable Async Queue & Outbound Worker**: SQLite-backed durable message queue with exponential backoff retries, dead-letter tracking, and an asynchronous worker process for heavy tasks, digest summaries, and Twilio REST notifications.
- 🔒 **Privacy & DPDP Compliance**: Built-in deterministic `#private` and `#resume` switches allow sellers and customers to opt out of AI processing instantly.
- 📊 **PostgreSQL & Row-Level Security**: Production-grade Supabase database architecture with tenant-isolated seller stores and JWT authentication.
- 📱 **Pixel-Accurate Seller Dashboard**: Modern Next.js 16 + React 19 + Tailwind CSS dark-green dashboard for desktop (`/dashboard`) and mobile (`/mobile`).

---

## 🏛️ System Architecture

```
                                      [ Customer / Buyer on WhatsApp ]
                                                     │
                                                     ▼
                                         [ Twilio WhatsApp Gateway ]
                                                     │
                                                     ▼ (HTTP POST)
                                       [ FastAPI Webhook Engine ]
                                                     │
                        ┌────────────────────────────┴──────────────────────────┐
                        ▼                                                       ▼
            [ Instant Greeting Fast-Path ]                         [ Multimodal AI Pipeline ]
           (zero-intent greetings: < 5ms)                         ├── Text: Groq (qwen/qwen3.8-27b)
                                                                  ├── Audio: Gemini Multimodal Audio
                                                                  └── Images: Gemini Vision (UPI OCR)
                                                                                │
                                                                                ▼
                                                                    [ Normalized Schema ]
                                                                     (ExtractedMessage)
                                                                                │
                                                                                ▼
                                                                      [ Orchestrator ]
                         ┌──────────────────────────────────────────────────────┼──────────────────────────────────────┐
                         ▼                                                      ▼                                      ▼
               [ Customer Agent ]                                       [ Order Agent ]                        [ Finance Agent ]
       • Product catalog search                                 • Deterministic inventory check        • Match UTR & amount to orders
       • Size, price & availability                             • Atomic stock reservation             • Create 'pending_verification' claim
       • Store policies & escalation                            • Subtotal & total math in Python      • Calculate outstanding dues
       • Meko customer preferences recall                       • Meko repeat order intelligence       • Daily sales & hisaab summary
                         │                                                      │                                      │
                         └───────────────────────────────────┬──────────────────┴──────────────────────────────────────┘
                                                             │
                              ┌──────────────────────────────┴──────────────────────────────┐
                              ▼                                                             ▼
                [ Supabase PostgreSQL + RLS ]                              [ Meko Long-Term Memory ]
               (profiles, customers, products,                             ├── munim-customer (preferences)
                 orders, order_items, payments)                            ├── munim-orders (re-order context)
                              │                                            ├── munim-finance (payment patterns)
                              │                                            └── munim-build (system specs)
                              ▼                                                             ▲
                    [ Next.js Dashboard ]                                                   │
                    (Desktop & Mobile UI)                                  [ Async Queue & Worker ]
                                                                           (SQLite Durable Queue, Twilio REST,
                                                                            daily digests & retry mechanism)
```

---

## 🤖 Multi-Agent Architecture & Deterministic Rules

### 1. The Orchestrator (`backend/app/agents/orchestrator.py`)
Evaluates deterministic business rules **before** routing messages to specialized agents:

| Command / Trigger | Action Taken |
| :--- | :--- |
| **`#private`** | **Activates Privacy Mode**: Pauses automated AI processing, ledger writes, and memory storage for that specific customer number. Replies confirming that assistant is paused. |
| **`#resume`** | **Deactivates Privacy Mode**: Resumes automated assistant replies and ledger tracking for that customer. |
| **`#confirm`** | **Owner Approval**: Confirms and commits a pending low-confidence order or payment claim into the verified business ledger. |
| **`#reject`** | **Owner Rejection**: Discards or declines an uncertain transaction or complaint. |
| **`summary` / `dues` / `hisaab`** | **Financial Snapshot**: Generates an instant owner report on WhatsApp showing today's verified collections, pending claims, and total outstanding dues. |

---

### 2. Customer Agent (`backend/app/agents/customer_agent.py`)
*The Conversation & Store Policy Specialist.*
- **Catalog Inquiries**: Searches the seller's active product catalog by keyword, size, or color and replies with item descriptions and prices.
- **Preference Recall**: Recalls past preferences (e.g., preferred kurti size, favorite colors) via Meko memory.
- **Delivery & Tracking**: Fetches existing customer orders from Supabase and gives current parcel status.
- **Store Policies**: Explains standard business policies (e.g., 7-day exchange tag policy, all-India delivery timelines, return guidelines).
- **Escalation Policy**:
  > **If `confidence.overall < 0.70` OR message is a `complaint`:**  
  > The agent **does not guess or hallucinate store policies**. It immediately:
  > 1. Sets `escalate: True` and generates an owner alert with the reason.
  > 2. Sends a reassuring reply to the customer:  
  >    *"Humein khed hai ki aapko pareshani hui. Maine store owner ko ye message notify kar diya hai. Vo personally aapse jaldi contact karenge."*

---

### 3. Order Agent (`backend/app/agents/order_agent.py`)
*The Order & Inventory Operations Specialist.*
- **Repeat Order Intelligence**: Recognizes repeat queries (*"Pehle jo order kara tha wahi wapas karna hai"*), recalls the previous item, size, and quantity from Meko memory, and prepares the re-order automatically.
- **Strict Deterministic Arithmetic**: Prices, line totals, and order subtotals are calculated **strictly in Python**. LLMs are never allowed to perform financial arithmetic or guess prices.
- **Stock Availability Verification**: Queries catalog stock prior to order booking. If stock is insufficient, alerts the buyer (e.g., *"Sirf 2 available hai, aapne 5 maanga hai"*) and suggests available alternatives.
- **Atomic Stock Reservation**: Creates order header (`pending_payment`), inserts order items, and reserves inventory atomically.
- **Itemized Bill**: Formats an itemized bill with order ID (e.g., `ORD-A4B1C2`), total amount, and delivery address prompt.

---

### 4. Finance Agent (`backend/app/agents/finance_agent.py`)
*The Payment & Ledger Specialist.*
- **Screenshot Claim Generation**: Extracts the 12-digit UTR/UPI reference ID and ₹ amount from payment receipts.
- **Pending Order Reconciliation**: Matches payment claims to the customer's oldest open order.
- **Anti-Fraud Security Principle**: Payment receipts are **never automatically marked as verified cash**. They are stored as `status = "pending_verification"` until the seller confirms bank settlement on the dashboard.
- **Outstanding Dues Calculation**: Deterministically calculates:
  $$\text{Outstanding Dues} = \sum (\text{Non-Cancelled Orders}) - \sum (\text{Verified Payments})$$

---

## ⚡ Latency & Speed Optimizations

To comfortably beat Twilio's **15-second webhook timeout window**, Munim AI uses a 5-tier speed architecture:

1. **Sub-5ms Conversational Greeting Fast-Path**:
   - `is_conversational_greeting()` recognizes compound greetings (*"hi"*, *"kaise ho"*, *"namaste ji"*, *"hi am i talking to munim ai"*, *"kya haal hai"*) using zero-intent token analysis. Delivers an instant TwiML XML response in **< 5ms** without invoking any external API or database query.
2. **Groq LPU Fast-Path (~450ms)**:
   - Plain text orders and inquiries run through Groq's high-throughput `qwen/qwen3.8-27b` endpoint with a 3.5s timeout, returning structured intents in **350ms to 600ms**.
3. **Meko Memory TTL Cache (120s)**:
   - Recalled customer preferences and past order facts are cached in memory. Follow-up inquiries within 2 minutes return recalled memories in **< 1ms**.
4. **Non-Blocking Background Memory Writes**:
   - Meko memory persistence (`memory_add`) is scheduled via `asyncio.create_task` in the background, preventing write latency from delaying customer WhatsApp replies.
5. **Direct Binary Media Streaming**:
   - Voice notes and images stream directly from Twilio's media servers into memory and pass to Gemini Multimodal models, avoiding disk I/O bottlenecks.

---

## 🧠 Meko Long-Term Memory Integration

Munim AI connects to **Meko Long-Term Memory** via MCP JSON-RPC over HTTP (`https://mcp.mekodata.ai/mcp`) using 4 isolated datapacks:

| Datapack | Purpose | Usage in Agents |
|---|---|---|
| `munim-customer` | Customer preferences, favorite sizes, past inquiries | Used by `CustomerAgent` for inquiries (*"Same wali kurti available hai?"*) |
| `munim-orders` | Order history, reorder patterns, stock tracking | Used by `OrderAgent` for repeat purchase re-booking (*"Pehle jo order kara tha wahi wapas karna hai"*) |
| `munim-finance` | Payment history, UTR references, dues patterns | Used by `FinanceAgent` for ledger reconciliation |
| `munim-build` | Design contracts, schema obligations, API specifications | Isolated build-time architectural memory (never mixed with product data) |

### Meko ON vs. OFF Demonstration
- **Meko OFF**: Customer asks *"Same wali kurti available hai?"* → Munim AI has no context and responds generically: *"Aap kaunsi kurti ki baat kar rahe hain? Kripya naam aur size batayein."*
- **Meko ON**: Customer asks *"Same wali kurti available hai?"* → Meko recalls *"Customer 918587859710 previously ordered Cotton Anarkali Kurti in size XXL and Red color"* → Munim AI responds: *"Haanji! Aapki previous favorite Cotton Anarkali Kurti (XXL, Red) hamare paas stock mein available hai! Price ₹1299 hai. Kya main aapka order book kar doon?"*

---

## 📦 Async Message Queue & Background Worker

To decouple heavy background jobs, scheduled digests, and outbound notifications, Munim AI implements a **Durable SQLite Queue & Async Worker Engine**:

- **Durable Queue (`backend/app/queue/durable_queue.py`)**:
  - Backed by SQLite table `queue_jobs` with atomic state transitions (`pending` → `processing` → `completed` / `retrying` / `failed`).
  - Supports exponential backoff retries and dead-letter failure logging.
- **Worker Daemon (`backend/app/workers/queue_worker.py`)**:
  - Starts automatically on backend startup via the FastAPI lifespan hook.
  - Job Types supported:
    - `OUTBOUND_WHATSAPP`: Outbound customer & seller messaging via Twilio REST API (automatically enqueued on low-confidence escalation or new payment claim).
    - `PAYMENT_APPROVED_ALERT`: Triggered when seller approves payment on the dashboard (`POST /dashboard/payments/{payment_id}/approve`), dispatching confirmation to buyer.
    - `DAILY_DUES_DIGEST`: Computes hisaab report and dispatches morning digest to owner.
    - `INCOMING_HEAVY_MESSAGE`: Processes long multimodal audio or image analysis asynchronously.
- **Queue REST API (`backend/app/api/routes/queue.py`)**:
  - `GET /queue/status`: Real-time pending, processing, completed, and failed counts.
  - `GET /queue/jobs`: Paginated recent job history.
  - `POST /queue/retry-failed`: 1-click retry for all failed tasks.
- **Dashboard Payment Actions (`backend/app/api/routes/dashboard.py`)**:
  - `POST /dashboard/payments/{payment_id}/approve`: Commits verified claim in Supabase and enqueues customer WhatsApp confirmation via `DurableQueue`.
  - `POST /dashboard/payments/{payment_id}/reject`: Rejects unverified claim.

---

## 📁 Repository Structure

```
Munim AI/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint, lifespan worker, CORS & routing
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── webhook.py          # Sub-5ms fast-path & Twilio WhatsApp webhook handler
│   │   │       ├── auth.py             # Supabase seller registration, login, profile
│   │   │       ├── dashboard.py        # Seller metrics, sales charts, dues API
│   │   │       └── queue.py            # Durable Queue monitoring & retry REST endpoints
│   │   ├── ai/
│   │   │   ├── __init__.py             # Multimodal pipeline exports
│   │   │   ├── gemini.py               # Gemini multimodal client (audio, vision, JSON)
│   │   │   ├── text_extractor.py       # Groq fast-path (<500ms) + Gemini fallback
│   │   │   ├── audio_extractor.py      # Gemini Multimodal Audio voice note extractor
│   │   │   ├── image_extractor.py      # Gemini Vision UPI receipt & handwritten OCR
│   │   │   ├── normalize_message.py    # Strict schema validation & confidence scorer
│   │   │   └── response_generator.py   # Hinglish reply & owner alert builder
│   │   ├── agents/
│   │   │   ├── __init__.py             # Agent exports
│   │   │   ├── orchestrator.py         # Master router, privacy switches & owner commands
│   │   │   ├── customer_agent.py       # Conversation, catalog, policies, escalation
│   │   │   ├── order_agent.py          # Inventory verify, atomic reserve & order math
│   │   │   └── finance_agent.py        # UPI match, payment claims & dues calculation
│   │   ├── memory/
│   │   │   ├── __init__.py             # Memory exports
│   │   │   ├── interface.py            # Abstract memory provider interface
│   │   │   └── meko_adapter.py         # Meko MCP client with TTL cache & non-blocking writes
│   │   ├── queue/
│   │   │   ├── __init__.py             # Queue exports
│   │   │   ├── models.py               # JobType, JobStatus, QueueJob schemas
│   │   │   └── durable_queue.py        # SQLite atomic queue engine with backoff
│   │   ├── workers/
│   │   │   ├── __init__.py             # Worker exports
│   │   │   └── queue_worker.py         # Background async worker & Twilio dispatcher
│   │   ├── models/
│   │   │   ├── schemas.py              # Pydantic core data transfer models
│   │   │   ├── order.py                # Order domain entities
│   │   │   ├── payment.py              # Payment & claim entities
│   │   │   ├── product.py              # Product & inventory entities
│   │   │   └── dashboard_schemas.py    # Analytics schema models
│   │   ├── repositories/               # Supabase database access layer
│   │   │   ├── customer_repository.py
│   │   │   ├── order_repository.py
│   │   │   ├── payment_repository.py
│   │   │   └── product_repository.py
│   │   ├── services/
│   │   │   ├── database_service.py     # Tenant-aware Supabase CRUD helpers
│   │   │   ├── dashboard_service.py    # Analytics aggregation & dues calculation
│   │   │   ├── whatsapp.py             # Twilio REST API outbound dispatcher
│   │   │   └── db.py                   # SQLite message deduplication store
│   │   ├── utils/
│   │   │   └── privacy.py              # Deterministic #private / #resume filter
│   │   └── core/
│   │       ├── config.py               # Pydantic Settings & environment config
│   │       ├── supabase_client.py      # Authenticated Supabase client
│   │       └── auth.py                 # JWT Bearer token authentication dependency
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Dark-green marketing landing page
│   │   ├── dashboard/page.tsx          # Desktop seller dashboard with live refresh
│   │   ├── mobile/page.tsx             # Mobile seller dashboard mockup
│   │   ├── login/page.tsx              # Seller login page
│   │   └── signup/page.tsx             # Seller signup & store onboarding
│   ├── components/                     # Reusable UI components (SplineChart, TopNav, etc.)
│   └── context/AuthContext.tsx         # Global seller authentication state
├── scripts/
│   ├── test_multimodal_extraction.py   # Phase 1 multimodal unit tests
│   ├── test_phase3_agents.py           # Phase 3 agent & orchestrator test suite
│   ├── test_meko_memory.py             # Phase 4 Meko memory & datapacks verification
│   ├── test_repeat_order_flow.py       # Phase 4 repeat order auto-booking verification
│   ├── test_phase5_worker.py           # Phase 5 async worker & queue simulation
│   └── test_supabase_connection.py     # Live Supabase connection diagnostic
├── tests/
│   ├── test_phase5_queue.py            # Phase 5 queue unit & retry tests
│   ├── test_repositories.py            # Database repository tests
│   └── test_auth_and_dashboard.py      # Auth & dashboard API tests
├── .env.example
├── package.json
└── requirements.txt
```

---

## 🛠️ Environment Configuration (`.env`)

Create a `.env` file in the project root:

```env
# ── Twilio WhatsApp API ───────────────────────
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# ── Business Owner Details ─────────────────────
OWNER_WHATSAPP_NUMBER=918587859710

# ── AI Inference Engines ───────────────────────
GROQ_API_KEY=gsk_your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash

# ── Supabase Database & Auth ──────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key

# ── Meko Long-Term Memory (4 Datapacks) ────────
MEKO_API_KEY=mko_tkn_your_meko_key_here
MEKO_DATAPACK_BUILD=0491c3bb-05a2-4e7c-9f02-741b327cd80a
MEKO_DATAPACK_CUSTOMER=176d3ad2-4495-406b-ad41-715488de7713
MEKO_DATAPACK_ORDERS=2bf91f49-255b-45fc-acd7-a22272bfa3f7
MEKO_DATAPACK_FINANCE=f6862f0f-8e0d-43b4-b78d-5eb250edb8a2

# ── Application & Storage ─────────────────────
APP_ENV=development
APP_SECRET_KEY=munim-ai-hackathon-secret-2026
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./backend/data/munim.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Frontend environment file (`frontend/.env`):
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧪 Verification & Test Commands

Run the test suites to verify each layer independently:

```bash
# 1. Test Phase 1 Multimodal Extraction (Text, Voice Note, UPI Image)
python scripts/test_multimodal_extraction.py

# 2. Test Phase 3 Orchestrator & Three Specialized Agents
python scripts/test_phase3_agents.py

# 3. Test Phase 4 Meko Long-Term Memory (4 Datapacks & Meko ON vs OFF)
python scripts/test_meko_memory.py

# 4. Test Phase 4 Repeat Order Auto-Booking with Meko Memory
python scripts/test_repeat_order_flow.py

# 5. Test Phase 5 Async Durable Queue & Background Worker
python scripts/test_phase5_worker.py
python -m pytest tests/test_phase5_queue.py -v

# 6. Test Supabase Database & Auth Connectivity
python -m scripts.test_supabase_connection
```

---

## 🚀 Running Munim AI

### 1. Start FastAPI Backend (with Lifespan Queue Worker)
```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```

### 2. Start Next.js Frontend Dashboard
```bash
cd frontend
pnpm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** for the landing page and **[http://localhost:3000/dashboard](http://localhost:3000/dashboard)** for the seller khata dashboard.

### 3. Expose via ngrok for Live WhatsApp Webhook
```bash
ngrok http 8000
```
Configure your Twilio WhatsApp Sandbox Webhook URL to:
```
https://<YOUR-NGROK-SUBDOMAIN>.ngrok-free.app/webhook
```

---

## 🛡️ License & Compliance

Distributed under the **MIT License**. Built in compliance with India's **Digital Personal Data Protection (DPDP) Act 2023** principles through data minimization, deterministic privacy switches (`#private`), and human-in-the-loop owner approval for financial settlements.
