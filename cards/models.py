# cards/models.py
from django.db import models
from django.utils.text import slugify
import re

class Showcase(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название витрины")
    slug = models.SlugField(
        "URL-имя (после слеша)",
        max_length=64,
        unique=False,
        blank=True,   # можно оставить пустым — сгенерируется автоматически
        null=True,
        help_text="Только латиница, цифры, дефис. Пример: zaimy-moskva",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    domains = models.TextField(blank=True, help_text="Домен(ы) через запятую")
    # 👇 новое поле
    template = models.CharField(
        max_length=50,
        default="",
        blank=True,
        help_text="Имя папки темы из cards/templates/themes/<template>/"
    )

    def __str__(self):
        return self.name or f"Витрина {self.pk}"
    
    def domains_list(self):
        """Список доменов из поля domains (через запятую/пробел/переносы)."""
        return [h.strip() for h in re.split(r"[,\s]+", self.domains or "") if h.strip()]
    
    def domains_pairs(self):
        """
        Возвращает список кортежей (ascii_host_for_link, human_label) для каждого домена.
        В БД может быть как punycode, так и юникод — тут нормализуем оба случая.
        """
        pairs = []
        try:
            import idna
        except Exception:
            idna = None

        for raw in self.domains_list():
            ascii_host = raw
            label = raw
            if idna:
                # приводим к ascii (punycode) для href
                try:
                    ascii_host = idna.encode(raw, uts46=True).decode("ascii")
                except Exception:
                    ascii_host = raw
                # и получаем красивую метку для текста
                try:
                    label = idna.decode(ascii_host)
                except Exception:
                    label = raw
            pairs.append((ascii_host, label))
        return pairs

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name or "") or "showcase"
            cand, n = base, 2
            while Showcase.objects.filter(slug=cand).exclude(pk=self.pk).exists():
                cand = f"{base}-{n}"; n += 1
            self.slug = cand
        super().save(*args, **kwargs)


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
    

