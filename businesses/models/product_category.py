# businesses/models/product_category.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from kiini.models.base import UUIDModel, TimeStampedModel


class ProductCategory(UUIDModel, TimeStampedModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Category Name"),
        help_text=_("Jina la aina ya bidhaa, mfano: Vyakula, Vinywaji, Nguo.")
    )
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier, mfano: vyakula, vinywaji.")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Maelezo ya ziada kuhusu aina hii ya bidhaa.")
    )
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def parent_name(self):
        return self.parent.name if self.parent else '---'
    parent_name.fget.short_description = "Parent Category"

    def children_count(self):
        return self.subcategories.count()
