from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import httpx
import asyncio
import time
import json
import logging
import redis.asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather_app")

app = FastAPI(title="Medical Reports + Weather (with caching & rate-limiting)")

# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # seconds
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # requests
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Async Redis client (single shared client)
redis_client: aioredis.Redis | None = None

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Mount frontend static files (expects build output at the given path)
FRONTEND_DIST = os.getenv("FRONTEND_DIST", "frontend/dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/weather", StaticFiles(directory=FRONTEND_DIST, html=True), name="weather")
else:
    logger.warning("Frontend dist not found at %s — /weather route will not be available until you build the frontend.", FRONTEND_DIST)


@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    # simple ping to check connection (don't fail startup if redis not ready)
    try:
        await redis_client.ping()
        logger.info("Connected to Redis: %s", REDIS_URL)
    except Exception as e:
        logger.warning("Could not connect to Redis at %s: %s", REDIS_URL, e)


@app.on_event("shutdown")
async def shutdown_event():
    global redis_client
    if redis_client:
        await redis_client.close()


def _get_client_ip(request: Request) -> str:
    # Try common headers first (behind proxies), fall back to connection client
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # x-forwarded-for may contain multiple ips
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_rate_limit(ip: str) -> None:
    """Simple fixed-window counter rate limiter using Redis INCR + EXPIRE.
    Raises HTTPException(429) when exceeded.
    """
    if not redis_client:
        # If no redis, fail open (allow requests) but log warning
        logger.warning("Redis is not available; skipping rate limiting (fail-open).")
        return

    key = f"rl:{ip}"
    try:
        # INCR the counter
        current = await redis_client.incr(key)
        if current == 1:
            # set expiration if first increment
            await redis_client.expire(key, RATE_LIMIT_WINDOW)
        if current > RATE_LIMIT:
            ttl = await redis_client.ttl(key)
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry in {ttl} seconds.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Rate limiting check failed: %s", e)
        # fail-open on Redis error
        return


async def _get_cached(city_key: str):
    if not redis_client:
        return None
    try:
        data = await redis_client.get(city_key)
        if not data:
            return None
        return json.loads(data)
    except Exception as e:
        logger.exception("Failed to get cache for %s: %s", city_key, e)
        return None


async def _set_cache(city_key: str, value, ttl: int):
    if not redis_client:
        return
    try:
        await redis_client.set(city_key, json.dumps(value, ensure_ascii=False), ex=ttl)
    except Exception:
        logger.exception("Failed to set cache for %s", city_key)


@app.get("/api/v1/weather")
async def weather_proxy(request: Request, city: str = Query(..., min_length=1)):
    """Proxy endpoint that returns geocoding + forecast. Implements caching and simple per-IP rate-limiting.
    Example: GET /api/v1/weather?city=Riyadh
    """
    ip = _get_client_ip(request)
    await _check_rate_limit(ip)

    city_norm = city.strip().lower()
    cache_key = f"cache:weather:{city_norm}"

    # Try cache first
    cached = await _get_cached(cache_key)
    if cached:
        logger.info("Cache hit for %s (IP=%s)", city_norm, ip)
        return JSONResponse(content={"cached": True, "place": cached.get("place"), "weather": cached.get("weather")})

    logger.info("Cache miss for %s (IP=%s) — fetching from provider", city_norm, ip)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # geocoding
        try:
            gres = await client.get(GEOCODING_URL, params={"name": city, "count": 5})
            gres.raise_for_status()
            geo = gres.json()
        except httpx.HTTPError as e:
            logger.exception("Geocoding request failed: %s", e)
            raise HTTPException(status_code=502, detail="Geocoding provider error")

        if not geo.get("results"):
            raise HTTPException(status_code=404, detail="City not found")

        place = geo["results"][0]
        lat = place["latitude"]
        lon = place["longitude"]

        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "timezone": "auto",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum"
        }

        try:
            wres = await client.get(FORECAST_URL, params=params)
            wres.raise_for_status()
            weather = wres.json()
        except httpx.HTTPError as e:
            logger.exception("Weather request failed: %s", e)
            raise HTTPException(status_code=502, detail="Weather provider error")

    payload = {"place": place, "weather": weather}

    # store in cache
    await _set_cache(cache_key, payload, CACHE_TTL)

    return JSONResponse(content={"cached": False, **payload})


@app.get("/health")
async def health():
    redis_ok = False
    try:
        if redis_client:
            await redis_client.ping()
            redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok", "redis": redis_ok}
