from .common import router as common_router
from .booking import router as booking_router
from .info import router as info_router
from .contact import router as contact_router
from .admin_bookings import router as admin_bookings_router
from .admin_manage import router as admin_manage_router
from .admin_broadcast import router as admin_broadcast_router

__all__ = [
    "common_router",
    "booking_router",
    "info_router",
    "contact_router",
    "admin_bookings_router",
    "admin_manage_router",
    "admin_broadcast_router",
]
