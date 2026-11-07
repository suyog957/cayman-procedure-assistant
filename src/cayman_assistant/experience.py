"""Presentation helpers; no generated markup or untrusted HTML is executed."""
from html import escape
from hashlib import sha256
from pathlib import Path
import base64
import re

SHORT_NAMES = {"PR1000": "Notary services", "PR1263": "Records & destruction", "PR1277": "Identity requirements",
               "PR1779": "Business deposit accounts", "PR1949": "Savings bonds", "PR2306": "Copies & statements",
               "PR2321": "Teller approvals", "PR472": "Payment maintenance", "PR607": "TIN & foreign status",
               "PR63": "Coin-counting machines", "PR7554": "Incoming cash shipments"}

ICONS = {
    "spark": '<path d="m12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4Z"/><path d="m20 2 .7 1.3L22 4l-1.3.7L20 6l-.7-1.3L18 4l1.3-.7Z"/>',
    "book": '<path d="M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H4Z"/><path d="M20 4h-5a3 3 0 0 0-2 3v14a4 4 0 0 1 4-2h3Z"/>',
    "shield": '<path d="m12 3 8 3v6c0 4-4.2 7.2-8 9-3.8-1.8-8-5-8-9V6Z"/><path d="m8 12 3 3 5-6"/>',
    "layers": '<path d="m12 3 10 5-10 5L2 8Z"/><path d="m2 12 10 5 10-5M2 16l10 5 10-5"/>',
    "coins": '<ellipse cx="9" cy="6" rx="6" ry="3"/><path d="M3 6v5c0 1.7 2.7 3 6 3M3 11v5c0 1.7 2.7 3 6 3"/><ellipse cx="16" cy="13" rx="5" ry="2.5"/><path d="M11 13v5c0 1.4 2.2 2.5 5 2.5s5-1.1 5-2.5v-5"/>',
    "file": '<path d="M14 2H5v20h14V7Z"/><path d="M14 2v6h5M8 12h8M8 16h8"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "activity": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    "chart": '<path d="M4 3v18h17M8 16v-5M13 16V7M18 16v-3"/>',
}


def icon(name: str) -> str:
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'


def brand_header(root: Path) -> str:
    data = base64.b64encode((root / "assets/brand/wells-fargo-wordmark.png").read_bytes()).decode()
    return f'<div class="wf-topbar"><div class="wf-brand"><img src="data:image/png;base64,{data}" alt="Wells Fargo"><div class="wf-brand-divider"></div><div class="wf-product-wrap"><span class="wf-product">Branch Assist</span><span class="wf-mobile-prototype">Interview prototype</span></div></div><div class="wf-header-right"><span class="header-mode">PROCEDURE WORKSPACE</span><span class="wf-prototype">Interview prototype</span></div></div>'


def source_integrity(root: Path, source: dict) -> bool:
    """Check the cited file now, not a fabricated or permanently cached badge."""
    try:
        path = (root / source["source_file"]).resolve()
        path.relative_to(root.resolve())
        return sha256(path.read_bytes()).hexdigest() == source["source_sha256"]
    except (ValueError, OSError, KeyError):
        return False


def source_html(source: dict) -> str:
    return '<div class="source-text">' + escape(source["text"]) + '</div>'


def response_badge(status: str) -> tuple[str, str]:
    return {"answered": ("Checks passed", ""), "partial": ("Partial support", "review"),
            "evidence_only": ("Source review needed", "review"), "unsupported": ("Insufficient evidence", "blocked"),
            "clarify": ("More context needed", "blocked"), "refused": ("Outside scope", "blocked")}.get(status, (status, "blocked"))


def active_response(messages: list[dict], selected: str | None) -> dict | None:
    answers = [m["result"] for m in messages if m["role"] == "assistant"]
    return next((r for r in answers if r["trace_id"] == selected), answers[-1] if answers else None)


def cited_sources(result: dict) -> list[dict]:
    labels = set(re.findall(r"\[(S\d+)\]", result["answer"]))
    return [s for s in result["sources"] if s["label"] in labels] or result["sources"]
