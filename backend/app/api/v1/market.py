from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import require_farmer_or_admin
from app.services.market_price_service import MarketPriceError, ReportNotFoundError, market_price_service


router = APIRouter(prefix="/market", tags=["Market Prices"])


@router.get("/prices")
async def get_market_prices(
    report_date: Optional[date] = Query(None, description="Report date (YYYY-MM-DD). Defaults to the latest published report."),
    current_user: dict = Depends(require_farmer_or_admin),
):
    """
    Returns wholesale and retail prices for selected food commodities at
    Pettah (Manning), Dambulla, Narahenpita and other economic centers,
    parsed from the CBSL Daily Price Report.
    """
    try:
        return await market_price_service.get_report(report_date)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except MarketPriceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
