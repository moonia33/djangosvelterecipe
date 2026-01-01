"""Signalai Upstash Search indeksavimui.

Principai:
- Indeksuojam tik publikuotus receptus.
- Po bet kokio recepto / ingredientų / M2M pasikeitimo perindeksuojam receptą.
- Darom per `transaction.on_commit`, kad indeksuotume tik sėkmingai išsaugotą būseną.
- Upstash klaidos neturi blokuoti įrašymo.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .models import Recipe, RecipeIngredient
from .upstash_search import delete_recipe, upsert_recipe


def _schedule_upsert(recipe_id: int) -> None:
    transaction.on_commit(lambda: upsert_recipe(recipe_id))


def _schedule_delete(recipe_id: int) -> None:
    transaction.on_commit(lambda: delete_recipe(recipe_id))


@receiver(post_save, sender=Recipe, dispatch_uid="recipes.upstash.recipe_post_save")
def _recipe_post_save(sender, instance: Recipe, **kwargs) -> None:
    # Upsert funkcija pati nuspręs: jei nepublikuota – delete.
    _schedule_upsert(instance.id)


@receiver(post_delete, sender=Recipe, dispatch_uid="recipes.upstash.recipe_post_delete")
def _recipe_post_delete(sender, instance: Recipe, **kwargs) -> None:
    _schedule_delete(instance.id)


@receiver(post_save, sender=RecipeIngredient, dispatch_uid="recipes.upstash.recipeingredient_post_save")
def _recipeingredient_post_save(sender, instance: RecipeIngredient, **kwargs) -> None:
    _schedule_upsert(instance.recipe_id)


@receiver(
    post_delete,
    sender=RecipeIngredient,
    dispatch_uid="recipes.upstash.recipeingredient_post_delete",
)
def _recipeingredient_post_delete(sender, instance: RecipeIngredient, **kwargs) -> None:
    _schedule_upsert(instance.recipe_id)


@receiver(
    m2m_changed,
    sender=Recipe.tags.through,
    dispatch_uid="recipes.upstash.recipe_tags_m2m_changed",
)
@receiver(
    m2m_changed,
    sender=Recipe.categories.through,
    dispatch_uid="recipes.upstash.recipe_categories_m2m_changed",
)
@receiver(
    m2m_changed,
    sender=Recipe.cuisines.through,
    dispatch_uid="recipes.upstash.recipe_cuisines_m2m_changed",
)
def _recipe_m2m_changed(sender, instance: Recipe, action: str, **kwargs) -> None:
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    _schedule_upsert(instance.id)
