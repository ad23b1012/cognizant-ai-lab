# 📄 Project Summary: Scheme Navigator (YojanaMitra AI)

**Welfare & Scholarship Screening Assistant for Indian Citizens**
*Cognizant AI Lab × Indian Institute of Information Technology Raichur — Agentic AI Hackathon (October 2026)*  
**Team**: Atom | **Framework**: Cognizant Neuro-SAN Studio | **LLM**: Google Gemini 3.1 Flash-Lite + OpenRouter Fallback

---

### 1. Executive Summary & Problem Context

Every year, the Central and State Governments of India allocate over **₹3,00,000 Crore** across hundreds of citizen welfare and education initiatives. However, an estimated **₹1,00,000+ Crore goes unclaimed or rejected annually**. In rural and semi-urban communities—such as the Kalyana-Karnataka belt surrounding Raichur—eligible citizens routinely miss life-altering benefits due to four systemic barriers:

1. **Information Asymmetry**: Fragmented state and central portals (*NSP, Karnataka SSP, AP JnanaBhumi, PM-KISAN, PMFBY*) obscure eligibility rules from the citizens who need them most.
2. **Statutory Ambiguity & LLM Hallucinations**: Complex criteria (board percentiles, income ceilings, land acreage, crop insurance cutoffs) cause general-purpose AI chatbots to hallucinate dates and thresholds, misinforming vulnerable applicants.
3. **High Procedural Rejection Rates**: Up to **40% of submitted applications fail** during institutional verification due to missing state-specific certificates (e.g., 15-digit Nadakacheri RD numbers, MeeSeva certificates) or lack of **NPCI Direct Benefit Transfer (DBT) bank seeding**.
4. **Middleman Exploitation**: Illiterate and marginalized citizens frequently pay 20% to 30% of their entitlements to predatory brokers for services that are legally free.

**Scheme Navigator (YojanaMitra AI)** is a scheme screening prototype with a local Python CLI and a HOCON registry describing an intended Neuro-SAN agent network. The CLI directly runs deterministic screening and guidance tools; it does not run the agent network or an LLM. The configured concierge prompt defaults to English and allows language changes on explicit request. Results are preliminary and require confirmation with scheme authorities.

---

### 2. Multi-Agent System Architecture (Neuro-SAN)

Scheme Navigator is architected around the **Front Man Multi-Agent Pattern**, declaratively defined in HOCON (`registries/scheme_navigator.hocon`):

* **CitizenConcierge (Front Man Agent)**: The Neuro-SAN public interface, configured to default to English and switch to Telugu, Hindi, Kannada, or Tamil only when explicitly requested. When screening lacks details, it asks one follow-up at a time with numbered options and “Other (please specify).” Run it with `python main.py --agent`; the local CLI remains a separate direct-tool demo.
* **Cross-agent review and application support**: Every specialist result is reviewed by `VerificationAuditorAgent`, which can challenge and request one correction. For implemented rules, what-if analysis computes one-field numeric gaps using the same eligibility engine. A yes/no/not-sure readiness check flags common document, DBT, name-matching, and institution-verification risks with fixes.
* **ScholarshipSpecialist (Subordinate Agent)**: Specialized in higher technical education, degree scholarships, and state fee reimbursement programs (Central Sector PM-USP CSSS, NMMSS, Top Class SC/ST, AP Jagananna Vidya & Vasathi Deevena, Karnataka SSP).
* **FarmerWelfareSpecialist (Subordinate Agent)**: Dedicated to agricultural livelihood support, smallholder land categorization, and statutory exclusions (PM-KISAN, PMFBY Crop Insurance, Kisan Credit Cards, PMKSY Micro-Irrigation, PM-KMY Pension, Rythu Bharosa).
* **VerificationAuditorAgent (Subordinate Agent)**: Conducts adversarial checking and transparent **"Why Not Eligible"** root-cause audits, pinpointing exact unmet criteria and recommending alternative qualified schemes.
* **Deterministic CodedTools Layer (Python)**:
  * `SchemeEligibilityEngine`: Evaluates supported citizen profiles with deterministic Python rules and returns the registry snapshot date and source URLs. Results are preliminary; the rules need ongoing official-source review.
  * `LiveSchemeFetcher`: Checks reachability of official `.gov.in`/`.nic.in` portals, enforces HTTPS domain checks for fetches, and can parse fetched PDF or HTML text. A reachability check does not retrieve announcements; configured portal guidance is static.
  * `DocumentChecklistGenerator`: Maps scheme requirements to localized issuing authorities (*Nadakacheri, MeeSeva, e-Sevai, DigiLocker, UIDAI*).
  * `ApplicationGuide`: Provides step-by-step portal navigation, Aadhaar-NPCI DBT seeding instructions, and anti-bribe warnings.
