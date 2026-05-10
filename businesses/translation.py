# businesses/translation.py

from modeltranslation.translator import register, TranslationOptions
from businesses.models.category import BusinessCategory


@register(BusinessCategory)
class BusinessCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')