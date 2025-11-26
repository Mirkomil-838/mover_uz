from .user import router as user_router
from .admin import router as admin_router
from .channels import router as channels_router
from .movies import router as movies_router

__all__ = ['user_router', 'admin_router', 'channels_router', 'movies_router']