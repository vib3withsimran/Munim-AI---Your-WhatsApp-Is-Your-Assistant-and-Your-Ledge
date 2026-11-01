# Munim AI 🧾🤖

> **Your WhatsApp is your Assistant, your Cashier, and your Khata.**  
> Munim AI turns an Indian small seller's existing WhatsApp into an automated AI business operations system: it answers customer inquiries, takes orders, matches UPI payment screenshots, and maintains a self-updating ledger in Supabase and Google Sheets — with zero new apps for buyers or sellers to learn.

---

## 🌟 Key Highlights

- 💬 **Multilingual & Hinglish First**: Speaks natural Hindi, Hinglish, and English buyer chats (*"2 anarkali kurti pack kar do XXL size mein"*).
- 🎙️ **Voice Note to Ledger**: Native multimodal audio understanding transcribes spoken Hindi/English voice notes and extracts order items in one shot.
- 📸 **UPI Screenshot & Handwritten OCR**: Automatically detects PhonePe, Google Pay, and Paytm receipts, extracts the 12-digit UTR and ₹ amount, and deciphers paper order lists.
- ⚡ **Sub-1s Fast Path**: Uses Groq LPU inference for instant text turnaround and sub-10ms in-memory routing for conversational greetings (*"hi"*, *"kaise ho"*, *"namaste"*).
- 🧠 **Autonomous Multi-Agent Architecture**: Separate deterministic agents for **Customer Relations**, **Order & Inventory Management**, and **Finance/Ledger Reconciliation**.
- 🔒 **Privacy & DPDP Compliance**: Built-in deterministic `#private` and `#resume` switches allow sellers and customers to opt out of AI processing instantly.
- 📊 **Dual Ledger Architecture**: Real-time Supabase PostgreSQL backend with Row-Level Security (RLS) + dual backup sync to Google Sheets.
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
        [ Instant Fast-Path ]                                  [ Multimodal AI Pipeline ]
     (greetings: < 10ms response)                         ├── Text: Groq (openai/gpt-oss-20b)
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
   • Delivery & return policies                             • Subtotal & total math in Python      • Calculate outstanding dues
   • Owner escalation if conf < 0.70                        • Create order (pending_payment)       • Generate daily sales summary
                     │                                                      │                                      │
                     └──────────────────────────────────────────────────────┴──────────────────────────────────────┘
                                                                │
                                                                ▼
                                                [ Supabase PostgreSQL + RLS ]
                                               (profiles, customers, products,
                                                 orders, order_items, payments)
                                                                │
                                              ┌─────────────────┴─────────────────┐
                                              ▼                                   ▼
                                    [ Next.js Dashboard ]               [ Google Sheets Sync ]
                                    (Desktop & Mobile UI)                 (Background Backup)
