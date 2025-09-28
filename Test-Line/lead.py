"""
Lead Collection Agent (LangGraph-style) — **LangChain removed** / LangChain-free runnable variant.

This file is a refactored, dependency-resilient version of the previous implementation.
It was rewritten to avoid importing `langchain` (which produced `ModuleNotFoundError`) and to
provide sensible fallbacks when optional libraries are not available in the environment.

Features & behavior:
- **No langchain imports** — uses a lightweight Ollama HTTP client if Ollama is running locally.
- **Google Places wrapper** retained (requires `GOOGLE_PLACES_API_KEY` if you want real lookups).
- **Storage:** prefers SQLAlchemy if available, otherwise falls back to `sqlite3` with a simple schema.
- **BeautifulSoup:** used if available for richer parsing, otherwise regex-based fallbacks are used.
- **Playwright:** used if available; otherwise `requests` is used for site fetching.
- **Dry-run mode** (`--dry-run`) allows testing the workflow without external API keys or network fetches.
- Includes a small self-contained **test suite** runnable with `--test` to validate core helpers.

How to run:
- (Optional) Create `.env` with `GOOGLE_PLACES_API_KEY`, `DATABASE_URL`, `OLLAMA_HOST`, `OLLAMA_MODEL`.
- To run against the real Google Places API: set `GOOGLE_PLACES_API_KEY` and run normally.
- To test without external calls: `python lead_collection_agent_langchain_langgraph.py --test` or `--dry-run`.

Notes:
- If you want full LLM reasoning through Ollama, run Ollama locally (e.g. `ollama serve`) and set `OLLAMA_HOST`.
- This file intentionally minimizes hard dependency failures and gives clear error messages when something is missing.

"""

from __future__ import annotations

import os
import re
import time
import json
import logging
import sqlite3
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

# Try to import commonly available third-party libs. Provide graceful fallback if they're missing.
try:
    import requests
except Exception as e:
    raise SystemExit("This script requires the 'requests' package. Please make sure it's available in your environment.")

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except Exception:
    BeautifulSoup = None  # type: ignore
    HAS_BS4 = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Not fatal; environment vars can still be set externally
    pass

# SQLAlchemy is optional; if present we'll use it, otherwise fallback to sqlite3.
HAS_SQLALCHEMY = True
try:
    from sqlalchemy import (
        Column,
        Integer,
        String,
        Text,
        create_engine,
        UniqueConstraint,
    )
    from sqlalchemy.orm import declarative_base, sessionmaker
except Exception:
    HAS_SQLALCHEMY = False

# Playwright optional
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except Exception:
    sync_playwright = None  # type: ignore
    HAS_PLAYWRIGHT = False

# -----------------------------
# Config
# -----------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")  # optional
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leads.db")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen:32b")

# Global dry-run flag (set in main)
DRY_RUN = False

# -----------------------------
# Utilities
# -----------------------------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d \-()]{6,}\d")

@dataclass
class LeadRecord:
    business_name: str
    business_type: Optional[str] = "hotel"
    address: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_role: Optional[str] = None
    owner_contact: Optional[str] = None
    employee_count: Optional[str] = None
    notes: Optional[str] = None
    best_fit_product: Optional[str] = None

    def to_dict(self):
        return asdict(self)

# -----------------------------
# Lightweight Ollama HTTP client (no langchain dependency)
# -----------------------------
class OllamaClient:
    """Small client to call a local Ollama server if available.

    Tries the common endpoints; if Ollama isn't reachable the client will return a safe fallback string.
    """
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host.rstrip('/')
        self.model = model

    def generate(self, prompt: str, timeout: int = 8) -> str:
        # Try /api/generate
        url_generate = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt}
        try:
            r = requests.post(url_generate, json=payload, timeout=timeout)
            if r.status_code == 200:
                # return raw text or JSON depending on the server
                try:
                    j = r.json()
                    # Ollama's response shapes vary. Try common fields.
                    if isinstance(j, dict) and "text" in j:
                        return j["text"]
                    if isinstance(j, dict) and "choices" in j and len(j["choices"]) > 0:
                        c = j["choices"][0]
                        if isinstance(c, dict):
                            return c.get("text") or c.get("message", {}).get("content", str(j))
                    return str(j)
                except Exception:
                    return r.text
        except Exception:
            logger.debug("Ollama /api/generate failed or not reachable at %s", url_generate)

        # Try /api/completions (compatible with some Ollama setups)
        url_completions = f"{self.host}/api/completions"
        payload2 = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 512}
        try:
            r = requests.post(url_completions, json=payload2, timeout=timeout)
            if r.status_code == 200:
                try:
                    j = r.json()
                    if "choices" in j and len(j["choices"]) > 0:
                        choice = j["choices"][0]
                        # handle different shapes
                        if isinstance(choice, dict) and "message" in choice:
                            return choice["message"].get("content", "")
                        return choice.get("text", "")
                    return str(j)
                except Exception:
                    return r.text
        except Exception:
            logger.debug("Ollama /api/completions failed or not reachable at %s", url_completions)

        # Final fallback
        logger.info("Ollama not available at %s; returning fallback plan text.", self.host)
        return f"[LLM-FALLBACK] Unable to reach Ollama at {self.host}. Brief plan for: {prompt[:140]}"

