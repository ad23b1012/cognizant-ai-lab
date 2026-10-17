#!/usr/bin/env python3
# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
# Scheme Navigator (YojanaMitra AI) - Interactive Live Demo Console
# Designed for Cognizant AI Lab x IIIT Raichur Agentic AI Hackathon
# Powered by Verified Official Government of India Scheme Registry

import asyncio
import os
import sys
import time
from typing import Any, Dict, List

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Ensure root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coded_tools.scheme_navigator.scheme_eligibility_engine import SchemeEligibilityEngine
from coded_tools.scheme_navigator.document_checklist_generator import DocumentChecklistGenerator
from coded_tools.scheme_navigator.application_guide import ApplicationGuide
from coded_tools.scheme_navigator.live_scheme_fetcher import LiveSchemeFetcher

console = Console()


SCRIPTED_PERSONAS = [
    {
        "id": "1",
        "title": "🎓 Scenario 1: Undergraduate Technical Student (Raichur)",
        "summary": "19-year-old student in Raichur. SC Category, Family Income ₹1.4 Lakhs. Enrolled in higher technical degree.",
        "args": {
            "name": "Applicant #1 (Undergraduate Student)",
            "state": "karnataka",
            "occupation": "student",
            "education_level": "engineering",
            "age": 19,
            "gender": "male",
            "class12_percentile": 89.5
        },
        "sly_data": {
            "annual_income_inr": 140000,
            "social_category": "SC",
            "ration_card_tier": "BPL",
            "aadhaar_seeded": True
        }
    },
    {
        "id": "2",
        "title": "🌾 Scenario 2: Smallholder Cultivator (Raichur Rural)",
        "summary": "28-year-old smallholder cultivator in Raichur with 3.0 acres land. Non-taxpayer seeking agricultural credit & pension.",
        "args": {
            "name": "Applicant #2 (Smallholder Farmer)",
            "state": "karnataka",
            "occupation": "farmer",
            "gender": "male",
            "age": 28,
            "land_acres": 3.0,
            "crops": ["jowar", "cotton"],
            "is_taxpayer": False
        },
        "sly_data": {
            "annual_income_inr": 85000,
            "social_category": "ST",
            "ration_card_tier": "BPL",
            "aadhaar_seeded": True
        }
    },
    {
        "id": "3",
        "title": "👩‍🎓 Scenario 3: Higher Technical Scholar (Top-Class Education)",
        "summary": "20-year-old student pursuing technical degree in notified national institute. ST Category, Family Income ₹3.8 Lakhs.",
        "args": {
            "name": "Applicant #3 (Technical Scholar)",
            "state": "karnataka",
            "occupation": "student",
            "gender": "female",
            "education_level": "engineering",
            "age": 20,
            "class12_percentile": 91.0
        },
        "sly_data": {
            "annual_income_inr": 380000,
            "social_category": "ST",
            "ration_card_tier": "BPL"
        }
    },
    {
        "id": "4",
        "title": "🔍 Scenario 4: Transparent Rejection Audit (Taxpayer Case)",
        "summary": "Agricultural landholder with 8 acres who filed Income Tax in the previous assessment year (Income ₹7.2 Lakhs). Inquiring about eligibility status.",
        "args": {
            "name": "Applicant #4 (Landholder Audit Case)",
            "state": "karnataka",
            "occupation": "farmer",
            "gender": "male",
            "age": 52,
            "land_acres": 8.0,
            "crops": ["cotton", "paddy"],
            "is_taxpayer": True
        },
        "sly_data": {
            "annual_income_inr": 720000,
            "social_category": "General",
            "ration_card_tier": "APL"
        }
    }
]


