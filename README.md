# TalentScout — AI Hiring Assistant

> An intelligent conversational chatbot that screens tech candidates through structured information gathering and adaptive technical assessments.

## Project Overview

TalentScout is an AI-powered hiring assistant built for technology recruitment. It conducts end-to-end candidate screening sessions: collecting personal and professional details, then generating tailored technical questions based on the candidate's declared tech stack. The chatbot adapts question difficulty to the candidate's experience level and maintains full conversational context throughout the session.

**Key Capabilities:**
- Structured 4-phase interview flow (Welcome → Info Gathering → Technical Assessment → Closing)
- Dynamic tech question generation via LLaMA 3.3-70B (Groq)
- Real-time candidate profile card with live completion tracking
- Session summary and downloadable candidate JSON profile
- Exit keyword detection with graceful session closure
- Input validation for email and phone

---

## Installation Instructions

### Prerequisites
- Python 3.9 or higher
- A [Groq API key](https://console.groq.com/)

### Steps

1. **Clone the repository**
```bash
   git clone https://github.com/Aadish2423/talentscout-hiring-assistant.git
   cd talentscout-hiring-assistant
```

2. **Create and activate a virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
   cp .env.example .env
```
   Open `.env` and replace `your_groq_api_key_here` with your actual Groq API key.

5. **Run the application**
```bash
   streamlit run app.py
```
   The app will open at `http://localhost:8501`

---

## Usage Guide

1. Open the app in your browser
2. The chatbot greets you automatically — respond to begin
3. Answer questions about your background (name, email, phone, experience, role, location, tech stack)
4. Once all info is collected, the Technical Assessment begins automatically
5. Answer each technical question in sequence
6. The session ends naturally after all questions, or type `exit` / `bye` at any time
7. A session summary screen displays your profile stats — you can download your full candidate profile as a JSON file.

**Exit keywords:** `exit`, `quit`, `bye`, `goodbye`, `stop`, `end`

---

## Technical Details

| Component | Details |
|---|---|
| **Language** | Python 3.9+ |
| **Frontend** | Streamlit with custom CSS (DM Sans, DM Mono, DM Serif Display) |
| **LLM** | LLaMA 3.3-70B-Versatile via Groq API |
| **LLM Client** | `groq` Python SDK |
| **Env Management** | `python-dotenv` |
| **Data Storage** | Session state (in-memory) + `candidates_log.json` (simulated backend) |

**Architecture Decisions:**
- Full conversation history is sent on every API call to maintain context — no separate memory module needed
- Candidate data is extracted via regex from a structured JSON block the LLM is prompted to emit once info gathering is complete
- Phase detection is derived from conversation content (question patterns, candidate state) rather than a separate state machine

---

## Prompt Design

The system prompt is divided into four phases that mirror the interview flow:

**Phase 1 — Welcome:** Instructs the model to introduce itself and set candidate expectations warmly and concisely.

**Phase 2 — Information Gathering:** Enumerates all 7 required fields and instructs the model to collect them 1-2 at a time (to avoid overwhelming the candidate). After collection, the model is instructed to emit a structured JSON block used to populate the live candidate profile card.

**Phase 3 — Technical Assessment:** Instructs the model to generate 2-3 questions per declared technology, adapting difficulty to years of experience (conceptual for juniors, design/architecture for seniors). Questions are numbered (`Question N/Total`) and tagged with difficulty (`[Beginner]`, `[Intermediate]`, `[Advanced]`), which the frontend parses to render styled question blocks.

**Phase 4 — Closing:** Instructs the model to summarize collected information and inform the candidate about next steps (recruiter contact within 2-3 business days).

**Fallback handling** is addressed via a rule in the system prompt: if the user sends an off-topic message, the model politely redirects back to the interview flow without engaging with the unrelated content.

---

## Challenges & Solutions

**Challenge 1: Extracting structured data from conversational output**
The LLM needed to both converse naturally and emit structured candidate data. Solution: the system prompt instructs the model to emit a ` ```json ... ``` ` block exactly once after info gathering completes. The frontend uses regex to extract and parse this block, stripping it from the displayed message so the UI stays clean.

**Challenge 2: Phase detection without a rigid state machine**
Rather than tracking phase with a counter that could desync from the actual conversation, `smart_phase_detect()` inspects recent assistant messages for question patterns and checks the candidate state object — making phase detection self-healing and conversation-driven.

**Challenge 3: Difficulty calibration**
Static difficulty rules would feel rigid. Solution: the system prompt ties difficulty to the candidate's stated years of experience, letting the LLM reason about appropriate depth dynamically rather than hard-coding cutoffs in application logic.

**Challenge 4: Preventing topic drift**
LLMs naturally follow user-led conversation. A strict rule in the system prompt ("Your ONLY purpose is to screen candidates") combined with explicit redirect instructions ensures the bot stays on task even when candidates try to chat casually.

---

## Data Privacy

- All candidate data is stored in session memory only during the active session
- The `candidates_log.json` file stores anonymizable session metadata locally and is excluded from version control via `.gitignore`
- No data is transmitted to third parties beyond the Groq API (which processes messages to generate responses)
- The application does not collect sensitive financial, government ID, or biometric data
- Designed with GDPR principles: data minimization, purpose limitation, and session-scoped retention

---

## License

MIT License — see `LICENSE` for details.
