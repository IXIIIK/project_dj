# cards/models.py
from django.db import models

class Showcase(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название витрины")
    slug = models.SlugField(max_length=50, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    domains = models.TextField(blank=True, help_text="Домен(ы) через запятую")

    def __str__(self):
        return self.name or f"Витрина {self.pk}"

class Card(models.Model):
    # 👇 новое поле
    showcase = models.ForeignKey(
        Showcase, on_delete=models.CASCADE, related_name="cards",
        null=True, blank=True
    )
    title = models.CharField(max_length=255)
    price = models.PositiveIntegerField(default=0)
    rate_line = models.CharField(max_length=255, default="0% в день", blank=True)
    age_line = models.CharField(max_length=255, default="от 18 лет", blank=True)
    btn_text = models.CharField(max_length=100, default="ПОЛУЧИТЬ ДЕНЬГИ", blank=True)
    btn_url = models.URLField(blank=True, null=True)
    fine_print = models.CharField(max_length=255, default="Решение по заявке принимается в течение нескольких минут.", blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    order_index = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order_index","id"]

    def __str__(self):
        return self.title
