"""Centrinis Ninja API objektas ir bendri hook'ai."""

from ninja import NinjaAPI

from accounts.api import router as accounts_router
from recipes.api import router as recipes_router
from sitecontent.api import router as sitecontent_router

api = NinjaAPI(
    title="Recipe Platform API",
    version="0.1.0",
    description="Moderni receptų platformos API",
)

api.add_router("/sitecontent", sitecontent_router)
api.add_router("/recipes", recipes_router)
api.add_router("/auth", accounts_router)