* **Sensitive data handling (`sly_data`)**: The front-man schema offers income, category, land, and taxpayer fields through the private channel. The eligibility tool requires consent and rejects these values in normal tool arguments. The CLI asks before screening and masks values in its output; production isolation still depends on the runtime and client configuration.

---

### 3. Core Innovations & Competitive Advantages

| Feature | Generic LLM Chatbots | Scheme Navigator (YojanaMitra AI) |
|---|---|---|
| **Eligibility Reliability** | May generate unsupported criteria. | Deterministic Python checks for implemented rules, with missing and unsupported cases surfaced; official criteria and current cycles still require confirmation. |
| **Data Privacy** | Injects citizen income, caste, and PII into external cloud LLM prompts. | `sly_data` can carry sensitive values out-of-band when the host is configured to do so. |
| **Portal Verification** | May recommend broken links or phishing mirrors. | **Live `.gov.in`/`.nic.in` reachability checks**, HTTPS domain validation for fetches, and optional PDF/HTML text parsing. Reachability is not a rules or announcement check. |
| **Language Support** | Often requires English-only input. | The concierge prompt supports English by default and other configured languages on explicit request; the CLI language showcase is scripted. |
| **Transparency** | Generic "You are not eligible" responses without explanation. | **Clause-by-clause audit trails** explaining root causes and recommending alternatives. |
| **Middleman Defense** | No protection against fraudulent third-party intermediaries. | **Strict anti-broker defense**, official issuing authorities, and verified grievance helplines. |

---

### 4. Technical Implementation & Verification Metrics

* **Automated Test Suite**: Automated unit tests are included; run them for current results. (`tests/test_eligibility.py` and `tests/test_live_fetcher.py`) verifying deterministic calculations, income edge cases, taxpayer exclusions, `sly_data` vaulting, portal reachability behavior, URL allowlisting, and PDF guideline ingestion.
* **Interactive Terminal CLI (`demo_cli.py`)**: A local deterministic demo featuring 4 scripted citizen personas, consented custom profiling, portal reachability checks, and scripted language examples. It calls Python tools directly and does not run LLM or Neuro-SAN agents.
* **Neuro-SAN runtime**: `python main.py --agent` launches the HOCON agent network and `nsflow` using the focused Scheme Navigator manifest.
* **Resilience & Dual-Tier Fallback**: Primary Google Gemini 3.1 Flash-Lite backed by automatic zero-retry failover to OpenRouter NVIDIA Nemotron 3.5 Lightning.

---

### 5. Alignment with Hackathon Judging Criteria

| Criterion | Weight | How Scheme Navigator Excels |
|---|---|---|
| **Problem Relevance** | 20% | Directly targets India's **₹1,00,000 Crore unclaimed citizen benefits crisis**, empowering marginalized students and smallholder farmers. |
| **Innovation** | 20% | Blends **deterministic Python statutory verification** (rule-based checks for implemented criteria) with **out-of-band `sly_data` privacy** and **live `.gov.in` portal sync**. |
| **Effective Use of Neuro-SAN** | 20% | Includes a HOCON agent registry and a `main.py --agent` launch path for the focused `nsflow` demo. |
| **Technical Implementation** | 15% | automated tests (run locally for current results), portal reachability checks wrapped for async callers, on-the-fly PDF parsing, and clean modular code architecture. |
| **Impact & Scalability** | 15% | Scheme metadata can be added to `data/schemes_db.json`; eligibility behavior requires a supported Python rule implementation. Future integrations could include with national voice/telephony APIs (Bhashini / Twilio). |
| **Presentation & UX** | 10% | Rich terminal demo with scripted examples in four Indic languages, English-default concierge instructions in the registry, and submission documentation. |

---

### 6. Team & Submission Details

- **Project**: Scheme Navigator (YojanaMitra AI)
- **Repository**: [https://github.com/ad23b1012/cognizant-ai-lab](https://github.com/ad23b1012/cognizant-ai-lab)
- **Institution**: Indian Institute of Information Technology Raichur (IIITR)
- **Hackathon**: Cognizant AI Lab × IIIT Raichur Agentic AI Hackathon (October 2026)

