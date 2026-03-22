# Autonomous AI Job Application Assistant

**An intelligent, local-LLM powered web automation agent designed to autonomously navigate, parse, and interact with complex web applications like LinkedIn.**

Traditional web scrapers and automation bots break whenever a website updates its layout or changes a CSS class name. This project solves that fragility using an innovative **Two-Phase Hybrid Pipeline**:
1. **Strict Deterministic Scripting (Playwright)**: Reliably navigates the authentication phase (e.g. LinkedIn Login) alongside manual user confirmation steps to prevent bot-detection blacklisting.
2. **Cognitive Agent Loop (Local LLM via Ollama)**: The "Brain." It perceives the DOM, processes visible elements into a highly compressed format, makes logical decisions using Pydantic structured schemas, and executes human-like interactions dynamically.

---

## 📂 Folder Structure & File Functions

```text
Job-application-assistant/
├── linkedin_main.py         # Main entry point. Orchestrates the Hybrid Pipeline (Strict Login -> LLM Agent Loop).
├── pyproject.toml / uv.lock # Python package dependencies (rapidly managed by `uv`).
├── .env                     # Local environment variables (Credentials & Config).
│
├── ai_engine/               # The "Brain" of the operation
│   ├── agent_brain.py       # Forces the LLM to output strict JSON commands corresponding to DOM targets. Contains prompt logic.
│   └── resume_parser.py     # Uses a local LLM to extract structured JSON data from your PDF resume.
│
├── scrapers/driver/         # The "Hands and Eyes" (Playwright integration)
│   └── form_filler.py       # Handles the strict login sequence, injects DOM state markers, and executes the physical LLM commands (click, fill, type).
│
├── config/                  # Configuration Loader
│   └── config.py            # Loads .env paths, models, and directory structure safely into the application.
│
├── assets/                  # Master data directory
│   └── resume/              # Place your PDF resumes here to be processed into JSON profiles.
│
└── utils/                   # Helper scripts
    └── func_timers.py       # Performance benchmarking decorators.
```

---

## 🚀 Local Setup & Installation Guide

This project runs 100% locally to protect your personal data and to avoid immense cloud API charges. 

### 1. Prerequisites
- **Python 3.10+** or higher.
- **[uv](https://docs.astral.sh/uv/)** (Extremely fast Python package manager)
  - Install via terminal: `pip install uv`
- **[Ollama](https://ollama.com/)** (Local LLM execution server)
  - Download and install from [ollama.com](https://ollama.com/download). 

### 2. Clone and Install Dependencies
Open your terminal inside the project directory and use `uv` to install dependencies and synchronize the environment:
```bash
uv venv
uv sync
```
*Note: Playwright requires specific browser binaries to run. Install them by running:*
```bash
uv run playwright install firefox
```

### 3. Environment Configuration (`.env`)
Create a `.env` file in the root folder of the project. This configures the agent. You must specify which model the agent should use natively (see Section 4).
```env
LINKEDIN_EMAIL="your.email@example.com"
LINKEDIN_PASSWORD="your_secure_password"
OLLAMA_BASE_URL="http://localhost:11434"
DEFAULT_MODEL="qwen2.5:3b"  
```

### 4. Hardware-Specific AI Model Selection
Because this agent relies heavily on structured JSON outputs, you must pick an LLM that is smart enough to format JSON reliably, but small enough to run rapidly on your specific GPU/CPU setup.

Open a new terminal and run `ollama pull <model_name>` based on your computer's specs:

- **CPU-Only / Standard Laptop (No Dedicated GPU):**
  - **Recommended Model:** `qwen2.5:1.5b` or `llama3.2:1b`
  - **Command:** `ollama pull qwen2.5:1.5b`
  - *Why:* These models are extraordinarily lightweight (~1-2GB) and run entirely on your standard system RAM. They execute rapidly using standard CPU cores without needing an expensive graphics card.

- **Low-End GPU (≤ 4GB VRAM) or Integrated Graphics:**
  - **Recommended Model:** `qwen2.5:3b`
  - **Command:** `ollama pull qwen2.5:3b`
  - *Why:* This model is incredibly optimized, fits entirely in 4GB of VRAM/Shared RAM, and inherently supports strict JSON structured output without hallucinating.

- **Mid-Range GPU (8GB VRAM):**
  - **Recommended Model:** `qwen2.5:7b` or `llama3.1:8b`
  - **Command:** `ollama pull qwen2.5:7b`
  - *Why:* Strikes the perfect balance between complex logical reasoning (for tricky CAPTCHAs and ambiguous forms) and inference speed.

- **High-End GPU (12GB+ VRAM):**
  - **Recommended Model:** `qwen2.5-coder:14b`
  - **Command:** `ollama pull qwen2.5-coder:14b`
  - *Why:* Code-focused models excel tremendously at understanding HTML/DOM structures and complex JSON schemas. Navigation decisions will be practically flawless.

### 5. Running the Agent

**Step A (Optional but recommended): Parse Your Resume**
Place your resume in `assets/resume/your_resume.pdf` (e.g., `mahadev.pdf`) and run:
   ```bash
   uv run python ai_engine/resume_parser.py
   ```
This translates your unstructured PDF into a structured schema located in `assets/profiles/`.

**Step B: Launch the Hybrid Automation Agent**
   ```bash
   uv run python linkedin_main.py
   ```
1. The script will open Firefox and strictly navigate standard LinkedIn login.
2. It will pause mid-way, asking you to strike "Enter" in the terminal sequentially to verify that it isn't triggering anti-bot alarms.
3. Once on the `/jobs` portal, the script relinquishes control to the **AgentBrain loop**.
4. The AI surveys the page layout and executes standard agentic web-browsing tasks seamlessly!
