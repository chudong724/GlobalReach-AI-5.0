from __future__ import annotations

from urllib.parse import urlparse, urljoin

from tools.email_finder import extract_emails_from_text
from tools.email_verifier import EmailVerifierTool
from tools.google_search import GoogleSearchTool
from tools.jina_reader import JinaReaderTool

COMMON_PATHS = ("", "/contact", "/contact-us", "/about", "/about-us", "/team", "/company")
GENERIC_LOCAL_PARTS = {"info", "sales", "contact", "hello", "support", "office", "business", "marketing", "export"}


def _normalize_website(website: str) -> str:
    value = str(website or "").strip()
    if not value:
        return ""
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value.rstrip("/")


def _domain(website: str) -> str:
    host = urlparse(_normalize_website(website)).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _name_patterns(full_name: str, domain: str) -> list[str]:
    parts = [p.lower() for p in str(full_name or "").replace("-", " ").split() if p.strip()]
    if len(parts) < 2 or not domain:
        return []
    first, last = parts[0], parts[-1]
    values = [
        f"{first}.{last}@{domain}",
        f"{first}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{last}.{first}@{domain}",
    ]
    return list(dict.fromkeys(values))


def _base_confidence(email: str, *, source_type: str, company_domain: str) -> int:
    local, _, domain = email.lower().partition("@")
    if source_type == "website":
        score = 95 if domain == company_domain else 78
        if local in GENERIC_LOCAL_PARTS:
            score -= 8
        return score
    if source_type == "search":
        return 82 if domain == company_domain else 68
    if source_type == "pattern":
        return 42
    return 50


async def discover_contact_emails(website: str, *, contact_name: str = "", company_name: str = "", max_results: int = 20) -> dict:
    site = _normalize_website(website)
    domain = _domain(site)
    if not site or not domain:
        return {"website": website, "domain": "", "candidates": [], "errors": ["valid website required"]}

    candidates: dict[str, dict] = {}
    errors: list[str] = []
    reader = JinaReaderTool()
    verifier = EmailVerifierTool()

    async def add(email: str, source_type: str, source_url: str, evidence: str = "") -> None:
        key = email.lower().strip()
        if not key:
            return
        base = _base_confidence(key, source_type=source_type, company_domain=domain)
        existing = candidates.get(key)
        item = existing or {
            "email": key,
            "source_type": source_type,
            "source_urls": [],
            "evidence": [],
            "confidence": base,
            "verification": {},
        }
        if source_url and source_url not in item["source_urls"]:
            item["source_urls"].append(source_url)
        if evidence and evidence not in item["evidence"]:
            item["evidence"].append(evidence[:300])
        item["confidence"] = max(int(item.get("confidence", 0)), base)
        if existing and source_type == "website":
            item["confidence"] = min(99, item["confidence"] + 3)
        candidates[key] = item

    try:
        for path in COMMON_PATHS:
            url = site if not path else urljoin(site + "/", path.lstrip("/"))
            try:
                text = await reader.read(url)
            except Exception as exc:
                errors.append(f"read {url}: {type(exc).__name__}")
                continue
            for email in extract_emails_from_text(text):
                await add(email, "website", url, "Publicly visible on company website")
    finally:
        await reader.close()

    # Search-engine evidence is supplemental and only used when Serper is configured.
    search = GoogleSearchTool()
    try:
        query = f'site:{domain} "@{domain}" contact email'
        if company_name:
            query = f'"{company_name}" "@{domain}" email'
        try:
            results = await search.search(query, num=10)
            for result in results:
                text = f"{result.get('title','')} {result.get('snippet','')}"
                for email in extract_emails_from_text(text):
                    await add(email, "search", str(result.get("link") or ""), str(result.get("snippet") or ""))
        except Exception as exc:
            errors.append(f"search: {type(exc).__name__}")
    finally:
        await search.close()

    # Pattern inference is deliberately low confidence and never presented as verified discovery.
    for email in _name_patterns(contact_name, domain):
        await add(email, "pattern", site, f"Inferred from contact name pattern: {contact_name}")

    ordered = list(candidates.values())
    checks = await verifier.verify_batch([x["email"] for x in ordered]) if ordered else []
    for item, check in zip(ordered, checks):
        item["verification"] = check
        if check.get("is_deliverable"):
            item["confidence"] = min(99, int(item["confidence"]) + 5)
        else:
            item["confidence"] = max(0, int(item["confidence"]) - 25)
        if item["source_type"] == "pattern":
            item["status"] = "inferred"
        elif check.get("is_deliverable"):
            item["status"] = "public+mx"
        else:
            item["status"] = "public-unverified"

    ordered.sort(key=lambda x: (-int(x.get("confidence", 0)), x["email"]))
    return {
        "website": site,
        "domain": domain,
        "contact_name": contact_name,
        "company_name": company_name,
        "candidates": ordered[:max(1, min(max_results, 50))],
        "errors": errors[:20],
        "policy_note": "Pattern-derived addresses are inference only. MX confirms domain mail capability, not mailbox existence.",
    }