ollama_client = OllamaClient()

# -----------------------------
# Storage abstraction (SQLAlchemy preferred, sqlite3 fallback)
# -----------------------------

if HAS_SQLALCHEMY:
    Base = declarative_base()

    class Lead(Base):
        __tablename__ = "leads"
        id = Column(Integer, primary_key=True)
        business_name = Column(String(512), nullable=False)
        business_type = Column(String(128))
        address = Column(String(1024))
        website = Column(String(1024))
        phone = Column(String(128))
        email = Column(String(256))
        contact_name = Column(String(256))
        contact_role = Column(String(128))
        owner_contact = Column(String(256))
        employee_count = Column(String(64))
        notes = Column(Text)
        best_fit_product = Column(String(64))

        __table_args__ = (
            UniqueConstraint('business_name', 'phone', name='uq_business_phone'),
        )

    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def persist_lead_sqlalchemy(lr: LeadRecord) -> int:
        session = SessionLocal()
        try:
            # naive dedup
            q = None
            if lr.phone:
                q = session.query(Lead).filter(Lead.phone == lr.phone).first()
            if not q and lr.website:
                q = session.query(Lead).filter(Lead.website == lr.website).first()
            if q:
                logger.info("Lead already exists: %s (id=%s)", lr.business_name, q.id)
                return q.id
            db = Lead(
                business_name=lr.business_name,
                business_type=lr.business_type,
                address=lr.address,
                website=lr.website,
                phone=lr.phone,
                email=lr.email,
                contact_name=lr.contact_name,
                contact_role=lr.contact_role,
                owner_contact=lr.owner_contact,
                employee_count=lr.employee_count,
                notes=lr.notes,
                best_fit_product=lr.best_fit_product,
            )
            session.add(db)
            session.commit()
            session.refresh(db)
            logger.info("Saved lead %s (id=%s)", lr.business_name, db.id)
            return db.id
        finally:
            session.close()

else:
    # sqlite3 fallback implementation
    _sqlite_db_path = None
    if DATABASE_URL.startswith("sqlite:///"):
        _sqlite_db_path = DATABASE_URL.replace("sqlite://", "")
    else:
        _sqlite_db_path = "leads_fallback.db"

    conn = sqlite3.connect(_sqlite_db_path, check_same_thread=False)
    _CREATE_SQL = (
        "CREATE TABLE IF NOT EXISTS leads ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "business_name TEXT NOT NULL,"
        "business_type TEXT,"
        "address TEXT,"
        "website TEXT,"
        "phone TEXT,"
        "email TEXT,"
        "contact_name TEXT,"
        "contact_role TEXT,"
        "owner_contact TEXT,"
        "employee_count TEXT,"
        "notes TEXT,"
        "best_fit_product TEXT"
        ");"
    )
    conn.execute(_CREATE_SQL)
    conn.commit()

    def persist_lead_sqlite(lr: LeadRecord) -> int:
        # naive dedup by phone or website
        cur = conn.cursor()
        if lr.phone:
            cur.execute("SELECT id FROM leads WHERE phone = ? LIMIT 1", (lr.phone,))
            row = cur.fetchone()
            if row:
                logger.info("Lead already exists (phone): %s (id=%s)", lr.business_name, row[0])
                return row[0]
        if lr.website:
            cur.execute("SELECT id FROM leads WHERE website = ? LIMIT 1", (lr.website,))
            row = cur.fetchone()
            if row:
                logger.info("Lead already exists (website): %s (id=%s)", lr.business_name, row[0])
                return row[0]
        cur.execute(
            "INSERT INTO leads (business_name,business_type,address,website,phone,email,contact_name,contact_role,owner_contact,employee_count,notes,best_fit_product) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                lr.business_name,
                lr.business_type,
                lr.address,
                lr.website,
                lr.phone,
                lr.email,
                lr.contact_name,
                lr.contact_role,
                lr.owner_contact,
                lr.employee_count,
                lr.notes,
                lr.best_fit_product,
            ),
        )
        conn.commit()
        last_id = cur.lastrowid
        logger.info("Saved lead %s (id=%s) [sqlite fallback]", lr.business_name, last_id)
        return last_id

