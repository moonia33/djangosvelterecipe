"""Upstash Search integracija receptų indeksavimui.

Tikslas:
- Indeksuojami tik publikuoti receptai (`published_at` nustatytas).
- Dokumento dydis turi būti nedidelis: NEįtraukiame `steps`.
- Klaidos indeksuojant neturi blokuoti recepto išsaugojimo (log + continue).

Šis modulis sąmoningai neturi jokių signalų registracijos – tai daroma per
`recipes.signals` ir `RecipesConfig.ready()`.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

from django.conf import settings
from django.db.models import QuerySet
from django.utils.html import strip_tags

from upstash_search import Search

from .models import Recipe

logger = logging.getLogger(__name__)


def _recipe_document_id(recipe_id: int) -> str:
    return f"recipe:{recipe_id}"


def _is_enabled() -> bool:
    if not getattr(settings, "UPSTASH_SEARCH_ENABLED", True):
        return False
    return bool(os.environ.get("UPSTASH_SEARCH_REST_URL")) and bool(
        os.environ.get("UPSTASH_SEARCH_REST_TOKEN")
    )


def is_enabled() -> bool:
    """Ar Upstash Search integracija įjungta ir turi kredencialus."""

    return _is_enabled()


def parse_recipe_id(document_id: str) -> int | None:
    """Iš Upstash dokumento id bando ištraukti recipe_id.

    Tikimės formato: "recipe:<id>".
    """

    if not isinstance(document_id, str):
        return None
    if not document_id.startswith("recipe:"):
        return None
    raw = document_id.removeprefix("recipe:").strip()
    try:
        return int(raw)
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _client() -> Search:
    # Naudojame iš env, kad nereikėtų dubliuoti secret'ų settings faile.
    # Taip pat išjungiam telemetry.
    return Search.from_env(allow_telemetry=False)


def _index_name() -> str:
    return getattr(settings, "UPSTASH_SEARCH_INDEX", "recipes")


def _as_text(value: str | None) -> str:
    return (value or "").strip()


def _compact_join(values: list[str]) -> str:
    items = [v.strip() for v in values if v and v.strip()]
    return ", ".join(items)


def _published_recipe_queryset() -> QuerySet[Recipe]:
    return (
        Recipe.objects.filter(published_at__isnull=False)
        .prefetch_related(
            "tags",
            "categories",
            "cuisines",
            "meal_types",
            "cooking_methods",
            "recipe_ingredients__ingredient",
        )
    )


def build_recipe_document(recipe: Recipe) -> dict[str, Any]:
    """Sukuria Upstash dokumentą pagal receptą.

    Pastaba: receptas privalo būti publikuotas.
    """

    title = _as_text(recipe.title)

    # Aprašymą laikome tekstinį + HTML'ą paverčiam tekstu (be tagų), kad
    # paieška būtų švari ir dokumentas nebūtų per didelis.
    description_text = _as_text(recipe.description)
    description_html_text = _as_text(strip_tags(recipe.description_html))

    ingredients = [
        ri.ingredient.name
        for ri in recipe.recipe_ingredients.all()
        if getattr(ri, "ingredient", None) is not None
    ]

    cuisines = [c.name for c in recipe.cuisines.all()]
    categories = [c.name for c in recipe.categories.all()]
    tags = [t.name for t in recipe.tags.all()]

    content: dict[str, Any] = {
        "title": title,
        "description": description_text,
        "description_html": description_html_text,
        "ingredients": _compact_join(ingredients),
        "cuisines": _compact_join(cuisines),
        "categories": _compact_join(categories),
        "tags": _compact_join(tags),
    }

    metadata: dict[str, Any] = {
        "recipe_id": recipe.id,
        "slug": recipe.slug,
        "difficulty": recipe.difficulty,
        "preparation_time": recipe.preparation_time,
        "cooking_time": recipe.cooking_time,
        "servings": recipe.servings,
        "published_at": recipe.published_at.isoformat() if recipe.published_at else None,
    }

    return {
        "id": _recipe_document_id(recipe.id),
        "content": content,
        "metadata": metadata,
    }


def upsert_recipe(recipe_id: int) -> None:
    """Upsert'ina receptą į Upstash Search, jei publikuotas.

    Jei receptas nepublikuotas arba nerastas – dokumentą pašalina.
    """

    if not _is_enabled():
        return

    try:
        recipe = _published_recipe_queryset().filter(id=recipe_id).first()
        index = _client().index(_index_name())

        if recipe is None:
            index.delete(ids=[_recipe_document_id(recipe_id)])
            return

        doc = build_recipe_document(recipe)
        index.upsert(documents=[doc])

    except Exception:
        logger.exception(
            "Upstash Search: nepavyko upsert'inti recepto (recipe_id=%s)", recipe_id)


def delete_recipe(recipe_id: int) -> None:
    """Pašalina recepto dokumentą iš Upstash Search."""

    if not _is_enabled():
        return

    try:
        index = _client().index(_index_name())
        index.delete(ids=[_recipe_document_id(recipe_id)])
    except Exception:
        logger.exception(
            "Upstash Search: nepavyko ištrinti recepto (recipe_id=%s)", recipe_id)


def search_recipe_ids(query: str, *, limit: int = 10) -> list[int] | None:
    """Grąžina receptų ID iš Upstash pagal užklausą.

    Pastabos:
    - Upstash index'e laikome tik publikuotus receptus, todėl rezultatai yra publikuoti.
    - Jei integracija išjungta arba įvyksta klaida – grąžina `None`.
    """

    if not _is_enabled():
        return None

    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    try:
        index = _client().index(_index_name())
        scores = index.search(cleaned_query, limit=limit)

        ids: list[int] = []
        seen: set[int] = set()
        for item in scores:
            recipe_id = parse_recipe_id(getattr(item, "id", ""))
            if recipe_id is None or recipe_id in seen:
                continue
            ids.append(recipe_id)
            seen.add(recipe_id)
        return ids
    except Exception:
        logger.exception("Upstash Search: nepavyko atlikti paieškos")
        return None
