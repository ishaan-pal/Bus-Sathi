from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.dependencies import get_db, get_current_admin
from app.models.user import User
from app.models.bus import Bus, BusStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.pass_ import BusPass, PassStatus
from app.models.route import Route
from app.schemas.user import UserListResponse, UpdateUserRequest

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Dashboard Stats ───────────────────────────────────────────────────────────
@router.get(
    "/dashboard",
    summary="[Admin] Get dashboard statistics",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Returns key metrics for the admin dashboard:
    - Total users, buses, tickets, passes
    - Active buses on road right now
    - Pending pass applications
    - Revenue today
    """
    # User count
    user_count = await db.scalar(
        select(func.count()).select_from(User).where(User.is_active == True)
    )

    # Bus counts
    total_buses = await db.scalar(
        select(func.count()).select_from(Bus).where(Bus.is_active == True)
    )
    active_buses = await db.scalar(
        select(func.count()).select_from(Bus).where(
            Bus.status.in_([BusStatus.RUNNING, BusStatus.DELAYED])
        )
    )

    # Ticket counts
    total_tickets = await db.scalar(
        select(func.count()).select_from(Ticket)
    )
    active_tickets = await db.scalar(
        select(func.count()).select_from(Ticket).where(
            Ticket.status == TicketStatus.ACTIVE
        )
    )

    # Revenue today (sum of paid tickets today)
    from datetime import date
    today = date.today().isoformat()
    today_revenue = await db.scalar(
        select(func.sum(Ticket.total_fare_paise)).where(
            Ticket.journey_date == today,
            Ticket.payment_verified == True,
        )
    )
    today_revenue_rupees = round((today_revenue or 0) / 100, 2)

    # Pass counts
    total_passes = await db.scalar(
        select(func.count()).select_from(BusPass)
    )
    pending_passes = await db.scalar(
        select(func.count()).select_from(BusPass).where(
            BusPass.status.in_([
                PassStatus.SUBMITTED,
                PassStatus.VERIFICATION_PENDING,
            ])
        )
    )

    # Route count
    route_count = await db.scalar(
        select(func.count()).select_from(Route).where(Route.is_active == True)
    )

    return {
        "success": True,
        "stats": {
            "users": {
                "total": user_count,
            },
            "buses": {
                "total": total_buses,
                "active_on_road": active_buses,
                "in_depot": total_buses - active_buses,
            },
            "tickets": {
                "total": total_tickets,
                "active": active_tickets,
                "today_revenue_rupees": today_revenue_rupees,
            },
            "passes": {
                "total": total_passes,
                "pending_review": pending_passes,
            },
            "routes": {
                "total": route_count,
            },
        },
    }


# ── User Management ───────────────────────────────────────────────────────────
@router.get(
    "/users",
    response_model=list[UserListResponse],
    summary="[Admin] List all users",
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    search: str = Query(None, description="Search by mobile or name"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List all registered users with optional search."""
    query = select(User).order_by(User.created_at.desc())

    if search:
        query = query.where(
            User.mobile.ilike(f"%{search}%")
            | User.name.ilike(f"%{search}%")
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return [
        UserListResponse(
            id=u.id,
            mobile=u.mobile,
            name=u.name,
            aadhaar_verified=u.aadhaar_verified,
            profile_complete=u.profile_complete,
            is_active=u.is_active,
            is_admin=u.is_admin,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.patch(
    "/users/{user_id}",
    summary="[Admin] Update user account",
)
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Update user account details — activate/deactivate, grant admin."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.name is not None:
        user.name = body.name
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.is_admin is not None:
        user.is_admin = body.is_admin

    await db.commit()
    return {"success": True, "message": "User updated"}


# ── Route Management ──────────────────────────────────────────────────────────
@router.get(
    "/routes",
    summary="[Admin] List all routes",
)
async def admin_list_routes(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """List all routes for admin management."""
    result = await db.execute(
        select(Route).order_by(Route.route_number)
    )
    routes = result.scalars().all()

    return {
        "success": True,
        "total": len(routes),
        "routes": [
            {
                "id": r.id,
                "route_number": r.route_number,
                "name": r.name,
                "origin": r.origin,
                "destination": r.destination,
                "total_distance_km": r.total_distance_km,
                "estimated_duration_minutes": r.estimated_duration_minutes,
                "is_active": r.is_active,
            }
            for r in routes
        ],
    }


@router.patch(
    "/routes/{route_id}/toggle",
    summary="[Admin] Toggle route active status",
)
async def toggle_route(
    route_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Activate or deactivate a route."""
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found",
        )
    route.is_active = not route.is_active
    await db.commit()
    return {
        "success": True,
        "route_number": route.route_number,
        "is_active": route.is_active,
    }


# ── Live Bus Monitor ──────────────────────────────────────────────────────────
@router.get(
    "/monitor/live",
    summary="[Admin] Live bus monitor",
)
async def live_bus_monitor(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Real-time overview of all buses currently on road.
    Shows location, status, delay, and route for each bus.
    """
    result = await db.execute(
        select(Bus).where(
            Bus.status.in_([BusStatus.RUNNING, BusStatus.DELAYED, BusStatus.STOPPED])
        ).order_by(Bus.bus_number)
    )
    buses = result.scalars().all()

    bus_list = []
    for bus in buses:
        route_number = None
        if bus.route_id:
            r = await db.execute(
                select(Route.route_number).where(Route.id == bus.route_id)
            )
            route_number = r.scalar_one_or_none()

        bus_list.append({
            "bus_id": bus.id,
            "bus_number": bus.bus_number,
            "status": bus.status.value,
            "delay_minutes": bus.delay_minutes,
            "eta_display": bus.eta_display,
            "current_stop": bus.current_stop,
            "next_stop": bus.next_stop,
            "latitude": bus.current_latitude,
            "longitude": bus.current_longitude,
            "last_updated": (
                bus.last_location_update.isoformat()
                if bus.last_location_update else None
            ),
            "is_stale": bus.is_location_stale,
            "route_number": route_number,
            "driver_name": bus.driver_name,
            "conductor_name": bus.conductor_name,
        })

    return {
        "success": True,
        "total_active": len(bus_list),
        "buses": bus_list,
    }