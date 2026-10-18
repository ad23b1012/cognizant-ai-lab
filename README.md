# 🇮🇳 Scheme Navigator (YojanaMitra AI)
### Welfare & Scholarship Screening Assistant for Indian Citizens
**Cognizant AI Lab × Indian Institute of Information Technology Raichur — Agentic AI Hackathon (October 2026)**

[![Neuro-SAN Studio](https://img.shields.io/badge/Framework-Neuro--SAN%20Studio-blue.svg)](https://github.com/cognizant-ai-lab/neuro-san-studio)
[![LLM](https://img.shields.io/badge/LLM-Google%20Gemini%203.1%20Flash--Lite%20%2B%20OpenRouter-orange.svg)](https://ai.google.dev/)
[![Unit Tests](https://img.shields.io/badge/Automated%20Tests-Included-blue.svg)]()
[![Portal Checks](https://img.shields.io/badge/Portal%20Checks-Reachability%20Only-teal.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-configurable%20sly__data-purple.svg)]()
[![Theme](https://img.shields.io/badge/Theme-AI%20for%20Social%20Good-success.svg)]()

> 📌 **Key Hackathon Submission Deliverables**:
> - 🧱 [**architecture.md**](architecture.md): Prototype agent registry, coded tools, configured `sly_data` handling, and architecture diagrams.
> - 📄 [**summary.md**](summary.md): 2-Page Executive Project Summary, Problem Statement, Solution, Innovation Matrix, and Judging Alignment.
> - 🧪 [**tests/**](tests/): Automated unit tests for eligibility screening, portal fetch behavior, and PDF parsing. Run them locally for current results.

---

## 🌟 Executive Summary & The Problem

In India, central and state governments allocate over **₹3,00,000 Crore annually** across hundreds of citizen welfare and education programs. Yet, over **₹1,00,000 Crore goes unclaimed** or gets rejected every year due to four compounding barriers:

1. **Information Asymmetry**: A rural student in Raichur or an engineering student in Andhra Pradesh rarely knows they qualify for full tuition fee reimbursement (e.g. *Jagananna Vidya Deevena* or *AICTE Pragati*).
2. **Ambiguous Statutory Rules**: A small dryland farmer doesn't know whether cultivating millets qualifies them for state incentives or if income tax filing status disqualifies them from PM-KISAN.
3. **High Document Rejection Rates**: Up to **40% of applications are rejected** due to missing certificates (e.g., 15-digit Nadakacheri RD numbers, MeeSeva certificates, or missing NPCI bank account DBT seeding).
4. **Middlemen Exploitation**: Citizens are frequently exploited by predatory middlemen charging 20–30% bribes for schemes that are 100% free on official government portals.

**Scheme Navigator (YojanaMitra AI)** is a CLI prototype with a Neuro-SAN agent registry. It screens profiles using Python rules, returns rule-level explanations, and checks reachability of configured official government portals. Results are preliminary guidance; scheme rules and application cycles require confirmation with the relevant authority. Privacy depends on the host passing sensitive values through an out-of-band channel; the prototype does not itself guarantee that user disclosures never enter model context.

---

## 🏛️ System Architecture

The HOCON registry defines a hierarchical Neuro-SAN agent network. `main.py` supports both the local CLI and a live Neuro-SAN/`nsflow` session:

```
                            ┌────────────────────────────────────────┐
                            │           Citizen User                 │
                            │  (English, Telugu, Hindi, Kannada, etc)│
                            └───────────────────┬────────────────────┘
                                                │
                                                ▼
                            ┌────────────────────────────────────────┐
                            │    Front Man: CitizenConcierge         │
                            │  (Welcomes, Elicits Profile, Routes)   │
                            └───────┬────────────────────────┬───────┘
                                    │                        │
         ┌──────────────────────────┴──────┐  ┌──────────────┴──────────────────────────┐
         │                                 │  │                                         │
         ▼                                 ▼  ▼                                         ▼
┌────────────────────────┐      ┌────────────────────────┐      ┌───────────────────────────────┐
│ ScholarshipSpecialist  │      │ FarmerWelfareSpecialist│      │  VerificationAuditorAgent     │
│ Higher Education, NSP, │      │ PM-KISAN, PMFBY, KCC,  │      │ Audits Exclusions, Explains   │
│ AICTE Pragati, SSP, AP │      │ Rythu Bharosa, Millets │      │ "Why Not Eligible", Links URLs│
└───────────┬────────────┘      └──────────┬─────────────┘      └───────────────┬───────────────┘
            │                              │                                    │
            └───────────────────────┬──────┴────────────────────────────────────┘
                                    │
                                    ▼
       =================== DETERMINISTIC CODED TOOLS ===================
       │                                                               │
       │  1. LiveSchemeFetcher                                         │
       │     - Live official portal ping (AP JnanaBhumi, NSP, PM-KISAN)│
       │     - Anti-phishing domain defense (strictly .gov.in/.nic.in) │
       │     - Optional PDF/HTML text parser (fetch action)              │
       │                                                               │
       │  2. SchemeEligibilityEngine                                   │
       │     - Python rule checks for implemented schemes │
       │     - Fast matching against verified data/schemes_db.json     │
       │                                                               │
       │  3. DocumentChecklistGenerator                                │
       │     - State issuing authorities (Nadakacheri, MeeSeva, UIDAI) │
       │     - Mandatory attestation and DBT bank seeding guidance     │
       │                                                               │
       │  4. ApplicationGuide                                          │
       │     - Step-by-step portal roadmap, anti-bribe defense         │
       │     - Grama/Ward Sachivalayam e-KYC navigation                │
       =================================================================
                                    │
                                    ▼
       ========== OPTIONAL HOST-CONFIGURED PRIVATE DATA =================
       │  Optional host-configured private fields (`sly_data`):                           │
       │  • Annual Family Income (INR)   • Caste / Social Category     │
       │  • Ration Card Tier             • Aadhaar DBT Status          │
       │  (Use a configured private data channel; the CLI displays persona data locally.)      │
       =================================================================
```

*(For detailed architecture specifications and sequence diagrams, refer to [**architecture.md**](architecture.md).)*

---

## 💎 Key Innovations for the Hackathon

| Innovation | Traditional AI Assistants | Scheme Navigator (YojanaMitra AI) |
|---|---|---|
| **Rule-Based Screening** | May rely on generated answers for criteria. | Deterministic Python checks for the implemented schemes; rules need ongoing official-source review and confirmation. |
| **Portal Reachability & Source Checks** | May output broken or phishing links. | **`LiveSchemeFetcher`**: Checks reachability of configured `.gov.in`/`.nic.in` sites, validates HTTPS government domains for fetches, and can parse fetched PDF/HTML text. Reachability does not verify announcements or rules. |
| **Sensitive Citizen Privacy** | Privacy depends on application design and deployment. | The coded tool can read sensitive values from `sly_data` and omits income/category from its result; deployment must ensure those values are routed privately. |
| **Language Support** | Often requires English-only input. | The concierge prompt defaults to English and supports Telugu, Hindi, Kannada, and Tamil when explicitly requested. The local CLI language showcase uses scripted examples; it does not run an LLM conversation. |
| **Transparent Rejection Audit** | Gives generic "You are not eligible" responses. | Generates a clause-by-clause **"Why am I not eligible" audit trail** detailing exact unmet criteria and recommending alternative schemes. |
| **Hyper-Local State Schemes** | Generic national demos that ignore regional programs. | Tailored to **Andhra Pradesh** (*Jagananna Vidya & Vasathi Deevena*, *Rythu Bharosa*), **Karnataka** (*SSP Post-Matric*, *Raitha Siri*), and **Central NSP**. |
| **Anti-Middleman Citizen Defense** | Leaves citizens vulnerable to fraudulent agents. | Direct `.gov.in` URLs, official grievance helplines, issuing authorities (*MeeSeva*, *Nadakacheri*, *Sachivalayam*), and anti-bribe warnings. |

---

## 📋 Verified Schemes Database (`data/schemes_db.json`)

The registry contains 13 scheme records and source URLs. The stored text is not a live verification; confirm each criterion, benefit, and application cycle with the official authority. The Python engine has separate hardcoded rules for supported IDs, while metadata-only additions are not evaluated:

### 🎓 Higher Education & Scholarships
1. **[AP-EDU-001] Jagananna Vidya Deevena (RTF - Andhra Pradesh)**: 100% full tuition fee reimbursement for eligible B.Tech, Degree, and Polytechnic students with annual family income $\le$ ₹2.5 Lakhs. Portal: `jnanabhumi.ap.gov.in`.
2. **[AP-EDU-002] Jagananna Vasathi Deevena (MTF - Andhra Pradesh)**: ₹20,000/year hostel and food maintenance allowance credited in two installments to the mother's Aadhaar-seeded bank account. Portal: `jnanabhumi.ap.gov.in`.
3. **[EDU-001] PM-USP Central Sector Scheme of Scholarship for College and University Students (CSSS)**: Financial assistance to meritorious students scoring $>80\text{th}$ percentile in Class XII with family income $\le$ ₹4.5 Lakhs. Portal: `scholarships.gov.in`.
4. **[EDU-002] National Means-cum-Merit Scholarship Scheme (NMMSS)**: ₹12,000/yr for meritorious secondary school students (Class IX-XII) with parental income $\le$ ₹3.5 Lakhs.
5. **[EDU-003] Central Sector Scholarship of Top Class Education for SC Students**: Full tuition and academic/living allowances for Scheduled Caste students admitted to notified premier institutes (IITs, NITs, IIITs like IIIT Raichur) with income $\le$ ₹8.0 Lakhs.
6. **[EDU-004] National Fellowship and Scholarship for Higher Education of ST Students (Top Class)**: Support for tuition, living allowance, and computer allowance for ST students in notified institutions with income $\le$ ₹6.0 Lakhs.
7. **[EDU-005] Post-Matric Scholarship for Scheduled Caste Students (PMS-SC)**: Fee reimbursement and monthly maintenance allowances for SC students with family income $\le$ ₹2.5 Lakhs.
8. **[KA-EDU-001] Karnataka State Scholarship Portal (SSP Post-Matric)**: Fee concession, hostel subsidy, and merit awards for Karnataka students linked with Nadakacheri RD certificates. Portal: `ssp.postmatric.karnataka.gov.in`.

### 🌾 Agriculture & Farmer Welfare
9. **[FARM-001] Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)**: ₹6,000/yr in three installments of ₹2,000 for landholding farmer families (with statutory income taxpayer exclusion). Portal: `pmkisan.gov.in`.
10. **[FARM-002] Pradhan Mantri Fasal Bima Yojana (PMFBY)**: Subsidized crop insurance (capped at 2% Kharif, 1.5% Rabi) covering prevented sowing, standing crop damage, and localized natural disaster loss. Portal: `pmfby.gov.in`.
11. **[FARM-003] Kisan Credit Card (KCC)**: Revolving bank credit limit for input purchases at effective prompt repayment rates of 4% per annum.
12. **[FARM-004] PMKSY — Per Drop More Crop (PDMC)**: Subsidized financial assistance for micro-irrigation systems (drip and sprinkler) to maximize water productivity.
13. **[FARM-005] Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)**: Assured old-age pension of ₹3,000 per month after 60 years of age for small & marginal farmers ($\le$ 2 hectares) with entry age between 18–40 years.

---

## 🚀 Quickstart & Setup Guide

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and Git first. Python 3.12 is selected below; `uv` can install it if needed. You will also need a Google Gemini API key from [Google AI Studio](https://aistudio.google.com/). The OpenRouter key is optional.

### Windows (PowerShell)

Install `uv` if it is not already installed, then restart PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Clone the repository, create and activate the virtual environment, install dependencies, and copy the environment template:

```powershell
git clone https://github.com/ad23b1012/cognizant-ai-lab.git
Set-Location cognizant-ai-lab
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS / Linux

Install `uv` if it is not already installed, then restart your shell:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repository, create and activate the virtual environment, install dependencies, and copy the environment template:

```bash
git clone https://github.com/ad23b1012/cognizant-ai-lab.git
cd cognizant-ai-lab
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your API keys:

```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

The OpenRouter key is optional. The other runtime settings are already supplied in `.env.example`.

---

### 6. Run Automated Verification Tests
Run the automated test suite for the current implementation (it does not establish scheme accuracy, privacy guarantees, or portal uptime):

```bash
# Cross-platform execution (works universally):
python -m pytest tests/ -v

# Or using uv:
uv run pytest tests/ -v
```

The previous test transcript was removed because results change with the current code and environment. Run the command above for current output.


---

## 🎮 Running the Project

The repository provides a terminal demo entry point:

### Interactive Terminal Console (`main.py` / `demo_cli.py`)
Run the standalone Rich CLI. It demonstrates the local tools and scripted personas:

```bash
python main.py
# or
python demo_cli.py
```

### Live Neuro-SAN Agent Network

Set `GOOGLE_API_KEY` in `.env`, then launch the Scheme Navigator agent network and `nsflow` UI:

```bash
python main.py --agent
# or
uv run python main.py --agent
```

The dedicated manifest exposes Scheme Navigator without the unrelated example networks in the general development manifest. In `nsflow`, choose **scheme_navigator**. When eligibility checks report missing information, the concierge should ask one short follow-up at a time, offer numbered choices and **Other (please specify)**, then retry after your answer. It should offer **I don't know / Skip** when appropriate. Income, social category, landholding, and tax status must be collected only through a client-supported private `sly_data` field after consent; do not type them into chat. If the client has no private fields, dependent criteria cannot be checked in that session.

The network also sends specialist screening results through an independent auditor review. For supported ineligible schemes, `analyze_eligibility_gaps` simulates one numeric criterion change at a time with the existing rule engine and shows any remaining failures; it never recommends changing official records. When you are preparing an application, `check_application_readiness` asks applicable yes/no/not-sure questions about name matching, DBT, certificates, and institution verification, then returns practical fixes. These checks are guidance, not guarantees of eligibility or acceptance.

**7 Illustrative Demo Scenarios:**

The persona results below are generated from this prototype's implemented rules. They are screening examples, not official eligibility decisions.
1. **🎓 Scenario 1: Undergraduate Technical Student**: Raichur applicant (SC Category, Income ₹1.4L) $\rightarrow$ Screens as eligible for EDU-001 (PM-USP CSSS), EDU-003 (Top Class SC), and EDU-005 (PMS-SC).
2. **🌾 Scenario 2: Smallholder Cultivator**: Rural applicant (3.0 acres, non-taxpayer) $\rightarrow$ Screens as eligible for FARM-001 (PM-KISAN), FARM-002 (PMFBY), FARM-003 (KCC), FARM-004 (PMKSY), and FARM-005 (PM-KMY Pension).
3. **👩‍🎓 Scenario 3: Higher Technical Scholar**: ST Category student (B.Tech, Income ₹3.8L) $\rightarrow$ Screens as eligible for EDU-001 (PM-USP) and EDU-004 (Top Class ST).
4. **🔍 Scenario 4: Transparent Rejection Audit**: Landholder applicant (Taxpayer case) $\rightarrow$ Demonstrates the configured taxpayer exclusion rule and possible alternatives.
5. **✍️ Scenario 5: Custom Interactive Profile**: Enter any custom profile values (State, Course, Income, Quota) and receive a rule-based screening result.
6. **🌐 Scenario 6: Portal monitor and parser demo**: Government portal reachability checks (`.gov.in` / `.nic.in`), an anti-phishing domain check, and a parser demonstration using clearly labeled sample text (not a live gazette).
7. **🗣️ Scenario 7: Multilingual examples**: A scripted showcase for **Telugu (తెలుగు)**, **Hindi (हिंदी)**, **Kannada (ಕನ್ನಡ)**, and **Tamil (தமிழ்)**. It displays example intent/response pairs and does not perform live language understanding or generation.

---

### Neuro-SAN registry

`registries/scheme_navigator.hocon` defines the live network. Use `python main.py --agent` to launch it with the dedicated `registries/scheme_navigator_manifest.hocon`; `python main.py` continues to launch the local terminal demo.

Eligibility conditions are implemented in Python for the supported scheme IDs. Adding a record to `data/schemes_db.json` alone does not add eligibility logic; unsupported IDs are reported without an eligibility decision. Portal ping results establish reachability only, and the returned static guidance is not a live announcement feed. The registry snapshot date and official source URLs are shown with screening results when available.

The demo is not production-ready. Treat its rule output as preliminary screening, confirm scheme criteria and dates with the linked authority, and configure the deployment to keep sensitive profile values out of model-visible prompts.

The local CLI asks for consent before requesting a custom profile, masks sensitive values in its summary, and keeps those values in memory for the local screening workflow. In the live agent UI, private values should be supplied only through the client’s private `sly_data` fields. Do not enter identity numbers.

## 📁 Repository Structure

```text
cognizant-ai-lab/
├── architecture.md                      # 🧱 Complete Multi-Agent Architecture & Sequence Diagrams
├── summary.md                           # 📄 2-Page Executive Project Summary for Hackathon
├── README.md                            # 🚀 Setup, Quickstart & Evaluation Guide
├── main.py                              # 🎮 CLI and Neuro-SAN runtime entrypoint
├── demo_cli.py                          # 🖥️ Interactive visual terminal console (7 scenarios)
├── requirements.txt                     # 📦 Pinned Python dependencies
├── pyproject.toml                       # ⚙️ Project build metadata
├── .env.example                         # 🔑 Template for environment variables
├── .gitignore                           # 🛡️ Git exclusion rules
├── coded_tools/                         # 🐍 Deterministic Python coded tools for implemented rules
│   ├── scheme_navigator/
│   │   ├── scheme_eligibility_engine.py # Deterministic statutory rule validation engine
│   │   ├── live_scheme_fetcher.py       # Portal reachability, allowlisting & PDF/HTML parser
│   │   ├── document_checklist_generator.py # State issuing authority checklist generator
│   │   ├── application_guide.py         # Step-by-step portal roadmap & Sachivalayam e-KYC
│   │   └── __init__.py                  # Package exports
│   └── __init__.py
├── config/
│   └── llm_config.hocon                 # Primary Gemini LLM & fallback configuration
├── data/
│   └── schemes_db.json                  # Official verified schemes database (Central, AP, KA)
├── registries/
│   ├── manifest.hocon                   # Development manifest
│   ├── scheme_navigator_manifest.hocon  # Focused hackathon demo manifest
│   ├── scheme_navigator.hocon           # Multi-agent graph specification (Front Man + Specialists)
│   └── expertise_scoping_instructions.hocon # Guardrail and scoping prompt templates
└── tests/
    ├── test_eligibility.py              # Automated tests for deterministic rules & sly_data privacy
    └── test_live_fetcher.py             # Automated tests for portal pings, PDF parser & whitelists
```

---

## 📊 Alignment with Hackathon Judging Criteria

| Criterion | Weight | How Scheme Navigator Delivers |
|---|---|---|
| **Problem Relevance** | 20% | Directly addresses India's **₹1,00,000 Crore unclaimed benefits crisis** by providing an accessible, transparent, and empathetic bridge for students and farmers. |
| **Innovation** | 20% | Combines Python rule checks for implemented criteria, configurable `sly_data` handling, and government portal reachability checks. |
| **Effective Use of Neuro-SAN** | 20% | Includes a **Front Man architecture** with specialized sub-agents (`ScholarshipSpecialist`, `FarmerWelfareSpecialist`), deterministic `CodedTools`, HOCON configuration, and a focused agent launch path via `python main.py --agent`. |
| **Technical Implementation** | 15% | automated tests for the current prototype, a Rich interactive CLI, and threaded network requests exposed through async tools. |
| **Impact Potential & Scalability** | 15% | The registry is structured for metadata additions; every new scheme also needs reviewed eligibility logic and tests. |
| **Presentation & User Experience** | 10% | Rich terminal panels, scripted examples in four Indic languages, English-default concierge instructions in the registry, and submission materials. |

---

## 👥 Hackathon Team & Acknowledgements
- **Team**: Atom (Scheme Navigator AI)
- **Institution**: Indian Institute of Information Technology Raichur (IIITR)
- **Event**: Cognizant AI Lab × IIIT Raichur Agentic AI Hackathon (October 2026)
- **Framework**: Neuro-SAN Studio by Cognizant Technology Solutions
