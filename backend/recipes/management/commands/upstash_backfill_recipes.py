from __future__ import annotations

from django.core.management.base import BaseCommand

from recipes.models import Recipe
from recipes.upstash_search import upsert_recipe


class Command(BaseCommand):
    help = "Backfill'inti publikuotus receptus į Upstash Search indeksą."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipe-id",
            type=int,
            default=None,
            help="Jei nurodyta, backfill'inamas tik vienas receptas.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maksimalus publikuotų receptų kiekis (naudinga testui).",
        )

    def handle(self, *args, **options):
        recipe_id = options.get("recipe_id")
        limit = options.get("limit")

        if recipe_id:
            self.stdout.write(f"Upstash backfill: recipe_id={recipe_id}")
            upsert_recipe(recipe_id)
            self.stdout.write(self.style.SUCCESS("OK"))
            return

        qs = Recipe.objects.filter(published_at__isnull=False).order_by("id")
        if limit:
            qs = qs[:limit]

        total = qs.count() if limit else None
        processed = 0

        self.stdout.write(
            "Upstash backfill: start" +
            (f" (max={total})" if total is not None else "")
        )

        for recipe_pk in qs.values_list("id", flat=True).iterator(chunk_size=200):
            upsert_recipe(int(recipe_pk))
            processed += 1
            if processed % 100 == 0:
                self.stdout.write(f"Upstash backfill: {processed}...")

        self.stdout.write(self.style.SUCCESS(
            f"Upstash backfill: done ({processed})"))
