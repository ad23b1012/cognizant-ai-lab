# 📄 Project Summary: Scheme Navigator (YojanaMitra AI)

**Autonomous Multi-Agent Welfare & Scholarship Concierge for Indian Citizens**  
*Cognizant AI Lab × Indian Institute of Information Technology Raichur — Agentic AI Hackathon (October 2026)*  
**Team**: Atom | **Framework**: Cognizant Neuro-SAN Studio | **LLM**: Google Gemini 3.1 Flash-Lite + OpenRouter Fallback

---

### 1. Executive Summary & Problem Context

Every year, the Central and State Governments of India allocate over **₹3,00,000 Crore** across hundreds of citizen welfare and education initiatives. However, an estimated **₹1,00,000+ Crore goes unclaimed or rejected annually**. In rural and semi-urban communities—such as the Kalyana-Karnataka belt surrounding Raichur—eligible citizens routinely miss life-altering benefits due to four systemic barriers:

1. **Information Asymmetry**: Fragmented state and central portals (*NSP, Karnataka SSP, AP JnanaBhumi, PM-KISAN, PMFBY*) obscure eligibility rules from the citizens who need them most.
2. **Statutory Ambiguity & LLM Hallucinations**: Complex criteria (board percentiles, income ceilings, land acreage, crop insurance cutoffs) cause general-purpose AI chatbots to hallucinate dates and thresholds, misinforming vulnerable applicants.
3. **High Procedural Rejection Rates**: Up to **40% of submitted applications fail** during institutional verification due to missing state-specific certificates (e.g., 15-digit Nadakacheri RD numbers, MeeSeva certificates) or lack of **NPCI Direct Benefit Transfer (DBT) bank seeding**.
4. **Middleman Exploitation**: Illiterate and marginalized citizens frequently pay 20% to 30% of their entitlements to predatory brokers for services that are legally free.

**Scheme Navigator (YojanaMitra AI)** bridges this gap by deploying an autonomous, empathetic multi-agent concierge built on **Cognizant's Neuro-SAN framework**. It conversationally elicits citizen profiles in native Indic languages, performs preliminary rule-based screening for implemented schemes, supports sensitive values supplied through `sly_data`, and checks reachability of configured government portals. Results require confirmation with scheme authorities.

---

### 2. Multi-Agent System Architecture (Neuro-SAN)

Scheme Navigator is architected around the **Front Man Multi-Agent Pattern**, declaratively defined in HOCON (`registries/scheme_navigator.hocon`):

* **CitizenConcierge (Front Man Agent)**: The public multilingual voice of the system. Welcomes citizens in **Telugu (తెలుగు)**, **Hindi (हिंदी)**, **Kannada (ಕನ್ನಡ)**, **Tamil (தமிழ்)**, and **English**, decomposes conversational inquiries into structured parameters, delegates to domain specialists, and synthesizes actionable guidance with fraud advisories.
* **ScholarshipSpecialist (Subordinate Agent)**: Specialized in higher technical education, degree scholarships, and state fee reimbursement programs (Central Sector PM-USP CSSS, NMMSS, Top Class SC/ST, AP Jagananna Vidya & Vasathi Deevena, Karnataka SSP).
* **FarmerWelfareSpecialist (Subordinate Agent)**: Dedicated to agricultural livelihood support, smallholder land categorization, and statutory exclusions (PM-KISAN, PMFBY Crop Insurance, Kisan Credit Cards, PMKSY Micro-Irrigation, PM-KMY Pension, Rythu Bharosa).
* **VerificationAuditorAgent (Subordinate Agent)**: Conducts adversarial checking and transparent **"Why Not Eligible"** root-cause audits, pinpointing exact unmet criteria and recommending alternative qualified schemes.
* **Deterministic CodedTools Layer (Python)**:
  * `SchemeEligibilityEngine`: Evaluates citizen profiles against verified rules in `data/schemes_db.json` with 0% LLM hallucination.
  * `LiveSchemeFetcher`: Performs real-time uptime health checks on official `.gov.in`/`.nic.in` portals, enforces strict anti-phishing domain whitelists, and parses statutory PDF gazettes on-the-fly (`pypdf`).
  * `DocumentChecklistGenerator`: Maps scheme requirements to localized issuing authorities (*Nadakacheri, MeeSeva, e-Sevai, DigiLocker, UIDAI*).
  * `ApplicationGuide`: Provides step-by-step portal navigation, Aadhaar-NPCI DBT seeding instructions, and anti-bribe warnings.
