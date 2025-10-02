from django.contrib import admin
from .models import Showcase, Card, Logo
from django.utils.html import format_html


@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "preview")

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:40px"/>', obj.image.url)
        return "-"
    preview.short_description = "Превью"

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "showcase", "price", "active", "logo_preview")

    def logo_preview(self, obj):
        if obj.logo and obj.logo.image:
            return format_html('<img src="{}" style="max-height:40px"/>', obj.logo.image.url)
        return "-"
    logo_preview.short_description = "Логотип"