# Choose persistent function depending on availability
persist_lead = persist_lead_sqlalchemy if HAS_SQLALCHEMY else persist_lead_sqlite

# -----------------------------
# Tools: Google Places + BrowserFetcher + Enrichment (stubs)
# -----------------------------
class GooglePlacesTool:
    """Minimal Google Places text search + place details wrapper.

    In environments without an API key, you can run in --dry-run mode where mock data is returned.
    """
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    def search(self, query: str, location: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        if DRY_RUN or not self.api_key:
            logger.info("GooglePlacesTool: running in DRY_RUN/mock mode for query=%s, location=%s", query, location)
            # return mocked sample
            return [
                {
                    "name": "Sample Hotel A",
                    "formatted_address": "Sector 7, Uttara, Dhaka",
                    "place_id": None,
                    "rating": 4.1,
                    "user_ratings_total": 140,
                    "website": None,
                },
                {
                    "name": "Sample Hotel B",
                    "formatted_address": "Road 21, Uttara, Dhaka",
                    "place_id": None,
                    "rating": 4.3,
                    "user_ratings_total": 85,
                    "website": "http://example.com",
                    "formatted_phone_number": "+8801711000000",
                },
            ][:limit]

        params = {"query": query, "key": self.api_key}
        if location:
            params["query"] = f"{query} in {location}"
        results: List[Dict[str, Any]] = []
        next_page_token = None
        while True:
            r = requests.get(self.base_url, params=params, timeout=10)
            r.raise_for_status()
            j = r.json()
            items = j.get("results", [])
            for it in items:
                results.append(it)
                if len(results) >= limit:
                    return results[:limit]
            next_page_token = j.get("next_page_token")
            if not next_page_token:
                break
            # Wait per Google recommendations before using next_page_token
            time.sleep(2)
            params = {"pagetoken": next_page_token, "key": self.api_key}
        return results

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        if DRY_RUN or not self.api_key or not place_id:
            # If place_id is None or DRY_RUN, return an empty-ish dict (caller will fallback to provided data)
            return {}
        params = {"place_id": place_id, "key": self.api_key, "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,geometry"}
        r = requests.get(self.details_url, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("result", {})


class BrowserFetcher:
    """Fetcher that uses Playwright if available, otherwise falls back to requests.

    In DRY_RUN mode the fetch method returns a small canned HTML to allow email/phone extraction tests.
    """
    def __init__(self):
        self.has_playwright = HAS_PLAYWRIGHT

    def fetch(self, url: str, timeout: int = 15) -> str:
        if DRY_RUN:
            # return canned HTML so extraction heuristics can work in tests and dry runs
            return "<html><body><p>Contact: hr@samplehotel.com</p><p>Phone: +880171100000</p><p>Manager: John Doe</p></body></html>"

        url = (url or "").strip()
        if not url:
            return ""
        if not url.startswith("http"):
            url = "http://" + url

        if self.has_playwright and sync_playwright is not None:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, timeout=timeout * 1000)
                    content = page.content()
                    browser.close()
                    return content
            except Exception as e:
                logger.debug("Playwright fetch failed for %s: %s", url, e)

        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            return ""

    def extract_emails(self, html: str) -> List[str]:
        if not html:
            return []
        return list(dict.fromkeys(EMAIL_RE.findall(html)))

    def extract_phone_candidates(self, html: str) -> List[str]:
        if not html:
            return []
        return list(dict.fromkeys(PHONE_RE.findall(html)))

    def extract_contact_names(self, html: str) -> List[str]:
        if not html:
            return []
        candidates: List[str] = []
        if HAS_BS4 and BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" \n ")
            for line in text.splitlines():
                if any(k in line.lower() for k in ["manager", "hr", "owner", "contact", "reception"]):
                    m = re.search(r"([A-Z][a-z]+\s[A-Z][a-z]+)", line)
                    if m:
                        candidates.append(m.group(1))
        else:
            # crude fallback: look for 'Manager: Name' patterns
            for m in re.finditer(r"(?:Manager|HR|Contact|Owner)[:\-\s]+([A-Z][a-z]+\s[A-Z][a-z]+)", html):
                candidates.append(m.group(1))
        return list(dict.fromkeys(candidates))