```

---

## 🤖 Phase 3: The Orchestrator & Three Specialized Agents

### 1. The Orchestrator (`backend/app/agents/orchestrator.py`)
The Orchestrator evaluates deterministic business rules **before** routing messages to specialized agents:

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
- **Delivery & Tracking**: Fetches existing customer orders from Supabase and gives current parcel status.
- **Store Policies**: Explains standard business policies (e.g., 7-day exchange tag policy, all-India delivery timelines, return guidelines).
- **Escalation Policy**:
  > **If `confidence.overall < 0.70` OR message is a `complaint`:**  
  > The agent **does not guess or invent store policies**. It immediately:
  > 1. Sets `escalate: True` and generates an owner alert with the reason.
  > 2. Sends a reassuring reply to the customer:  
  >    *"Humein khed hai ki aapko pareshani hui. Maine store owner ko ye message notify kar diya hai. Vo personally aapse jaldi contact karenge."*

---

### 3. Order Agent (`backend/app/agents/order_agent.py`)
*The Order & Inventory Operations Specialist.*
- **Strict Deterministic Arithmetic**: Prices, line totals, and order subtotals are calculated **strictly in Python**. LLMs are never allowed to do arithmetic or guess prices.
- **Stock Availability Verification**: Queries catalog stock prior to order booking. If stock is insufficient, alerts the buyer (e.g., *"Sirf 2 available hai, aapne 5 maanga hai"*) and suggests available alternatives.
- **Atomic Stock Reservation**: Creates order header (`pending_payment`), inserts order items, and reserves inventory.
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

## 🎯 How Confidence Scores Are Calculated

Every message (text, audio, image) outputs a structured `ConfidenceScore`:
```json
"confidence": {
  "overall": 0.95,
  "items": 0.95,
  "amount": 1.0
}
```

### Calculation Rules & Penalty Thresholds:
1. **Text Messages**:
   - Clear item names, quantities, and sizes $\rightarrow$ `overall: 0.90 – 0.98`.
   - Vague queries (*"kuch accha dikhao"*, missing size or color) $\rightarrow$ `items: 0.50`, `overall: 0.60`.
2. **Audio Voice Notes**:
   - Clear Hindi/Hinglish speech $\rightarrow$ `overall: 0.88 – 0.95`.
   - Background traffic noise, whispering, or muffled microphone $\rightarrow$ penalized to `overall < 0.70` (triggers owner escalation).
3. **UPI Payment Receipts**:
   - Clear PhonePe/GPay/Paytm checkmark with visible 12-digit UTR and ₹ amount $\rightarrow$ `overall: 0.95 – 1.0`.
   - Blurry image, cropped reference number, or *"Payment Pending"* status $\rightarrow$ penalized to `overall: 0.50 – 0.65` (`escalate_to_owner = True`).
4. **General Escalation Trigger**:
   - Whenever `confidence.overall < 0.75`, `escalate_to_owner` is automatically set to `True`, creating an approval record and preventing blind automated ledger updates.

---

## ⚡ Latency & Speed Optimizations

To comfortably beat Twilio's **15-second webhook timeout window**, Munim AI uses a 4-tier speed architecture:

1. **Sub-10ms Fast-Path Greetings**:
   - Over 18 common greetings (*"hi"*, *"kaise ho"*, *"namaste"*, *"hello ji"*, *"kya haal hai"*) are intercepted by an in-memory dictionary lookup. Response delivered in **< 10ms**.
2. **In-Memory TTL Catalog Cache**:
   - Product catalog is cached in memory with a 5-minute TTL. Eliminates repeated Google Sheets / database roundtrips, saving **2.5 to 4 seconds** per message.
3. **Groq LPU Fast Path (< 1s)**:
   - Plain text orders and inquiries run through Groq's `openai/gpt-oss-20b` endpoint with a 4.0s timeout, returning structured intents in **300ms to 800ms**.
4. **Direct Twilio Binary Media Streaming**:
   - Voice notes and images are streamed directly from Twilio's media servers into memory and passed to Gemini Multimodal models, avoiding disk I/O bottlenecks.

---

## 📁 Updated Project Structure

```
Munim AI/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint, CORS & route registration
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── webhook.py          # Sub-1s Twilio WhatsApp webhook & media handler
│   │   │       ├── auth.py             # Supabase seller registration, login, profile
│   │   │       └── dashboard.py        # Seller metrics, sales charts, dues API
│   │   ├── ai/
│   │   │   ├── __init__.py             # Multimodal pipeline exports
│   │   │   ├── gemini.py               # Gemini multimodal client (audio, vision, JSON)
│   │   │   ├── text_extractor.py       # Groq fast-path (<1s) + Gemini fallback
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
│   │   ├── services/
│   │   │   ├── catalog.py              # Catalog search, variant finder & in-memory cache
│   │   │   ├── orders.py               # create_with_stock_reservation & payment matching
│   │   │   ├── payments.py             # create_claim & outstanding dues arithmetic
│   │   │   ├── database_service.py     # Reusable Supabase CRUD with tenant isolation
│   │   │   ├── dashboard_service.py    # Analytics, revenue, top products, sales trends
│   │   │   ├── sheets.py               # Google Sheets background backup sync
│   │   │   └── db.py                   # SQLite idempotency deduplication
│   │   └── core/
│   │       ├── config.py               # Pydantic Settings
│   │       ├── supabase_client.py      # Cached Supabase client
│   │       └── auth.py                 # JWT Bearer token authentication dependency
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Pixel-accurate marketing landing page
│   │   ├── dashboard/page.tsx          # Desktop seller dashboard with live refresh
│   │   ├── mobile/page.tsx             # Mobile seller dashboard mockup
│   │   ├── login/page.tsx              # Seller login page
│   │   └── signup/page.tsx             # Seller signup & store onboarding
│   ├── components/                     # Reusable UI components (SplineChart, TopNav, etc.)
│   └── context/AuthContext.tsx         # Global seller authentication state
├── scripts/
│   ├── test_multimodal_extraction.py   # Phase 1 multimodal unit tests
│   ├── test_phase3_agents.py           # Phase 3 agent & orchestrator test suite
│   └── test_supabase_connection.py     # Live Supabase connection diagnostic
├── .env.example
├── package.json
└── requirements.txt
```

---

## 🛠️ Environment Configuration (`.env`)

Create a `.env` file in the project root:

```env
# Twilio WhatsApp API
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Business Owner Details
OWNER_WHATSAPP_NUMBER=918587859710

# AI Credentials
GROQ_API_KEY=gsk_your_groq_api_key_here
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Supabase (Database & Auth)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_anon_key

# Google Sheets Backup (Optional)
GOOGLE_SERVICE_ACCOUNT_JSON=./backend/data/service_account.json
GOOGLE_SHEET_ID=your_google_sheet_id_here

# App Settings
APP_ENV=development
APP_SECRET_KEY=munim-ai-hackathon-secret-2026
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

---

## 🧪 Verification & Test Commands

Run the comprehensive test suites to verify each layer independently:

```bash
# 1. Test Phase 1 Multimodal Extraction (Text, Voice Note, UPI Image)
python scripts/test_multimodal_extraction.py

# 2. Test Phase 3 Orchestrator & Three Specialized Agents
python scripts/test_phase3_agents.py

# 3. Test Supabase Database & Auth Connectivity
python -m scripts.test_supabase_connection
```

---

## 🚀 Running Munim AI

### 1. Start FastAPI Backend
```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```

### 2. Start Next.js Frontend Dashboard
```bash
cd frontend
pnpm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** for the marketing landing page and **[http://localhost:3000/dashboard](http://localhost:3000/dashboard)** for the seller khata dashboard.

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
