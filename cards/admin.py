
from django.contrib import admin
from .models import Card

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id","title","price","order_index","active")
    list_editable = ("order_index","active")
    search_fields = ("title",)
    list_filter = ("active",)
