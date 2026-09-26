"""
Market Price Service

Fetches the Central Bank of Sri Lanka (CBSL) "Daily Price Report" PDF and parses
the "Wholesale and Retail Prices: Selected Food Commodities" table into JSON.

Source: https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report
Reports are published on working days, so the latest available report is found
by walking back from today (Sri Lanka time) until a published PDF is found.
"""
import asyncio
import io
import re
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from pypdf import PdfReader

from app.core.logging_config import logger


REPORT_URL = (
    "https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/"
    "statistics/pricerpt/price_report_{ymd}_e.pdf"
)
SOURCE_PAGE = "https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report"

SL_TZ = timezone(timedelta(hours=5, minutes=30))
MAX_LOOKBACK_DAYS = 10
LATEST_CACHE_TTL = 30 * 60  # seconds
HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=20.0, write=10.0, pool=5.0)

# Column order of the 10 price columns (Yesterday/Today pairs) in the table.
# The rice and fish sections reuse the same columns for different markets.
DEFAULT_COLUMNS = [
    ("wholesale", "Pettah"),
    ("wholesale", "Dambulla"),
    ("retail", "Pettah"),
    ("retail", "Dambulla"),
    ("retail", "Narahenpita"),
]
SECTION_COLUMNS = {
    "RICE": [
        ("wholesale", "Pettah"),
        ("wholesale", "Marandagahamula"),
        ("retail", "Pettah"),
        ("retail", "Dambulla"),
        ("retail", "Narahenpita"),
    ],
    "FISH": [
        ("wholesale", "Peliyagoda"),
        ("wholesale", "Negombo"),
        ("retail", "Pettah"),
        ("retail", "Negombo"),
        ("retail", "Narahenpita"),
    ],
}
SECTIONS = {"VEGETABLES", "OTHER", "FRUITS", "RICE", "FISH"}

_NUM_RE = re.compile(r"n\.a\.|[\d,]+\.\d{2}")
_ROW_RE = re.compile(r"^(\S.*?)\s{2,}(Rs\./\w+)\s")


class MarketPriceError(Exception):
    """Raised when the price report cannot be fetched or parsed."""


class ReportNotFoundError(MarketPriceError):
    """Raised when no report is published for the requested date(s)."""


def _parse_number(token: str) -> Optional[float]:
    return None if token == "n.a." else float(token.replace(",", ""))


def _change_pct(yesterday: Optional[float], today: Optional[float]) -> Optional[float]:
    if yesterday in (None, 0) or today is None:
        return None
    return round((today - yesterday) / yesterday * 100, 1)


def parse_price_report(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """
    Parse the commodity price table out of a CBSL daily price report PDF.

    Numbers are assigned to columns by their horizontal position relative to the
    "Yesterday"/"Today" header labels, so empty cells don't shift values.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    page = next(
        (p for p in reader.pages if "Wholesale and Retail Prices" in (p.extract_text() or "")),
        None,
    )
    if page is None:
        raise MarketPriceError("Price table page not found in report")

    lines = page.extract_text(extraction_mode="layout").splitlines()
    header = next((l for l in lines if l.count("Yesterday") == 5), None)
    if header is None:
        raise MarketPriceError("Price table header not found in report")
    centers = [m.start() + len(m.group()) / 2 for m in re.finditer(r"Yesterday|Today", header)]

    items: list[dict[str, Any]] = []
    section = None
    for line in lines:
        compact = line.replace(" ", "")
        if compact in SECTIONS:
            section = compact
            continue
        row = _ROW_RE.match(line)
        if not row or section is None:
            continue

        values: list[Optional[float]] = [None] * len(centers)
        for tok in _NUM_RE.finditer(line, row.end()):
            mid = (tok.start() + tok.end()) / 2
            col = min(range(len(centers)), key=lambda k: abs(centers[k] - mid))
            values[col] = _parse_number(tok.group())

        prices = []
        for i, (price_type, market) in enumerate(SECTION_COLUMNS.get(section, DEFAULT_COLUMNS)):
            yesterday, today = values[2 * i], values[2 * i + 1]
            if yesterday is None and today is None:
                continue
            prices.append({
                "market": market,
                "type": price_type,
                "yesterday": yesterday,
                "today": today,
                "change_pct": _change_pct(yesterday, today),
            })

        if prices:
            items.append({
                "name": row.group(1).strip(),
                "category": section.title(),
                "unit": row.group(2),
                "prices": prices,
            })

    if not items:
        raise MarketPriceError("No commodity rows parsed from report")
    return items


class MarketPriceService:
    def __init__(self) -> None:
        self._reports: dict[date, dict[str, Any]] = {}
        self._missing: dict[date, float] = {}
        self._latest: Optional[tuple[float, date]] = None
        self._lock = asyncio.Lock()

    async def _fetch_report(self, client: httpx.AsyncClient, day: date) -> Optional[dict[str, Any]]:
        if day in self._reports:
            return self._reports[day]
        missing_at = self._missing.get(day)
        if missing_at and time.time() - missing_at < LATEST_CACHE_TTL:
            return None

        url = REPORT_URL.format(ymd=day.strftime("%Y%m%d"))
        response = await client.get(url)
        if response.status_code == 404 or not response.content.startswith(b"%PDF"):
            self._missing[day] = time.time()
            return None
        response.raise_for_status()

        items = await asyncio.to_thread(parse_price_report, response.content)
        report = {
            "report_date": day.isoformat(),
            "source": "Central Bank of Sri Lanka - Daily Price Report",
            "source_url": url,
            "source_page": SOURCE_PAGE,
            "currency": "LKR",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
        }
        self._reports[day] = report
        logger.info("Parsed CBSL price report for %s (%d items)", day, len(items))
        return report

    async def get_report(self, day: Optional[date] = None) -> dict[str, Any]:
        """
        Return the report for `day`, or the latest published report when `day` is None.
        """
        async with self._lock:
            try:
                async with httpx.AsyncClient(
                    timeout=HTTP_TIMEOUT,
                    follow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0 (AgriKetha-AI Market Advisor)"},
                ) as client:
                    if day is not None:
                        report = await self._fetch_report(client, day)
                        if report is None:
                            raise ReportNotFoundError(f"No price report published for {day.isoformat()}")
                        return report

                    if self._latest and time.time() - self._latest[0] < LATEST_CACHE_TTL:
                        return self._reports[self._latest[1]]

                    today = datetime.now(SL_TZ).date()
                    for offset in range(MAX_LOOKBACK_DAYS):
                        candidate = today - timedelta(days=offset)
                        report = await self._fetch_report(client, candidate)
                        if report is not None:
                            self._latest = (time.time(), candidate)
                            return report
            except httpx.HTTPError as exc:
                logger.error("Failed to fetch CBSL price report: %s", exc)
                if day is None and self._latest:
                    return self._reports[self._latest[1]]
                raise MarketPriceError("Price report source is currently unreachable") from exc

        raise ReportNotFoundError(f"No price report found in the last {MAX_LOOKBACK_DAYS} days")


market_price_service = MarketPriceService()