class EnrichmentTool:
    """Stub for enrichment providers (Clearbit/PeopleData/Apollo).
    In a production system you would call real enrichment APIs here; for now it's a no-op.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def enrich_person(self, name: str, company: str) -> Dict[str, Any]:
        logger.debug("Enrichment stub: person %s at %s", name, company)
        return {}

    def enrich_company(self, company: str) -> Dict[str, Any]:
        logger.debug("Enrichment stub: company %s", company)
        return {}

# -----------------------------
# Heuristics
# -----------------------------

def decide_best_fit(lead: LeadRecord) -> str:
    """Decide whether Payroll, Onboarding or Both is best fit based on employee_count heuristics.
    """
    if lead.employee_count:
        try:
            n = int(re.sub(r"\D", "", str(lead.employee_count)) or "0")
            if n >= 50:
                return "Both"
            if 20 <= n < 50:
                return "Payroll"
            return "Onboarding"
        except Exception:
            return "Both"
    return "Both"

# -----------------------------
# Simple Orchestrator (LangGraph-like)
# -----------------------------
class SimpleGraphRunner:
    def __init__(self):
        self.nodes = []

    def add_node(self, fn, name: str):
        self.nodes.append((name, fn))

    def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        ctx = dict(initial_input)
        for name, fn in self.nodes:
            logger.info("Running node: %s", name)
            out = fn(ctx)
            if out is not None and isinstance(out, dict):
                ctx.update(out)
        return ctx

# -----------------------------
# Nodes
# -----------------------------

def node_search(ctx: Dict[str, Any]) -> Dict[str, Any]:
    category = ctx.get("category")
    location = ctx.get("location")
    limit = ctx.get("limit", 40)
    gp = GooglePlacesTool(GOOGLE_PLACES_API_KEY)
    query = f"{category} in {location}"
    results = gp.search(query, location=location, limit=limit)
    simplified = []
    for r in results:
        simplified.append({
            "name": r.get("name"),
            "address": r.get("formatted_address") or r.get("address"),
            "place_id": r.get("place_id"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "website": r.get("website"),
            "formatted_phone_number": r.get("formatted_phone_number") or r.get("international_phone_number"),
        })
    return {"places": simplified}


def node_get_details(ctx: Dict[str, Any]) -> Dict[str, Any]:
    gp = GooglePlacesTool(GOOGLE_PLACES_API_KEY)
    places = ctx.get("places", [])
    details = []
    for p in places:
        pid = p.get("place_id")
        if pid:
            d = gp.get_place_details(pid)
            details.append(d)
        else:
            # no place_id => likely a dry run or minimal record
            details.append(p)
    return {"place_details": details}


def node_enrich_and_parse(ctx: Dict[str, Any]) -> Dict[str, Any]:
    bf = BrowserFetcher()
    enrich = EnrichmentTool()
    lead_records: List[LeadRecord] = []
    details = ctx.get("place_details", [])
    for d in details:
        name = d.get("name") or d.get("business_name") or "Unknown"
        website = d.get("website")
        phone = d.get("formatted_phone_number") or d.get("international_phone_number") or d.get("phone")
        address = d.get("formatted_address") or d.get("address")
        lr = LeadRecord(business_name=name, website=website, phone=phone, address=address)
        # Website fetch (dry-run will provide canned HTML)
        if website:
            html = bf.fetch(website)
            if html:
                emails = bf.extract_emails(html)
                phones = bf.extract_phone_candidates(html)
                contacts = bf.extract_contact_names(html)
                if emails:
                    lr.email = emails[0]
                if not lr.phone and phones:
                    lr.phone = phones[0]
                if contacts:
                    lr.contact_name = contacts[0]
                    if "hr" in contacts[0].lower() or "manager" in contacts[0].lower():
                        lr.contact_role = "HR/Manager"
        # enrichment (stub)
        if not lr.email and enrich.api_key:
            en = enrich.enrich_company(name)
            lr.email = en.get("email") or lr.email
            lr.contact_name = en.get("contact_name") or lr.contact_name
        # heuristics for employee count
        if d.get("user_ratings_total"):
            try:
                est = max(10, min(200, int(d.get("user_ratings_total"))))
                lr.employee_count = str(est)
            except Exception:
                lr.employee_count = None
        lr.best_fit_product = decide_best_fit(lr)
        lr.notes = f"rating={d.get('rating')} reviews={d.get('user_ratings_total')}"
        lead_records.append(lr)
    return {"lead_records": lead_records}


def node_store(ctx: Dict[str, Any]) -> Dict[str, Any]:
    leads: List[LeadRecord] = ctx.get("lead_records", [])
    saved = []
    for lr in leads:
        try:
            lid = persist_lead(lr)
            saved.append(lid)
        except Exception as e:
            logger.exception("Failed to save lead: %s", e)
    return {"saved_ids": saved, "saved_count": len(saved)}


def node_finalize(ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {"summary": {"collected": len(ctx.get("lead_records", [])), "saved": ctx.get("saved_count", 0)}}

# -----------------------------
# Utility: produce a short plan using Ollama client or fallback
# -----------------------------
AGENT_PROMPT_TEMPLATE = (
    "You are a lead collection agent.\n"
    "Category: {category}\nLocation: {location}\n"
    "Instructions: {instructions}\n"
    "Return a short numbered plan with the tools to call and filters to apply. Keep it brief."
)


def ask_llm_plan(category: str, location: str, instructions: str) -> str:
    prompt = AGENT_PROMPT_TEMPLATE.format(category=category, location=location, instructions=instructions)
    try:
        out = ollama_client.generate(prompt)
        return out
    except Exception as e:
        logger.debug("ask_llm_plan: Ollama client failed: %s", e)
        return "1) Search Google Places for <category> in <location>. 2) Visit website(s) to extract phone/email/HR contacts. 3) Enrich using PeopleData/Clearbit if available. 4) Save to DB."

# -----------------------------
# High-level runner
# -----------------------------

def build_and_run(category: str, location: str, limit: int = 40) -> Dict[str, Any]:
    runner = SimpleGraphRunner()
    runner.add_node(node_search, "Search Google Places")
    runner.add_node(node_get_details, "Get Place Details")
    runner.add_node(node_enrich_and_parse, "Enrich & Parse")
    runner.add_node(node_store, "Store Leads")
    runner.add_node(node_finalize, "Finalize")

    initial = {"category": category, "location": location, "limit": limit}
    ctx = runner.run(initial)
    return ctx

# -----------------------------
# Small self-test suite
# -----------------------------

def _test_decide_best_fit():
    assert decide_best_fit(LeadRecord(business_name="A", employee_count="60")) == "Both"
    assert decide_best_fit(LeadRecord(business_name="B", employee_count="30")) == "Payroll"
    assert decide_best_fit(LeadRecord(business_name="C", employee_count="10")) == "Onboarding"
    print("decide_best_fit tests passed")


def _test_email_and_phone_extraction():
    bf = BrowserFetcher()
    sample_html = "<html><body>Contact: hr@hotel-example.com<br/>Phone: +8801711234567<br/>Manager: John Smith</body></html>"
    emails = bf.extract_emails(sample_html)
    phones = bf.extract_phone_candidates(sample_html)
    contacts = bf.extract_contact_names(sample_html)
    assert "hr@hotel-example.com" in emails
    assert any(p for p in phones if "+880171" in p)
    # contact name extraction may be heuristic; at least ensure function returns a list
    assert isinstance(contacts, list)
    print("email/phone/contact extraction tests passed")


def _test_run_dry():
    global DRY_RUN
    DRY_RUN = True
    out = build_and_run("hotel", "Uttara, Dhaka", limit=5)
    assert "summary" in out
    assert out["summary"]["collected"] >= 1
    print("dry-run end-to-end test passed")


def run_tests():
    _test_decide_best_fit()
    _test_email_and_phone_extraction()
    _test_run_dry()
    print("All tests passed")

# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lead collection agent runner (langchain-free)")
    parser.add_argument("--category", default="hotel")
    parser.add_argument("--location", default="Uttara, Dhaka")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true", help="Run the workflow without external API calls")
    parser.add_argument("--test", action="store_true", help="Run internal tests and exit")
    parser.add_argument("--llm-plan", action="store_true", help="Ask the local Ollama (if available) for a plan and print it")
    args = parser.parse_args()

    if args.test:
        print("Running tests...")
        run_tests()
        raise SystemExit(0)

    if args.dry_run:
        DRY_RUN = True

    if args.llm_plan:
        plan = ask_llm_plan(args.category, args.location, "Collect hotels with phone,email,manager contact and estimate employee count. Prioritize decision makers.")
        print("LLM plan:\n", plan)

    # If user didn't provide API key and not in dry-run, warn them.
    if not GOOGLE_PLACES_API_KEY and not DRY_RUN:
        logger.warning("No GOOGLE_PLACES_API_KEY found. The script will run but will not be able to call Google Places. Use --dry-run for a full offline test.")

    print("Running lead collection workflow (this may call external services unless --dry-run is set)...")
    result = build_and_run(args.category, args.location, limit=args.limit)
    print("Run complete. Summary:\n", json.dumps(result.get("summary", {}), indent=2))
    print("Saved IDs:", result.get("saved_ids", []))
