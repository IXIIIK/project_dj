# cards/models.py
from django.db import models
from django.utils.text import slugify
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
import re
import idna

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
    extra_params = models.CharField(
        max_length=255,
        blank=True,
        help_text="Дополнительные GET-параметры (например: aff_id=42&sub=abc)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    domains = models.TextField(blank=True, default='')
    # 👇 новое поле
    template = models.CharField(
        max_length=50,
        default="",
        blank=True,
        help_text="Имя папки темы из cards/templates/themes/<template>/"
    )
    class Meta:
        constraints = [
                models.UniqueConstraint(
                    fields=["domains", "slug"],
                    name="uniq_showcase_per_domain",
                ),
            ]

    def __str__(self):
        return self.name or f"Витрина {self.pk}"
    
    def domains_list(self):
        """Список доменов из поля domains (через запятую/пробел/переносы)."""
        out = []
        for line in (self.domains or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(idna.decode(line))
            except Exception:
                out.append(line)
        return out
    
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



class Logo(models.Model):
    name = models.CharField("Название", max_length=255)
    image = models.ImageField("Файл", upload_to="logos/")

    def __str__(self):
        return self.name or f"Логотип {self.pk}"


class Card(models.Model):
    showcase = models.ForeignKey(
        Showcase,
        on_delete=models.CASCADE,
        related_name="cards",
        null=True,
        blank=True,
        verbose_name="Витрина"
    )
    title = models.CharField("Заголовок", max_length=255)
    price = models.PositiveIntegerField("Цена", default=0)
    rate_line = models.CharField("Ставка", max_length=255, default="0% в день", blank=True)
    age_line = models.CharField("Возрастное ограничение", max_length=255, default="от 18 лет", blank=True)
    btn_text = models.CharField("Текст кнопки", max_length=100, default="ПОЛУЧИТЬ ДЕНЬГИ", blank=True)
    btn_url = models.URLField(
        "Ссылка",
        max_length=500,
        blank=True,
        null=True,
        help_text="Пример: partner.ru/apply или полный https://partner.ru/apply. Схема добавится автоматически."
    )
    fine_print = models.CharField(
        "Примечание мелким шрифтом",
        max_length=255,
        default="Решение по заявке принимается в течение нескольких минут.",
        blank=True
    )
    logo = models.ImageField("Логотип", upload_to="logos/", blank=True, null=True)
    order_index = models.IntegerField("Порядок", default=0)
    active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    logo = models.ForeignKey(
        "Logo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cards",
        verbose_name="Логотип"
    )

    class Meta:
        ordering = ["order_index", "id"]
        verbose_name = "Карточка"
        verbose_name_plural = "Карточки"


    def __str__(self):
        return self.title
    
    @property
    def get_full_btn_url(self):
            """
            Возвращает полную ссылку:
            - если схема отсутствует — добавляем https://
            - приклеиваем параметры из showcase.extra_params
            """
            raw = (self.btn_url or "").strip()
            if not raw:
                return ""

            # если пользователь вводит partner.ru/path — добавим схему
            p = urlparse(raw)
            if not p.scheme:
                raw = "https://" + raw.lstrip("/")
                p = urlparse(raw)

            # если всё ещё нет netloc (например, '/path') — считаем, что ссылка некорректна
            if not p.netloc:
                return raw  # можно вернуть "" если хочешь скрывать кнопку

            # текущие query-параметры из ссылки
            query = dict(parse_qsl(p.query, keep_blank_values=True))

            # приклеим доп. метки из витрины
            extra = (self.showcase.extra_params or "").strip().lstrip("?&")
            if extra:
                extra_qs = dict(parse_qsl(extra, keep_blank_values=True))
                query.update(extra_qs)

            # соберём назад
            p = p._replace(query=urlencode(query, doseq=True))
            return urlunparse(p)
        