* **Sensitive data handling (`sly_data`)**: The coded tool can accept private values through `sly_data` and omits income and category from its result. The host must configure private routing; this repository does not guarantee model-prompt or log isolation.

---

### 3. Core Innovations & Competitive Advantages

| Feature | Generic LLM Chatbots | Scheme Navigator (YojanaMitra AI) |
|---|---|---|
| **Eligibility Reliability** | Hallucinates statutory cutoffs, income limits, and application deadlines. | Deterministic Python checks for implemented scheme rules; official criteria and current cycles still require confirmation. |
| **Data Privacy** | Injects citizen income, caste, and PII into external cloud LLM prompts. | `sly_data` can carry sensitive values out-of-band when the host is configured to do so. |
| **Portal Verification** | Recommends static or broken links; vulnerable to phishing mirrors. | **Live `.gov.in`/`.nic.in` network pings** and on-the-fly statutory PDF gazette guideline parsing. |
| **Language Inclusivity** | English-dominated; struggles with rural Indian vernacular nuances. | **Native Indic fluency** in Telugu, Hindi, Kannada, Tamil, and English with conversational parameter extraction. |
| **Transparency** | Generic "You are not eligible" responses without explanation. | **Clause-by-clause audit trails** explaining root causes and recommending alternatives. |
| **Middleman Defense** | No protection against fraudulent third-party intermediaries. | **Strict anti-broker defense**, official issuing authorities, and verified grievance helplines. |

---

### 4. Technical Implementation & Verification Metrics

* **Automated Test Suite**: Automated unit tests are included; run them for current results. (`tests/test_eligibility.py` and `tests/test_live_fetcher.py`) verifying deterministic calculations, income edge cases, taxpayer exclusions, `sly_data` vaulting, portal reachability behavior, URL allowlisting, and PDF guideline ingestion.
* **Interactive Terminal CLI (`demo_cli.py`)**: A demo visual console featuring 4 scripted citizen personas (Raichur SC engineering student, rural dryland farmer, ST technical scholar, taxpayer audit case), interactive custom profiling, live portal monitoring, and a dedicated **Multilingual Native Language Assistant**.
* **Neuro-SAN registry**: HOCON describes the intended agent network; `main.py` launches the CLI and does not start an `nsflow` web UI.
* **Resilience & Dual-Tier Fallback**: Primary Google Gemini 3.1 Flash-Lite backed by automatic zero-retry failover to OpenRouter NVIDIA Nemotron 3.5 Lightning.

---

### 5. Alignment with Hackathon Judging Criteria

| Criterion | Weight | How Scheme Navigator Excels |
|---|---|---|
| **Problem Relevance** | 20% | Directly targets India's **₹1,00,000 Crore unclaimed citizen benefits crisis**, empowering marginalized students and smallholder farmers. |
| **Innovation** | 20% | Blends **deterministic Python statutory verification** (rule-based checks for implemented criteria) with **out-of-band `sly_data` privacy** and **live `.gov.in` portal sync**. |
| **Effective Use of Neuro-SAN** | 20% | Includes a HOCON agent registry; `main.py` launches the CLI, and no `nsflow` web UI is launched by this entry point. |
| **Technical Implementation** | 15% | automated tests (run locally for current results), portal reachability checks wrapped for async callers, on-the-fly PDF parsing, and clean modular code architecture. |
| **Impact & Scalability** | 15% | Scheme metadata can be added to `data/schemes_db.json`; eligibility behavior requires a supported Python rule implementation. Future integrations could include with national voice/telephony APIs (Bhashini / Twilio). |
| **Presentation & UX** | 10% | Native Indic conversational fluency in 5 languages, Rich terminal UI panels, and comprehensive submission documentation. |

---

### 6. Team & Submission Details

- **Project**: Scheme Navigator (YojanaMitra AI)
- **Repository**: [https://github.com/ad23b1012/cognizant-ai-lab](https://github.com/ad23b1012/cognizant-ai-lab)
- **Institution**: Indian Institute of Information Technology Raichur (IIITR)
- **Hackathon**: Cognizant AI Lab × IIIT Raichur Agentic AI Hackathon (October 2026)

