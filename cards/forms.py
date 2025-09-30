<<<<<<< Updated upstream
from django import forms
from .models import Card, Showcase

class ShowcaseForm(forms.ModelForm):
    class Meta:
        model = Showcase
        fields = ["name", "slug", "domains"]
=======
# cards/forms.py
import re
from pathlib import Path

from django import forms
from django.conf import settings
from django.utils.text import slugify

from .models import Showcase, Card

RESERVED = {"admin", "static", "media", "accounts", "login", "logout"}

# ---- темы (папки в cards/templates/themes/*) ----
def get_theme_choices():
    base = Path(settings.BASE_DIR) / "cards" / "templates" / "themes"
    label_map = {"green": "Зелёный", "blue": "Синий"}
    items = []
    if base.exists():
        for d in sorted(base.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                label = label_map.get(d.name, d.name)
                items.append((d.name, label))
    return [("", "Авто (общий шаблон)")] + items


# ---- домены из settings.DOMAINS_ALLOWED -> choices ----
def build_domain_choices():
    raw = list(getattr(settings, "DOMAINS_ALLOWED", []) or [])
    choices = []
    try:
        import idna
    except Exception:
        idna = None

    for d in raw:
        d = (d or "").strip()
        if not d:
            continue
        if idna:
            try:
                ascii_host = idna.encode(d, uts46=True).decode("ascii")
            except Exception:
                ascii_host = d
        else:
            ascii_host = d
        # value -> punycode/ascii (то что в БД), label -> как показываем
        choices.append((ascii_host, d))
    return choices


def normalize_domain_lines(value: str) -> str:
    lines = []
    for line in (value or "").splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return "\n".join(sorted(set(lines)))


class ShowcaseForm(forms.ModelForm):
    """
    ЕДИНСТВЕННАЯ версия формы. В ней:
    - выбор темы (ChoiceField)
    - домены: если есть список в settings -> чекбоксы; иначе textarea
    - нормализация и уникальность slug
    """
    template = forms.ChoiceField(choices=(), required=False)
    # по умолчанию — переопределим в __init__ при наличии choices
    domains = forms.MultipleChoiceField(
        required=False,
        choices=[],
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Showcase
        fields = ["name", "template", "slug", "domains"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Название"}),
            "slug": forms.TextInput(attrs={
                "placeholder": "URL-имя (после /). Можно оставить пустым — сгенерируется.",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # темы
        self.fields["template"].choices = get_theme_choices()
        self.fields["template"].label = "Тема"

        # домены
        choices = build_domain_choices()
        if choices:
            self.fields["domains"].choices = choices
            self.fields["domains"].help_text = "Выберите один или несколько доменов."
            self.fields["domains"].label = "Домены"
            # выставим выбранные (punycode) из instance
            if self.instance and self.instance.pk and self.instance.domains:
                current = [ln.strip() for ln in self.instance.domains.splitlines() if ln.strip()]
                self.initial["domains"] = current
        else:
            # если настроек нет — даём свободный ввод
            self.fields["domains"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={
                    "rows": 6,
                    "placeholder": "Список пуст. Добавьте домены в settings.DOMAINS_ALLOWED.",
                }),
                help_text="Каждый домен с новой строки.",
                label="Домены",
            )

        self.fields["slug"].label = "URL-имя (после /)"

    def clean_slug(self):
        # только латиница/цифры/-/_ ; автогенерация из name при пустом
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        if not slug:
            base = (self.cleaned_data.get("name") or "").strip().lower()
            slug = re.sub(r"[^a-z0-9-_]+", "-", base).strip("-_")
        else:
            slug = re.sub(r"[^a-z0-9-_]+", "-", slug).strip("-_")

        if slug in RESERVED:
            raise forms.ValidationError("Такое URL-имя зарезервировано.")

        # уникальность с учётом текущей витрины
        qs = Showcase.objects.exclude(pk=self.instance.pk) if self.instance and self.instance.pk else Showcase.objects.all()
        if slug and qs.filter(slug=slug).exists():
            raise forms.ValidationError("Это URL-имя уже занято другой витриной.")

        return slug

    def save(self, commit=True):
        sc = super().save(commit=False)

        # domains: если MultipleChoiceField — сохраняем выбранные (punycode)
        if isinstance(self.fields.get("domains"), forms.MultipleChoiceField):
            selected = self.cleaned_data.get("domains") or []
            sc.domains = "\n".join(sorted(set([s.strip() for s in selected if s.strip()])))
        else:
            # textarea
            sc.domains = normalize_domain_lines(self.cleaned_data.get("domains") or "")

        if commit:
            sc.save()
        return sc
>>>>>>> Stashed changes


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = [
            "showcase", "title", "price", "rate_line", "age_line",
            "btn_text", "btn_url", "fine_print", "logo",
            "order_index", "active",
        ]

    def __init__(self, *args, showcase=None, **kwargs):
        super().__init__(*args, **kwargs)
        if showcase is not None:
            self.fields["showcase"].initial = showcase
            self.fields["showcase"].widget = forms.HiddenInput()

