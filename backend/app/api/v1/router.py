from fastapi import APIRouter

from app.api.v1.endpoints import auth, buses, tickets, passes, admin, fleet

api_router = APIRouter()

# ── Mount all endpoint routers ────────────────────────────────────────────────
api_router.include_router(auth.router)
api_router.include_router(buses.router)
api_router.include_router(tickets.router)
api_router.include_router(passes.router)
api_router.include_router(admin.router)
api_router.include_router(fleet.router)