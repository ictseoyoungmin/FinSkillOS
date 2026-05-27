"""Warm the symbol logo cache for common Nasdaq/sector universes."""

from __future__ import annotations

# ruff: noqa: E402
import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.config import get_settings
from finskillos.db.repositories import SymbolLogoRepository
from finskillos.db.session import session_scope
from finskillos.services.symbol_logo_service import (
    LOGO_DEV_PROVIDER,
    logo_dev_ticker_url,
)

NASDAQ_100_TICKERS = (
    "NVDA",
    "GOOGL",
    "GOOG",
    "AAPL",
    "MSFT",
    "AMZN",
    "AVGO",
    "TSLA",
    "META",
    "MU",
    "WMT",
    "AMD",
    "ASML",
    "INTC",
    "CSCO",
    "COST",
    "LRCX",
    "NFLX",
    "AMAT",
    "ARM",
    "PLTR",
    "TXN",
    "KLAC",
    "QCOM",
    "LIN",
    "PANW",
    "TMUS",
    "ADI",
    "PEP",
    "STX",
    "MRVL",
    "AMGN",
    "WDC",
    "APP",
    "CRWD",
    "GILD",
    "ISRG",
    "HON",
    "PDD",
    "SHOP",
    "BKNG",
    "SBUX",
    "VRTX",
    "CEG",
    "CDNS",
    "SNPS",
    "MAR",
    "FTNT",
    "ADBE",
    "CMCSA",
    "ADP",
    "CSX",
    "MNST",
    "NXPI",
    "MELI",
    "INTU",
    "MPWR",
    "DDOG",
    "ABNB",
    "MDLZ",
    "ROST",
    "ORLY",
    "AEP",
    "CTAS",
    "WBD",
    "DASH",
    "BKR",
    "REGN",
    "PCAR",
    "MSTR",
    "FANG",
    "MCHP",
    "FAST",
    "EA",
    "XEL",
    "ADSK",
    "FER",
    "EXC",
    "ODFL",
    "IDXX",
    "CCEP",
    "TTWO",
    "KDP",
    "ALNY",
    "PYPL",
    "TRI",
    "PAYX",
    "ROP",
    "CPRT",
    "AXON",
    "WDAY",
    "ZS",
    "GEHC",
    "KHC",
    "DXCM",
    "CTSH",
    "INSM",
    "VRSK",
    "TEAM",
    "CHTR",
    "CSGP",
)

AI_TICKERS = (
    "NVDA",
    "MSFT",
    "GOOGL",
    "GOOG",
    "AMZN",
    "META",
    "AVGO",
    "AMD",
    "ARM",
    "PLTR",
    "APP",
    "CRWD",
    "DDOG",
    "SNPS",
    "CDNS",
    "MRVL",
    "MU",
    "ADBE",
    "ADSK",
    "PANW",
    "FTNT",
    "ZS",
    "TEAM",
    "WDAY",
    "MSTR",
    "INTU",
)

AEROSPACE_AIR_TICKERS = (
    "HON",
    "AXON",
    "RKLB",
    "LUNR",
    "ASTS",
    "IRDM",
    "SATS",
    "AVAV",
    "KTOS",
    "MRCY",
    "AAL",
    "UAL",
    "ALK",
    "JBLU",
    "ULCC",
)

QUANTUM_TICKERS = (
    "RGTI",
    "QUBT",
    "ARQQ",
    "QSI",
    "LAES",
    "QMCO",
)


@dataclass(frozen=True)
class SeedResult:
    ticker: str
    status: str
    detail: str = ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Logo.dev ticker image URLs and cache them in DB."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Revalidate and overwrite rows already present in symbol_logo_cache.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-symbol HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if settings.logo_provider != LOGO_DEV_PROVIDER or not settings.logo_dev_token:
        raise SystemExit(
            "Set FINSKILLOS_LOGO_PROVIDER=logo_dev and FINSKILLOS_LOGO_DEV_TOKEN "
            "or LOGO_DEV_PUBLISHABLE_KEY before seeding logos."
        )

    tickers = _logo_seed_universe()
    with session_scope() as session:
        repo = SymbolLogoRepository(session)
        results = [
            _seed_one(
                repo,
                ticker,
                token=settings.logo_dev_token,
                force=args.force,
                timeout=args.timeout,
            )
            for ticker in tickers
        ]
        session.commit()

    summary = _summary(results)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "Logo seed summary: "
            f"{summary['stored']} stored, "
            f"{summary['cached']} already cached, "
            f"{summary['failed']} failed, "
            f"{summary['total']} total"
        )
        if summary["failedTickers"]:
            print("Failed tickers:", ", ".join(summary["failedTickers"]))
    return 0 if summary["stored"] or summary["cached"] else 1


def _seed_one(
    repo: SymbolLogoRepository,
    ticker: str,
    *,
    token: str,
    force: bool,
    timeout: float,
) -> SeedResult:
    if not force and repo.get(ticker) is not None:
        return SeedResult(ticker=ticker, status="cached")

    logo_url = logo_dev_ticker_url(ticker, token)
    ok, detail = _validate_logo_url(logo_url, timeout=timeout)
    if not ok:
        return SeedResult(ticker=ticker, status="failed", detail=detail)

    repo.upsert_provider_logo(
        ticker,
        provider=LOGO_DEV_PROVIDER,
        logo_url=logo_url,
    )
    return SeedResult(ticker=ticker, status="stored")


def _validate_logo_url(logo_url: str, *, timeout: float) -> tuple[bool, str]:
    request = Request(
        logo_url,
        method="GET",
        headers={
            "Accept": "image/*",
            "Range": "bytes=0-0",
            "User-Agent": "FinSkillOS/1.0 logo-cache-seed",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "").lower()
            if response.status not in {200, 206}:
                return False, f"http_{response.status}"
            if "image" not in content_type:
                return False, "non_image_response"
            return True, "ok"
    except HTTPError as exc:
        return False, f"http_{exc.code}"
    except URLError as exc:
        return False, exc.reason.__class__.__name__
    except TimeoutError:
        return False, "timeout"


def _logo_seed_universe() -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *NASDAQ_100_TICKERS,
                *AI_TICKERS,
                *AEROSPACE_AIR_TICKERS,
                *QUANTUM_TICKERS,
            ]
        )
    )


def _summary(results: list[SeedResult]) -> dict:
    return {
        "total": len(results),
        "stored": sum(1 for result in results if result.status == "stored"),
        "cached": sum(1 for result in results if result.status == "cached"),
        "failed": sum(1 for result in results if result.status == "failed"),
        "failedTickers": [
            result.ticker for result in results if result.status == "failed"
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
