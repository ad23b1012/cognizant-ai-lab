# 📄 PROJECT SUMMARY: Scheme Navigator (YojanaMitra AI)
### Autonomous Multi-Agent Welfare & Scholarship Concierge for Indian Citizens
**Cognizant AI Lab × IIIT Raichur Agentic AI Hackathon | October 2026**

---

### 1. Executive Summary & Problem Context
India spends hundreds of thousands of crores annually on welfare programs for farmers, students, and underprivileged families. Despite this massive investment, **over 40% of eligible citizens in rural and semi-urban areas fail to access benefits** due to:
* **Information Asymmetry**: Complex eligibility criteria scattered across multiple central and state portals (NSP, SSP, PM-KISAN, MeeSeva).
* **Document Ambiguity**: Applications getting rejected at verification stages due to missing state-specific certificates (e.g. Nadakacheri 15-digit RD numbers or NPCI bank account seeding).
* **Middleman Exploitation**: Illiterate or semi-literate citizens paying up to 20-30% of their benefit in bribes to local brokers for services that are legally free.

**Scheme Navigator (YojanaMitra AI)** solves this using an autonomous multi-agent architecture built on **Cognizant's Neuro-SAN framework**. It provides a conversational, compassionate concierge in English, Telugu (తెలుగు), Hindi (हिंदी), Kannada (ಕನ್ನಡ), and Tamil (தமிழ்) that determines citizen eligibility **with 100% mathematical certainty** through deterministic Python tools, preserves sensitive financial privacy, and generates an official application roadmap.

---

### 2. Multi-Agent Architecture on Neuro-SAN
The system leverages Neuro-SAN's declarative HOCON graph and CodedTool capabilities:

1. **Front Man Agent (`CitizenConcierge`)**:
   * Engages citizens in natural, empathetic conversation across **Telugu, Hindi, Kannada, Tamil**, and English.
   * Discovers background, education, land ownership, and socioeconomic status.
   * Delegates domain tasks to specialized subordinate agents.

2. **Domain Specialist: Higher Education (`ScholarshipSpecialist`)**:
   * Focuses on Central Sector (PM-USP CSSS), NMMSS, Top Class SC Scholarship, Top Class ST Scholarship, and Post-Matric SC (PMS-SC).
   * Calculates exact monetary benefit and fee waiver components per official guidelines.

3. **Domain Specialist: Agriculture (`FarmerWelfareSpecialist`)**:
   * Focuses on verified farmer welfare: PM-KISAN, PMFBY Crop Insurance, Kisan Credit Cards, PMKSY Per Drop More Crop, and PM-KMY Pension.
   * Checks statutory landholding, small/marginal classification, and exclusion clauses.

4. **Auditor Agent (`VerificationAuditorAgent`)**:
   * Analyzes ineligibility root causes ("Why Am I Not Eligible?").
   * Verifies all portal links belong to official `.gov.in` and `.nic.in` domains.
   * Attaches warnings against middlemen and fraudulent commission agents.

5. **Deterministic Coded Tools (`CodedTool` Hierarchy)**:
   * `SchemeEligibilityEngine`: Evaluates citizen profiles against official rules stored in `schemes_db.json`. Zero LLM hallucination on cutoff percentages or income ceilings.
   * `DocumentChecklistGenerator`: Maps eligible schemes to specific issuing authorities (Nadakacheri, MeeSeva, e-Sevai, DigiLocker, UIDAI).
   * `ApplicationGuide`: Generates a step-by-step application walkthrough with helpline contacts.
   * `LiveSchemeFetcher`: Connects to live Indian government networks (`.gov.in` / `.nic.in`), rejects unverified 3rd-party commercial broker websites, and extracts statutory requirements from official PDF gazettes using `pypdf`.

6. **Zero-Leakage Financial Privacy (`sly_data`)**:
   * Citizen annual income, caste quotas, and ration card details are passed exclusively through Neuro-SAN's `sly_data` channel.
   * Sensitive socioeconomic data is processed out-of-band by the Python engine without leaking into the public LLM prompt or chat log.

---

### 3. Key Differentiators & Technical Highlights
* **Zero Hallucination Guarantee**: Many LLM prototypes fail because the model "invents" scholarship dates or eligibility rules. In Scheme Navigator, **eligibility decisions are 100% coded in Python**, while the LLM handles empathy, translation, and user explanation.
* **Native Indic Multilingual Support**: First-class support for **Telugu, Hindi, Kannada, and Tamil**. Unstructured vernacular queries are decomposed into structured tool parameters, and statutory advice is delivered back in the citizen's mother tongue.
* **Live Government Sync & Anti-Phishing Firewall**: Validates real-time uptime across NSP, PM-KISAN, PMFBY, and Karnataka SSP. Proactively shields citizens by rejecting non-government application links.
* **Dual-Tier Zero-Downtime Resilience**: Implements an automatic failover from Google Gemini 3 Flash to OpenRouter NVIDIA Nemotron 3.5 Lightning with `max_retries: 0`, guaranteeing continuous operation even if free API rate limits are exceeded.
* **Hyper-Localized for IIIT Raichur & Karnataka**: Specifically incorporates Kalyana-Karnataka regional realities — Karnataka SSP Post-Matric, Raitha Siri millet incentives, FRUITS ID, and Nadakacheri RD numbers.
* **Transparent Rejection Audits**: When a citizen is ineligible (e.g., a farmer paying income tax or an engineering student with family income exceeding ₹4.5 Lakhs), the system provides clear statutory reasons and recommends alternative schemes.

---

### 4. Verification & Testing
* **Automated Test Suite**: 13 comprehensive unit tests (`tests/test_eligibility.py` and `tests/test_live_fetcher.py`) validate edge cases, income thresholds, taxpayer exclusions, `sly_data` security, live portal monitoring, domain security whitelists, and PDF guideline parsing.
* **Interactive Rich CLI Console (`demo_cli.py`)**: A terminal UI demonstrating 4 realistic citizen personas, custom interactive profiling, live official portal monitoring with PDF guideline extraction, and a dedicated **Multilingual Native Language Assistant** for Telugu, Hindi, Kannada, and Tamil.
* **Live Web UI (`nsflow`)**: Fully verified on `localhost:4173` with visual agent delegation graphs.

---

### 5. Future Scalability & Impact
* **Open Schema Integration**: New state schemes (e.g., Telangana ePASS, Tamil Nadu Moovalur) can be onboarded in minutes by appending JSON entries or using the automated `discover_and_ingest_scheme` tool without modifying any Python code.
* **Voice & WhatsApp Deployment**: Can be connected via Twilio or Bhashini voice interfaces to enable illiterate rural farmers to query welfare benefits via a phone call.
