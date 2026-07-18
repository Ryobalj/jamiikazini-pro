# businesses/translation.py

from modeltranslation.translator import register, TranslationOptions
from businesses.models.category import BusinessCategory
from businesses.models.product_category import ProductCategory


@register(BusinessCategory)
class BusinessCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(ProductCategory)
class ProductCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')