def display_banner():
    banner_text = """
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                        🇮🇳  SCHEME NAVIGATOR (YojanaMitra AI)                  ║
  ║         Local Citizen Welfare & Scholarship Screening Demo        ║
  ║            Cognizant AI Lab × IIIT Raichur Agentic AI Hackathon               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner_text}[/bold cyan]")
    console.print("[dim]Local deterministic CLI demo • Official portal reachability checks • Scripted language examples • sly_data passed within this process[/dim]\n")


def display_persona_card(persona: Dict[str, Any]):
    p_args = persona["args"]
    p_sly = persona["sly_data"]

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold]Citizen Name:[/bold]", f"[cyan]{p_args.get('name')}[/cyan]")
    table.add_row("[bold]Domicile State:[/bold]", f"[white]{p_args.get('state', '').title()}[/white]")
    table.add_row("[bold]Occupation:[/bold]", f"[yellow]{p_args.get('occupation', '').title()}[/yellow]")
    table.add_row("[bold]Age / Gender:[/bold]", f"{p_args.get('age')} yrs / {p_args.get('gender', '').title()}")
    
    # Showcase sly_data privacy
    table.add_row(
        "[bold magenta]Annual Family Income:[/bold magenta]",
        f"[green]₹{p_sly.get('annual_income_inr', 0):,}[/green] [dim](Local demo value passed via sly_data; not isolated from this CLI)[/dim]"
    )
    table.add_row(
        "[bold magenta]Social Category / Quota:[/bold magenta]",
        f"[white]{p_sly.get('social_category')}[/white] [dim](Local demo value passed via sly_data; not isolated from this CLI)[/dim]"
    )

    if p_args.get("occupation") == "farmer":
        table.add_row("[bold]Landholdings:[/bold]", f"[white]{p_args.get('land_acres')} Acres[/white]")
        table.add_row("[bold]Crops Cultivated:[/bold]", f"[green]{', '.join(p_args.get('crops', []))}[/green]")
        table.add_row("[bold]Income Tax Payer:[/bold]", f"{'Yes ⚠️ (Disqualified for DBT)' if p_args.get('is_taxpayer') else 'No (Eligible for DBT)'}")
    else:
        table.add_row("[bold]Education Course:[/bold]", f"[white]{p_args.get('education_level', '').title()}[/white]")
        table.add_row("[bold]Merit Score:[/bold]", f"[green]{p_args.get('class12_percentile')}% (Class 12)[/green]")

    console.print(Panel(table, title=f"[bold gold1]{persona['title']}[/bold gold1]", border_style="cyan"))


async def run_agent_workflow(persona: Dict[str, Any]):
    engine = SchemeEligibilityEngine()
    doc_tool = DocumentChecklistGenerator()
    guide_tool = ApplicationGuide()

    args = persona["args"].copy()
    sly_data = persona["sly_data"].copy()

    console.print(
        "\n[bold yellow]Local demo workflow[/bold yellow] "
        "[dim](direct Python tool calls; this CLI does not invoke Neuro-SAN agents or an LLM)[/dim]"
    )
    console.print("  1. Citizen profile loaded; the CLI passes income/category in a local sly_data mapping.")
    console.print("  2. Running deterministic eligibility rules...")

    # 1. Evaluate eligibility using the local coded tool.
    elig_result = await engine.async_invoke(args, sly_data)
    if not isinstance(elig_result, dict) or elig_result.get("status") == "INVALID_INPUT":
        console.print(f"[bold red]Eligibility check could not run:[/bold red] {elig_result}")
        return
    eligible_schemes = elig_result.get("eligible_schemes", [])
    ineligible_schemes = elig_result.get("ineligible_schemes", [])
    needs_information = elig_result.get("needs_information", [])
    unsupported_schemes = elig_result.get("unsupported_schemes", [])
    registry_as_of = elig_result.get("registry_as_of") or "date unavailable"
    console.print(f"[dim]Registry snapshot: {registry_as_of}. This is a preliminary screen, not an official decision.[/dim]")

    # 2. Present Eligible Schemes
    console.print(f"\n[bold green]✅ SCHEMES SCREENED AS ELIGIBLE ({len(eligible_schemes)} Found):[/bold green]")
    if eligible_schemes:
        for idx, scheme in enumerate(eligible_schemes, 1):
            details_table = Table(show_header=False, box=None, padding=(0, 1))
            details_table.add_row("[bold]Direct Benefit:[/bold]", f"[bold green]{scheme['benefit']}[/bold green]")
            details_table.add_row("[bold]Authority:[/bold]", f"[dim]{scheme['administering_authority']}[/dim]")
            details_table.add_row("[bold]Official Portal:[/bold]", f"[link={scheme['portal_url']}]{scheme['portal_url']}[/link]")
            if scheme.get("application_status"):
                details_table.add_row("[bold]Registry note (verify live):[/bold]", f"[yellow]{scheme['application_status']}[/yellow]")
            source_urls = scheme.get("source_urls", [])
            if source_urls:
                details_table.add_row("[bold]Official sources:[/bold]", "\n".join(source_urls[:3]))

            # Add rules breakdown
            passed_rules = [f"✓ {r['rule']}: {r['reason']}" for r in scheme["rules_audit"] if r["status"] == "PASS"]
            details_table.add_row("[bold]Passed Rules:[/bold]", f"[green]{' | '.join(passed_rules[:2])}[/green]")

            console.print(Panel(
                details_table,
                title=f"[bold white]{idx}. [{scheme['scheme_id']}] {scheme['scheme_name']}[/bold white] [green bold]● ELIGIBLE[/green bold]",
                border_style="green"
            ))
    else:
        if needs_information:
            console.print("[yellow]No eligible match can be confirmed yet; some schemes need more profile information.[/yellow]")
        else:
            console.print("[yellow]No scheme screens as eligible under the implemented rules for this profile.[/yellow]")

    # 3. Present Ineligible Schemes & "Why am I not eligible" Audit
    if ineligible_schemes:
        console.print(f"\n[bold red]❌ INELIGIBLE SCHEMES - TRANSPARENT AUDIT TRAIL ({len(ineligible_schemes)} Evaluated):[/bold red]")
        audit_table = Table(title="Statutory Rejection Root Cause Analysis", show_lines=True)
        audit_table.add_column("Scheme", style="white", width=28)
        audit_table.add_column("Specific Failed Rule", style="red", width=30)
        audit_table.add_column("Next Step", style="yellow", width=30)
        audit_table.add_column("Official Source", style="cyan", width=30)

        for s in ineligible_schemes[:3]:  # Top 3 most relevant ineligibilities
            audit_table.add_row(
                f"[{s['scheme_id']}] {s['scheme_name']}",
                s["why_not_eligible"] or "Criteria mismatch",
                s["actionable_advice"],
                "\n".join(s.get("source_urls", [])[:2]) or "See official portal"
            )
        console.print(audit_table)

    if needs_information:
        console.print("\n[bold yellow]More information needed[/bold yellow]")
        for item in needs_information:
            fields = ", ".join(item.get("missing_fields", [])) or "profile details"
            console.print(f"  • {item.get('scheme_name', item.get('scheme_id'))}: provide {fields} to screen this scheme.")

    if unsupported_schemes:
        console.print("\n[bold dim]Rules not implemented for these registry entries[/bold dim]")
        for item in unsupported_schemes:
            console.print(f"  • {item.get('scheme_name', item.get('scheme_id'))} ({item.get('scheme_id')})")

    # 4. Document Checklist
    if eligible_schemes:
        console.print("\n[bold cyan]Next steps for your strongest current match[/bold cyan]")
        console.print("[dim]The first eligible result follows registry order; confirm current rules and deadlines with the authority.[/dim]")
        eligible_ids = [s["scheme_id"] for s in eligible_schemes]
        doc_result = await doc_tool.async_invoke({"scheme_ids": eligible_ids, "state": args.get("state")}, sly_data)
        console.print("  3. DocumentChecklistGenerator completed locally.")
        console.print(f"\n[bold cyan]📑 OFFICIAL DOCUMENT PREPARATION CHECKLIST:[/bold cyan]")
        doc_table = Table(show_lines=True)
        doc_table.add_column("Certificate / Document", style="bold white", width=28)
        doc_table.add_column("Issuing Authority", style="cyan", width=25)
        doc_table.add_column("Digital Procurement & DigiLocker Tip", style="dim", width=40)

        for d in doc_result["consolidated_checklist"][:4]:
            doc_table.add_row(
                d["document_name"],
                d["issuing_authority"],
                d["digital_acquisition_tips"]
            )
        console.print(doc_table)

    # 5. Application Steps for Top Scheme
    if eligible_schemes:
        top_scheme_id = eligible_schemes[0]["scheme_id"]
        guide_result = await guide_tool.async_invoke({"scheme_id": top_scheme_id}, sly_data)
        console.print("  4. ApplicationGuide completed locally.")
        console.print(f"\n[bold magenta]🚀 APPLICATION ROADMAP FOR: {guide_result['scheme_name']}[/bold magenta]")
        for i, step in enumerate(guide_result["step_by_step_instructions"], 1):
            console.print(f"  [bold cyan]{i}.[/bold cyan] {step}")

        console.print(f"\n[bold red]⚠️ Middlemen & Rejection Warning:[/bold red] [dim]{guide_result['official_verification_notice']}[/dim]")


async def interactive_mode():
    console.print("\n[bold cyan]=== Custom Interactive Citizen Consultation ===[/bold cyan]")
    name = console.input("[bold]Enter Citizen Name: [/bold]") or "Citizen"
    occ = console.input("[bold]Occupation (student / farmer) [default: student]: [/bold]").lower() or "student"
    state = console.input("[bold]State (e.g. karnataka, andhra_pradesh) [default: karnataka]: [/bold]").lower() or "karnataka"
    income_str = console.input("[bold]Annual Family Income (INR) [default: 150000]: [/bold]") or "150000"
    try:
        income = float(income_str)
    except ValueError:
        income = 150000.0

    category = console.input("[bold]Social Category (General / OBC / SC / ST) [default: SC]: [/bold]") or "SC"

    args = {
        "name": name,
        "occupation": occ,
        "state": state,
        "gender": "male",
        "age": 20
    }
    sly_data = {
        "annual_income_inr": income,
        "social_category": category,
        "ration_card_tier": "BPL"
    }

    if occ == "farmer":
        acres_str = console.input("[bold]Landholding in Acres [default: 3.0]: [/bold]") or "3.0"
        args["land_acres"] = float(acres_str)
        args["is_taxpayer"] = False
    else:
        args["education_level"] = "engineering"
        args["class12_percentile"] = 88.0

    custom_persona = {
        "title": f"Custom Consultation for {name}",
        "args": args,
        "sly_data": sly_data
    }
    display_persona_card(custom_persona)
    await run_agent_workflow(custom_persona)


async def run_live_portal_monitor():
    fetcher = LiveSchemeFetcher()
    console.print(Panel(
        "[bold green]🌐 LIVE OFFICIAL PORTAL MONITOR & PDF GUIDELINE INSPECTOR[/bold green]\n"
        "[dim]Checks portal reachability and restricts fetches to HTTPS .gov.in / .nic.in hosts. Reachability does not verify scheme rules.[/dim]",
        border_style="green"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Querying live government endpoints (NSP, PM-KISAN, PMFBY, MyScheme, SSP)...[/bold cyan]"),
        transient=True
    ) as progress:
        progress.add_task("ping", total=None)
        res = await fetcher.async_invoke({"action": "check_portal_status"}, {})

    portals = res.get("portals", [])
    table = Table(title="Live Portal Reachability and Registry Guidance", show_header=True, header_style="bold magenta")
    table.add_column("Portal", style="bold cyan", width=22)
    table.add_column("Live Status", style="green", width=14)
    table.add_column("Latency", style="yellow", width=10)
    table.add_column("Static registry guidance (not live notices)", style="white")

    for p in portals:
        status_text = "🟢 Reachable" if p.get("is_operational") else "🔴 Unreachable / check failed"
        latency = p.get("response_time_ms")
        latency_text = f"{latency} ms" if latency is not None else "—"
        guidance = p.get("static_guidance") or []
        table.add_row(p.get("portal_name", "Unknown portal"), status_text, latency_text,
                      guidance[0] if guidance else "No static guidance configured")

    console.print(table)

    # Demonstrate the allowlist rejecting a non-government domain.
    console.print("\n[bold yellow]🛡️ Anti-phishing domain allowlist demonstration:[/bold yellow]")
    fake_url = "https://fake-scholarship-agent.com/apply-now.pdf"
    blocked_res = await fetcher.async_invoke({"action": "fetch_official_pdf_guidelines", "url": fake_url}, {})
    console.print(f"  [bold]Input URL:[/bold] [dim]{fake_url}[/dim]")
    console.print(f"  [bold red]Result:[/bold red] {blocked_res.get('status')} - [italic]{blocked_res.get('error', '')[:85]}...[/italic]")

    # Demonstrate parsing on sample text; this sample is not downloaded from a portal.
    console.print("\n[bold green]📑 Guideline parser demonstration (sample text, not a live source):[/bold green]")
    sample_text = (
        "SCHEME OF CENTRAL SECTOR SCHOLARSHIP FOR COLLEGE AND UNIVERSITY STUDENTS\n"
        "Ministry of Education, Department of Higher Education\n"
        "Family income shall not exceed Rs. 4,50,000 per annum from all sources.\n"
        "Rate of scholarship of Rs. 20,000 per annum for higher technical degree.\n"
        "Mandatory documents: Aadhaar Card, Income Certificate, Class 12 marksheet."
    )
    parsed = fetcher.parse_guideline_text(sample_text, "https://scholarships.gov.in/guidelines.pdf")
    console.print(f"  • [bold]Detected Scheme:[/bold] {parsed['parsed_name']}")
    console.print(f"  • [bold]Statutory Income Ceiling:[/bold] ₹{parsed['income_ceiling_inr']:,}")
    console.print(f"  • [bold]Monetary Benefit:[/bold] {parsed['benefit_summary']}")
    console.print(f"  • [bold]Mandatory Certificates:[/bold] {', '.join(parsed['mandatory_documents'])}")
    console.print("  • [bold]Source status:[/bold] [yellow]Illustrative sample only; no government document was fetched for this parse.[/yellow]")


async def run_vernacular_showcase():
    engine = SchemeEligibilityEngine()

    console.print(Panel(
        "[bold cyan]🗣️ SCRIPTED MULTILINGUAL EXAMPLE SHOWCASE (ಯೋಜನಾಮಿತ್ರ / యోజనామిత్ర / योजनामित्र / யோஜனாமித்ரா)[/bold cyan]\n"
        "[dim]Prewritten examples: Kannada (ಕನ್ನಡ) • Telugu (తెలుగు) • Hindi (हिंदी) • Tamil (தமிழ்); no live language model runs in this CLI.[/dim]",
        border_style="cyan"
    ))

    vernacular_demos = [
        {
            "id": "1",
            "lang": "ಕನ್ನಡ (Kannada)",
            "title": "🌾 ರಾಯಚೂರಿನ ಸಣ್ಣ ರೈತ (Raichur Smallholder Farmer)",
            "query": "ನಮಸ್ಕಾರ! ನಾನು ರಾಯಚೂರಿನ 3 ಎಕರೆ ಜಮೀನಿರುವ ರೈತ, ಜೋಳ ಮತ್ತು ಸಜ್ಜೆ (ಸಿರಿಧಾನ್ಯ) ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ. ನನಗೆ ಯಾವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಸಬ್ಸಿಡಿಗಳು ಸಿಗುತ್ತವೆ?",
            "translation": "Hello! I am a farmer in Raichur with 3 acres land cultivating Jowar and Bajra (millets). Which government schemes and subsidies can I get?",
            "params": {
                "name": "Applicant (Kannada Farmer)",
                "state": "karnataka",
                "occupation": "farmer",
                "land_acres": 3.0,
                "crops": ["jowar", "millets"],
                "is_taxpayer": False,
                "age": 32,
                "gender": "male"
            },
            "sly_data": {
                "annual_income_inr": 85000,
                "social_category": "ST",
                "ration_card_tier": "BPL",
                "aadhaar_seeded": True
            },
            "vernacular_response": {
                "greeting": "ನಮಸ್ಕಾರ! ಯೋಜನಾಮಿತ್ರ (Scheme Navigator) ಗೆ ಸ್ವಾಗತ. ರಾಯಚೂರಿನ ನಮ್ಮ ರೈತ ಬಾಂಧವರಿಗೆ ಶುಭೋದಯ!",
                "summary": "ನಿಮ್ಮ 3 ಎಕರೆ ಜಮೀನಿಗೆ ಹಾಗೂ ಜೋಳ/ಸಿರಿಧಾನ್ಯ ಬೆಳೆಗಳಿಗೆ ನೀವು ಈ ಕೆಳಗಿನ 5 ಪ್ರಮುಖ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳಿಗೆ ಅರ್ಹರಾಗಿದ್ದೀರಿ:",
                "schemes": [
                    ("FARM-001: ಪಿಎಂ-ಕಿಸಾನ್ (PM-KISAN)", "ವಾರ್ಷಿಕ ₹6,000 ನೇರ ನಗದು ವರ್ಗಾವಣೆ (3 ಕಂತುಗಳಲ್ಲಿ ತಲಾ ₹2,000)", "pmkisan.gov.in"),
                    ("FARM-002: ಪ್ರಧಾನ ಮಂತ್ರಿ ಫಸಲ್ ಬಿಮಾ ಯೋಜನೆ (PMFBY)", "ಬೆಳೆ ಹಾನಿ ವಿಮೆ ರಕ್ಷಣೆ (ಖಾರಿಫ್ ಬೆಳೆಗೆ ಕೇವಲ 2% ಕಂತು)", "pmfby.gov.in"),
                    ("FARM-003: ಕಿಸಾನ್ ಕ್ರೆಡಿಟ್ ಕಾರ್ಡ್ (KCC)", "ರಿಯಾಯಿತಿ ದರದ ಶೇ. 4% ಬಡ್ಡಿಯಲ್ಲಿ ಕೃಷಿ ಸಾಲ ಮಿತಿ", "kcc.gov.in"),
                    ("FARM-004: ಪಿಎಂಕೆಎಸ್‌ವೈ (PMKSY) ಹನಿ ನೀರಾವರಿ", "ಸಿರಿಧಾನ್ಯಕ್ಕೆ ಹನಿ ಮತ್ತು ತುಂತುರು ನೀರಾವರಿ ಸಹಾಯಧನ", "pmksy.gov.in"),
                    ("FARM-005: ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಮಾನ್‌ಧನ್ (PM-KMY)", "60 ವರ್ಷ ವಯಸ್ಸಿನ ನಂತರ ತಿಂಗಳಿಗೆ ₹3,000 ಖಚಿತ ಪಿಂಚಣಿ", "maandhan.in")
                ],
                "documents": [
                    "ಭೂಮಿ RTC ಪಹಣಿ ಪತ್ರ (Bhoomi Portal / ಗ್ರಾಮ ಲೆಕ್ಕಾಧಿಕಾರಿ)",
                    "ಆಧಾರ್ ಕಾರ್ಡ್ ಹಾಗೂ NPCI ಜೋಡಣೆಗೊಂಡ ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್",
                    "ನಾಡಕಚೇರಿ ಜಾತಿ ಮತ್ತು ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ (RD Number)",
                    "ಕರ್ನಾಟಕ FRUITS FID ತಂತ್ರಾಂಶ ನೋಂದಣಿ ಸಂಖ್ಯೆ"
                ],
                "caution": "⚠️ ಎಚ್ಚರಿಕೆ: ಯಾವುದೇ ದಲ್ಲಾಳಿಗಳಿಗೆ ಅಥವಾ ಮಧ್ಯವರ್ತಿಗಳಿಗೆ ಹಣ ನೀಡಬೇಡಿ! ಅರ್ಜಿ ಸಲ್ಲಿಕೆ ಸರ್ಕಾರಿ ಪೋರ್ಟಲ್ ಹಾಗೂ ರೈತ ಸಂಪರ್ಕ ಕೇಂದ್ರಗಳಲ್ಲಿ ಉಚಿತವಾಗಿದೆ."
            }
        },
        {
            "id": "2",
            "lang": "తెలుగు (Telugu)",
            "title": "🎓 ఇంజనీరింగ్ విద్యార్థి స్కాలర్‌షిప్ (Engineering Technical Student)",
            "query": "నమస్కారం! నేను రాయచూర్ ఇంజనీరింగ్ విద్యార్థిని (SC కేటగిరీ, కుటుంబ వార్షిక ఆదాయం ₹1.4 లక్షలు). నాకు కేంద్ర మరియు రాష్ట్ర ప్రభుత్వాల నుండి ఏ స్కాలర్‌షిప్‌లు వస్తాయి?",
            "translation": "Namaskaram! I am an engineering student in Raichur (SC category, annual income ₹1.4 Lakhs). Which Central and State government scholarships do I qualify for?",
            "params": {
                "name": "Applicant (Telugu Student)",
                "state": "karnataka",
                "occupation": "student",
                "education_level": "engineering",
                "category": "SC",
                "annual_income_inr": 140000,
                "age": 19,
                "class12_percentile": 89.5,
                "gender": "male"
            },
            "sly_data": {
                "annual_income_inr": 140000,
                "social_category": "SC",
                "ration_card_tier": "BPL",
                "aadhaar_seeded": True
            },
            "vernacular_response": {
                "greeting": "నమస్కారం! యోజనామిత్ర (Scheme Navigator) కు స్వాగతం. రాయచూర్ ఇంజనీరింగ్ విద్యార్థిగా మీకు అభినందనలు!",
                "summary": "మీ ప్రొఫైల్ ప్రకారం (SC కేటగిరీ, ఆదాయం ₹1.4 లక్షలు, ఇంటర్ 89.5%), మీరు ఈ 3 ప్రధాన స్కాలర్‌షిప్‌లకు పూర్తి అర్హులు:",
                "schemes": [
                    ("EDU-001: PM-USP సెంట్రల్ సెక్టార్ స్కాలర్‌షిప్ (CSSS)", "డిగ్రీ చదువులకు వార్షిక ఆర్థిక సాయం (మెరిట్ ఆధారితం)", "scholarships.gov.in"),
                    ("EDU-003: టాప్ క్లాస్ ఎడ్యుకేషన్ ఫర్ SC స్టూడెంట్స్", "ప్రతిష్టాత్మక విద్యాసంస్థల్లో (IIIT/NIT) పూర్తి ట్యూషన్ ఫీజు రీయింబర్స్‌మెంట్", "scholarships.gov.in"),
                    ("EDU-005: పోస్ట్-మెట్రిక్ స్కాలర్‌షిప్ ఫర్ SC (PMS-SC)", "పూర్తి ఫీజు మినహాయింపు మరియు నెలవారీ హాస్టల్ నిర్వహణ అలవెన్స్", "ssp.postmatric.karnataka.gov.in")
                ],
                "documents": [
                    "మీసేవ / నాడకచేరి కుల ధృవీకరణ పత్రం (SC Certificate)",
                    "తాహసిల్దార్ జారీ చేసిన ఆదాయ ధృవీకరణ పత్రం (Income Certificate)",
                    "ఆధార్ కార్డు మరియు NPCI లింక్ అయిన బ్యాంక్ ఖాతా (DBT)",
                    "కాలేజీ అడ్మిషన్ లెటర్ & 12వ తరగతి మార్కుల జాబితా"
                ],
                "caution": "⚠️ హెచ్చరిక: స్కాలర్‌షిప్ దరఖాస్తు పూర్తిగా ఉచితం! దళారులను నమ్మి ఎటువంటి లంచాలు ఇవ్వకండి. నేరుగా scholarships.gov.in లో OTR పూర్తి చేయండి."
            }
        },
        {
            "id": "3",
            "lang": "हिंदी (Hindi)",
            "title": "🌾 छोटे किसान की योजनाएं (Smallholder Farmer Inquiry)",
            "query": "नमस्ते! मैं एक छोटा किसान हूँ (2.5 एकड़ भूमि, गैर-करदाता)। मुझे कौन सी सरकारी योजनाएं और पेंशन मिल सकती है?",
            "translation": "Namaste! I am a small farmer with 2.5 acres land, non-taxpayer. Which government schemes and pensions can I get?",
            "params": {
                "name": "Applicant (Hindi Farmer)",
                "state": "karnataka",
                "occupation": "farmer",
                "land_acres": 2.5,
                "crops": ["jowar", "cotton"],
                "is_taxpayer": False,
                "age": 35,
                "gender": "male"
            },
            "sly_data": {
                "annual_income_inr": 90000,
                "social_category": "OBC",
                "ration_card_tier": "BPL",
                "aadhaar_seeded": True
            },
            "vernacular_response": {
                "greeting": "नमस्ते! योजनामित्र (Scheme Navigator) में आपका स्वागत है।",
                "summary": "आपकी 2.5 एकड़ जोत एवं किसान प्रोफाइल के आधार पर, आप निम्नलिखित 4 प्रमुख योजनाओं के लिए पात्र हैं:",
                "schemes": [
                    ("FARM-001: प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)", "प्रति वर्ष ₹6,000 की सीधी आर्थिक सहायता (3 किस्तों में ₹2,000)", "pmkisan.gov.in"),
                    ("FARM-002: प्रधानमंत्री फसल बीमा योजना (PMFBY)", "प्राकृतिक आपदा एवं फसल क्षति पर व्यापक सुरक्षा (1.5%-2% प्रीमियम)", "pmfby.gov.in"),
                    ("FARM-003: किसान क्रेडिट कार्ड (KCC)", "4% रियायती ब्याज दर पर कृषि ऋण सुविधा", "kcc.gov.in"),
                    ("FARM-005: प्रधानमंत्री किसान मानधन योजना (PM-KMY)", "60 वर्ष की आयु के पश्चात ₹3,000 मासिक सुनिश्चित पेंशन", "maandhan.in")
                ],
                "documents": [
                    "भूलेख / खतौनी / जमाबंदी नकल (Land Ownership Record)",
                    "आधार कार्ड एवं बैंक पासबुक (NPCI / DBT सक्रिय)",
                    "स्व-प्रमाणित घोषणा पत्र (आयकरदाता न होने का प्रमाण)"
                ],
                "caution": "⚠️ सतर्कता: किसी भी बिचौलिए या अनधिकृत एजेंट को कमीशन न दें! पीएम-किसान पोर्टल (pmkisan.gov.in) पर पंजीकरण 100% निःशुल्क है।"
            }
        },
        {
            "id": "4",
            "lang": "தமிழ் (Tamil)",
            "title": "🎓 கல்லூரி மாணவர் கல்வி உதவித்தொகை (College Student Scholarship)",
            "query": "வணக்கம்! நான் ஒரு கல்லூரி பொறியியல் மாணவர் (SC பிரிவு, குடும்ப ஆண்டு வருமானம் ₹1.5 லட்சம்). எனக்கு என்ன மத்திய அரசு கல்வி உதவித்தொகை கிடைக்கும்?",
            "translation": "Vanakkam! I am a college engineering student (SC category, annual family income ₹1.5 Lakhs). What Central government scholarships do I qualify for?",
            "params": {
                "name": "Applicant (Tamil Student)",
                "state": "karnataka",
                "occupation": "student",
                "education_level": "engineering",
                "category": "SC",
                "annual_income_inr": 150000,
                "age": 19,
                "class12_percentile": 88.0,
                "gender": "male"
            },
            "sly_data": {
                "annual_income_inr": 150000,
                "social_category": "SC",
                "ration_card_tier": "BPL",
                "aadhaar_seeded": True
            },
            "vernacular_response": {
                "greeting": "வணக்கம்! யோஜனாமித்ரா (Scheme Navigator) விற்கு நல்வரவு. தங்களின் கல்விப் பயணத்திற்கு வாழ்த்துகள்!",
                "summary": "தங்களின் விவரங்களின்படி (SC பிரிவு, குடும்ப வருமானம் ₹1.5 லட்சம், பொறியியல் படிப்பு), தாங்கள் பின்வரும் 3 உதவித்தொகைகளுக்கு தகுதி பெற்றுள்ளீர்கள்:",
                "schemes": [
                    ("EDU-001: PM-USP மத்திய துறை உதவித்தொகை (CSSS)", "பல்கலைக்கழக மற்றும் கல்லூரி பட்டப்படிப்பு மாணவர்களுக்கான நிதியுதவி", "scholarships.gov.in"),
                    ("EDU-003: உயர் கல்வி நிறுவனங்களுக்கான உயர்மட்ட கல்வி உதவித்தொகை (Top Class SC)", "முன்னணி தேசிய கல்வி நிறுவனங்களில் (IIIT/NIT) முழு கல்வி கட்டண தள்ளுபடி", "scholarships.gov.in"),
                    ("EDU-005: போஸ்ட்-மெட்ரிக் கல்வி உதவித்தொகை (PMS-SC)", "முழு கட்டண விலக்கு மற்றும் மாதாந்திர பராமரிப்பு உதவித்தொகை", "scholarships.gov.in")
                ],
                "documents": [
                    "சாதி சான்றிதழ் (e-Sevai / வட்டாட்சியர் அலுவலகம்)",
                    "வருமான சான்றிதழ் (ஆண்டு வருமானம் ₹2.5 லட்சத்திற்குள்)",
                    "ஆதார் அட்டை மற்றும் NPCI இணைக்கப்பட்ட வங்கி கணக்கு",
                    "கல்லூரி சேர்க்கை கடிதம் மற்றும் 12-ஆம் வகுப்பு மதிப்பெண் சான்றிதழ்"
                ],
                "caution": "⚠️ எச்சரிக்கை: இடைத்தரகர்களுக்கு எவ்வித கமிஷனும் கொடுக்க வேண்டாம்! தேசிய கல்வி உதவித்தொகை இணையதளத்தில் (scholarships.gov.in) விண்ணப்பிப்பது முற்றிலும் இலவசம்."
            }
        }
    ]

    console.print("\n[bold]Select a scripted language example:[/bold]")
    for d in vernacular_demos:
        console.print(f"  [bold cyan][{d['id']}][/bold cyan] {d['title']}")
    console.print("  [bold cyan][5][/bold cyan] ✍️  Enter a query to display (not processed by a model)")

    sub_choice = console.input("\n[bold yellow]Select Example (1-5) [default: 1]: [/bold yellow]") or "1"

    if sub_choice in ("1", "2", "3", "4"):
        item = next(d for d in vernacular_demos if d["id"] == sub_choice)

        console.print(f"\n[bold green]━━━ 🇮🇳 {item['lang']} Demonstration ━━━[/bold green]")
        console.print(f"[bold]🗣️ Citizen Inquiry ({item['lang']}):[/bold]")
        console.print(f"  [italic cyan]\"{item['query']}\"[/italic cyan]")
        console.print(f"  [dim]Translation: \"{item['translation']}\"[/dim]")

        # Parameters and response are prewritten examples, not live model output.
        console.print("\n[bold yellow]Scripted example details:[/bold yellow]")
        console.print(f"  • [bold]Example language:[/bold] [green]{item['lang']}[/green]")
        console.print("  • [bold]Prewritten profile passed to the local rule engine:[/bold]")
        for k, v in item["params"].items():
            if k != "name":
                console.print(f"      - {k}: [cyan]{v}[/cyan]")

        # Step 2: Deterministic Python Engine Execution
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]Evaluating deterministic scheme rules in Python...[/bold cyan]"),
            transient=True
        ) as progress:
            progress.add_task("calc", total=None)
            calc_res = await engine.async_invoke(item["params"], item["sly_data"])

        eligible_count = len(calc_res.get("eligible_schemes", []))
        console.print(f"  • [bold]Deterministic Python Engine Result:[/bold] [bold green]✓ {eligible_count} schemes screened as eligible under implemented rules[/bold green]")

        # Step 3: Display the prewritten example response.
        vr = item["vernacular_response"]
        console.print(f"\n[bold magenta]Prewritten example response in {item['lang']}:[/bold magenta]")
        console.print(f"[bold]{vr['greeting']}[/bold]\n{vr['summary']}\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ಯೋಜನೆ / పథకం / योजना / திட்டம்", style="bold cyan")
        table.add_column("ಸೌಲಭ್ಯ / ప్రయోజనం / लाभ / பயன்கள்", style="green")
        table.add_column("ಅಧಿಕೃತ ಪೋರ್ಟಲ್ / అధికారిక వెబ్‌సైట్", style="yellow")

        for name, benefit, portal in vr["schemes"]:
            table.add_row(name, benefit, portal)
        console.print(table)

        console.print("\n[bold]📑 ಅಗತ್ಯ ದಾಖಲೆಗಳು / అవసరమైన ధృవీకరణ పత్రాలు / आवश्यक दस्तावेज / தேவையான ஆவணங்கள்:[/bold]")
        for doc in vr["documents"]:
            console.print(f"  • [white]{doc}[/white]")

        console.print(f"\n[bold red]{vr['caution']}[/bold red]")

    elif sub_choice == "5":
        user_query = console.input("\n[bold yellow]Enter text to display (the CLI will not process it): [/bold yellow]")
        if user_query:
            console.print(f"\n[bold]Unprocessed sample text:[/bold] [italic cyan]{user_query}[/italic cyan]")
            console.print("[yellow]No language detection, intent extraction, or agent call was made. Use a separately configured Neuro-SAN runtime for live conversations.[/yellow]")


async def main():
    display_banner()

    while True:
        console.print("\n[bold]Choose a Demo Scenario to Run:[/bold]")
        for p in SCRIPTED_PERSONAS:
            console.print(f"  [bold cyan][{p['id']}][/bold cyan] {p['title']}")
        console.print("  [bold cyan][5][/bold cyan] ✍️  Interactive Custom Profile")
        console.print("  [bold cyan][6][/bold cyan] 🌐 Live Official Portal Monitor & PDF Guideline Inspector")
        console.print("  [bold cyan][7][/bold cyan] 🗣️  Scripted Multilingual Language Examples (తెలుగు | தமிழ் | ಕನ್ನಡ | हिंदी)")
        console.print("  [bold cyan][0][/bold cyan] 🚪 Exit")

        choice = console.input("\n[bold yellow]Select Option (0-7) [default: 1]: [/bold yellow]") or "1"
        if choice == "0":
            console.print("[dim]Exiting Scheme Navigator. All the best for the Hackathon![/dim]")
            break
        elif choice in ("1", "2", "3", "4"):
            persona = next(p for p in SCRIPTED_PERSONAS if p["id"] == choice)
            display_persona_card(persona)
            await run_agent_workflow(persona)
        elif choice == "5":
            await interactive_mode()
        elif choice == "6":
            await run_live_portal_monitor()
        elif choice == "7":
            await run_vernacular_showcase()
        else:
            console.print("[red]Invalid choice. Please select 0-7.[/red]")

        console.print("\n" + "═" * 79)


if __name__ == "__main__":
    asyncio.run(main())

