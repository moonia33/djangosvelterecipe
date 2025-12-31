"""Admino registracijos."""

from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from django import forms

from recipes import models


class RecipeAdminForm(forms.ModelForm):
    """Papildomi laukų widget'ai (HTML editorius)."""

    description_html = forms.CharField(
        label="Rodymas HTML",
        widget=CKEditorWidget(),
        required=False,
    )

    class Meta:
        model = models.Recipe
        fields = "__all__"


class RecipeStepInlineForm(forms.ModelForm):
    description_html = forms.CharField(
        label="Žingsnio HTML",
        widget=CKEditorWidget(),
        required=False,
    )

    class Meta:
        model = models.RecipeStep
        fields = "__all__"


class RecipeIngredientInline(admin.TabularInline):
    """Greitas ingredientų redagavimas receptų formoje."""

    model = models.RecipeIngredient
    extra = 0


class RecipeStepInline(admin.StackedInline):
    """Žingsnių redagavimas admino sąsajoje."""

    model = models.RecipeStep
    form = RecipeStepInlineForm
    extra = 0
    ordering = ("order",)
    fieldsets = (
        ("Bazinė informacija", {"fields": ("order", "title", "duration")}),
        (
            "Turinys",
            {"fields": ("description", "description_html",
                        "image", "video_url")},
        ),
    )


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    list_display = ("title", "difficulty", "published_at", "updated_at")
    list_filter = ("difficulty", "published_at", "meal_types", "cuisines")
    search_fields = ("title", "description", "meta_description")
    autocomplete_fields = ("categories", "tags", "cuisines",
                           "meal_types", "cooking_methods")
    inlines = [RecipeIngredientInline, RecipeStepInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name",)
    list_filter = ("category",)


@admin.register(models.IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(models.RecipeCategory)
class RecipeCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(models.MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "unit_type")
    list_filter = ("unit_type",)


@admin.register(models.MealType, models.Cuisine, models.CookingMethod, models.Tag)
class SimpleLookupAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(models.RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount", "unit")
    search_fields = ("recipe__title", "ingredient__name")


@admin.register(models.RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ("recipe", "order", "title")
    ordering = ("recipe", "order")


@admin.register(models.Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "created_at")
    search_fields = ("user__email", "recipe__title")


@admin.register(models.Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe", "value")
    search_fields = ("user__email", "recipe__title")


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("recipe", "user", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("content", "user__email", "recipe__title")
    actions = ["approve_comments"]

    @admin.action(description="Pažymėti kaip patvirtintus")
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
