"""
Gold Price Service
Fetches and caches live gold prices from GoldAPI.io
"""

import os
import httpx
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

from app.database import supabase_admin


# =============================================================================
# CONFIGURATION
# =============================================================================

GOLD_API_URL = "https://www.goldapi.io/api/XAU/INR"
CACHE_DURATION_HOURS = 6  # Refresh every 6 hours

# Fallback prices (update periodically)
FALLBACK_PRICES = {
    "24": 14900.0,
    "22": 13650.0,
    "21": 13030.0,
    "20": 12410.0,
    "18": 11170.0,
    "16": 9930.0,
    "14": 8690.0,
    "10": 6200.0,
}


# =============================================================================
# MODELS
# =============================================================================

class GoldPriceData(BaseModel):
    """Gold price data model"""
    price_gram_24k: float
    price_gram_22k: float
    price_gram_21k: float
    price_gram_20k: float
    price_gram_18k: float
    price_gram_16k: float
    price_gram_14k: float
    price_gram_10k: float
    
    # Market data
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    prev_close_price: Optional[float] = None
    change_amount: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Metadata
    fetched_at: Optional[datetime] = None
    source: str = "goldapi.io"
    is_cached: bool = False
    cache_age_hours: Optional[float] = None


# =============================================================================
# SERVICE
# =============================================================================

class GoldPriceService:
    """Service for fetching and caching gold prices"""
    
    def __init__(self):
        self.api_key = os.getenv("GOLD_API_KEY")
    
    async def get_gold_prices(self, force_refresh: bool = False) -> GoldPriceData:
        """
        Get gold prices with caching.
        
        Args:
            force_refresh: If True, bypass cache and fetch live
            
        Returns:
            GoldPriceData with all purity prices
        """
        # 1. Check cache (unless force refresh)
        if not force_refresh:
            cached = await self._get_cached_price()
            if cached:
                return cached

        # 2. Fetch live price
        try:
            live_data = await self._fetch_live_price()

            # 3. Save to cache
            await self._save_to_cache(live_data)

            return live_data

        except Exception as e:
            print(f"Error fetching live gold price: {e}")

            # 4. Return stale cache if available
            stale_cache = await self._get_cached_price(ignore_expiry=True)
            if stale_cache:
                return stale_cache

            # 5. Return fallback
            return self._get_fallback_prices()
    
    async def _get_cached_price(
        self,
        ignore_expiry: bool = False
    ) -> Optional[GoldPriceData]:
        """Get cached price if valid"""
        try:
            result = supabase_admin.table("gold_price_cache") \
                .select("*") \
                .order("fetched_at", desc=True) \
                .limit(1) \
                .execute()
            
            if not result.data:
                return None
            
            cached = result.data[0]
            fetched_at = datetime.fromisoformat(cached["fetched_at"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - fetched_at).total_seconds() / 3600
            
            # Check if expired
            if not ignore_expiry and age_hours > CACHE_DURATION_HOURS:
                return None
            
            return GoldPriceData(
                price_gram_24k=float(cached["price_gram_24k"]),
                price_gram_22k=float(cached["price_gram_22k"]),
                price_gram_21k=float(cached["price_gram_21k"]),
                price_gram_20k=float(cached["price_gram_20k"]),
                price_gram_18k=float(cached["price_gram_18k"]),
                price_gram_16k=float(cached.get("price_gram_16k") or 0),
                price_gram_14k=float(cached["price_gram_14k"]),
                price_gram_10k=float(cached.get("price_gram_10k") or 0),
                open_price=float(cached["open_price"]) if cached.get("open_price") else None,
                high_price=float(cached["high_price"]) if cached.get("high_price") else None,
                low_price=float(cached["low_price"]) if cached.get("low_price") else None,
                prev_close_price=float(cached["prev_close_price"]) if cached.get("prev_close_price") else None,
                change_amount=float(cached["change_amount"]) if cached.get("change_amount") else None,
                change_percent=float(cached["change_percent"]) if cached.get("change_percent") else None,
                fetched_at=fetched_at,
                source=cached.get("source", "cache"),
                is_cached=True,
                cache_age_hours=round(age_hours, 2),
            )
            
        except Exception as e:
            print(f"Error reading cache: {e}")
            return None
    
    async def _fetch_live_price(self) -> GoldPriceData:
        """Fetch live price from GoldAPI"""
        if not self.api_key:
            raise ValueError("GOLD_API_KEY not configured in environment")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOLD_API_URL,
                headers={"x-access-token": self.api_key},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
        
        return GoldPriceData(
            price_gram_24k=data["price_gram_24k"],
            price_gram_22k=data["price_gram_22k"],
            price_gram_21k=data["price_gram_21k"],
            price_gram_20k=data["price_gram_20k"],
            price_gram_18k=data["price_gram_18k"],
            price_gram_16k=data.get("price_gram_16k", data["price_gram_18k"] * 0.889),
            price_gram_14k=data["price_gram_14k"],
            price_gram_10k=data.get("price_gram_10k", data["price_gram_14k"] * 0.714),
            open_price=data.get("open_price"),
            high_price=data.get("high_price"),
            low_price=data.get("low_price"),
            prev_close_price=data.get("prev_close_price"),
            change_amount=data.get("ch"),
            change_percent=data.get("chp"),
            fetched_at=datetime.now(timezone.utc),
            source="goldapi.io",
            is_cached=False,
        )
    
    async def _save_to_cache(self, data: GoldPriceData) -> None:
        """Save price to cache"""
        try:
            supabase_admin.table("gold_price_cache").insert({
                "price_gram_24k": data.price_gram_24k,
                "price_gram_22k": data.price_gram_22k,
                "price_gram_21k": data.price_gram_21k,
                "price_gram_20k": data.price_gram_20k,
                "price_gram_18k": data.price_gram_18k,
                "price_gram_16k": data.price_gram_16k,
                "price_gram_14k": data.price_gram_14k,
                "price_gram_10k": data.price_gram_10k,
                "open_price": data.open_price,
                "high_price": data.high_price,
                "low_price": data.low_price,
                "prev_close_price": data.prev_close_price,
                "change_amount": data.change_amount,
                "change_percent": data.change_percent,
                "source": data.source,
            }).execute()
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def _get_fallback_prices(self) -> GoldPriceData:
        """Return fallback prices when all else fails"""
        return GoldPriceData(
            price_gram_24k=FALLBACK_PRICES["24"],
            price_gram_22k=FALLBACK_PRICES["22"],
            price_gram_21k=FALLBACK_PRICES["21"],
            price_gram_20k=FALLBACK_PRICES["20"],
            price_gram_18k=FALLBACK_PRICES["18"],
            price_gram_16k=FALLBACK_PRICES["16"],
            price_gram_14k=FALLBACK_PRICES["14"],
            price_gram_10k=FALLBACK_PRICES["10"],
            source="fallback",
            is_cached=False,
        )
    
    def get_price_for_purity(self, prices: GoldPriceData, purity: str) -> float:
        """Get price for specific purity"""
        purity_map = {
            "24": prices.price_gram_24k,
            "22": prices.price_gram_22k,
            "21": prices.price_gram_21k,
            "20": prices.price_gram_20k,
            "18": prices.price_gram_18k,
            "16": prices.price_gram_16k,
            "14": prices.price_gram_14k,
            "13": prices.price_gram_14k * 0.928,
            "10": prices.price_gram_10k,
        }
        return purity_map.get(purity, prices.price_gram_22k)


# Singleton instance
gold_price_service = GoldPriceService()