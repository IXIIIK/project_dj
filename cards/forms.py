import re
from pathlib import Path
from django import forms
from django.conf import settings
from .models import Showcase, Card, Logo
from django.urls import reverse


# ---------------- utils ----------------

class DomainCheckboxSelect(forms.CheckboxSelectMultiple):
    template_name = "widgets/domain_checkbox.html"
    option_template_name = "widgets/domain_checkbox_option.html"


def build_domain_choices():
    """
    Берём домены из settings.DOMAINS_ALLOWED и превращаем в choices.
    - игнорируем localhost и IP
    - для value всегда используем punycode (ascii)
    - для label всегда показываем unicode
    - dedupe по punycode, сортируем по label
    """
    raw = getattr(settings, "DOMAINS_ALLOWED", []) or []
    uniq = {}  # ascii_host -> label

    try:
        import idna
    except ImportError:
        idna = None

    for d in raw:
        d = (d or "").strip().lower()
        if not d:
            continue

        # выкидываем локалки и IP
        if d in ("localhost", "127.0.0.1"):
            continue
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", d):
            continue

        # нормализуем к punycode для value
        ascii_host = d
        label = d
        if idna:
            try:
                ascii_host = idna.encode(d, uts46=True).decode("ascii")
            except Exception:
                ascii_host = d
            try:
                label = idna.decode(ascii_host)
            except Exception:
                label = d

        uniq[ascii_host] = label

    # вернём отсортированные пары (punycode, unicode)
    return sorted(uniq.items(), key=lambda kv: kv[1])


def normalize_domain_lines(value: str) -> str:
    lines = []
    for line in (value or "").splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return "\n".join(sorted(set(lines)))


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


# ---------------- forms ----------------

class ShowcaseForm(forms.ModelForm):
    template = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select
    )
    domains = forms.MultipleChoiceField(
        required=False,
        choices=[],
        widget=DomainCheckboxSelect
    )

    class Meta:
        model = Showcase
        fields = ["name", "template", "slug", "domains", "extra_params"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Название"}),
            "slug": forms.TextInput(attrs={"placeholder": "URL-имя (после /)"}),
            "extra_params": forms.TextInput(attrs={"placeholder": "aff_id=42&sub=abc"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["extra_params"].label = "Доп. метки (GET-параметры)"
        self.fields["extra_params"].help_text = "Формат: key=value&key2=value2 (без вопросительного знака)"
        # choices для тем
        self.fields["domains"].widget = forms.CheckboxSelectMultiple()

        theme_choices = get_theme_choices()
        print(">>> DEBUG get_theme_choices:", theme_choices)
        self.fields["template"].choices = theme_choices
        self.fields["template"].label = "Тема"

        # домены из settings
        print(">>> DEBUG DOMAINS_ALLOWED:", settings.DOMAINS_ALLOWED)
        choices = build_domain_choices()
        print(">>> DEBUG build_domain_choices:", choices)

        if choices:
            self.fields["domains"].choices = choices
            self.fields["domains"].help_text = "Выберите один или несколько доменов."
            # пересоздаём widget, чтобы он подтянул актуальные choices
            self.fields["domains"].widget = forms.CheckboxSelectMultiple(choices=choices)

            if self.instance and self.instance.pk and self.instance.domains:
                current = [ln.strip() for ln in self.instance.domains.splitlines() if ln.strip()]
                self.initial["domains"] = current
        else:
            self.fields["domains"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 6,
                                            "placeholder": "Список пуст. Добавьте домены в settings.DOMAINS_ALLOWED."}),
                help_text="Каждый домен с новой строки."
            )

        # подписи
        self.fields["template"].label = "Тема"
        self.fields["slug"].label = "URL-имя (после /)"
        self.fields["domains"].label = "Домены"

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        if not slug:
            base = (self.cleaned_data.get("name") or "").strip().lower()
            base = re.sub(r"[^a-z0-9-_]+", "-", base).strip("-_")
            return base
        return re.sub(r"[^a-z0-9-_]+", "-", slug).strip("-_")

    def save(self, commit=True):
        sc = super().save(commit=False)

        if isinstance(self.fields["domains"], forms.MultipleChoiceField):
            selected = self.cleaned_data.get("domains") or []
            sc.domains = "\n".join(sorted(set([s.strip() for s in selected if s.strip()])))
        else:
            sc.domains = normalize_domain_lines(self.cleaned_data.get("domains") or "")

        if commit:
            sc.save()
        return sc


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = [
            "showcase", "title", "price", "rate_line", "age_line",
            "btn_text", "btn_url", "fine_print", "logo",
            "order_index", "active",
        ]
        widgets = {
            "btn_url": forms.URLInput(attrs={"placeholder": "https://partner.ru/apply"}),
            "logo": forms.Select(attrs={
                "id": "id_logo",
                "data-placeholder": "Найти логотип…",
                # data-search-url добавим ниже, когда reverse доступен
            }),
        }
        help_texts = { "btn_url": "" }

    def __init__(self, *args, showcase=None, **kwargs):
        super().__init__(*args, **kwargs)

        if showcase is not None:
            self.fields["showcase"].initial = showcase
            self.fields["showcase"].widget = forms.HiddenInput()

        # --- ПРЕДЗАГРУЗКА: первые 50 логотипов по имени ---
        preload_ids = list(
            Logo.objects.order_by("name").values_list("pk", flat=True)[:50]
        )

        # учтём уже выбранный логотип (при редактировании) или присланный в POST
        selected_id = None
        if getattr(self.instance, "logo_id", None):
            selected_id = self.instance.logo_id
        elif self.data.get("logo"):
            selected_id = self.data.get("logo")

        if selected_id:
            try:
                selected_id = int(selected_id)
                if selected_id not in preload_ids:
                    preload_ids.append(selected_id)
            except (TypeError, ValueError):
                pass

        # финальный queryset БЕЗ distinct() и БЕЗ среза
        self.fields["logo"].queryset = (
            Logo.objects.filter(pk__in=preload_ids).order_by("name")
        )

        # атрибуты для JS-поиска
        self.fields["logo"].widget.attrs.update({
            "id": "id_logo",
            "data-placeholder": "Найти логотип…",
            "data-search-url": reverse("logos_search"),
            "data-showcase": str(getattr(showcase, "pk", "")) or "",
        })

    def clean_btn_url(self):
        u = (self.cleaned_data.get("btn_url") or "").strip()
        if not u:
            return u
        if not re.match(r"^https?://", u, re.I):
            u = "https://" + u.lstrip("/")
        return u


class LogoForm(forms.ModelForm):
    class Meta:
        model = Logo
        fields = ["name", "image"]