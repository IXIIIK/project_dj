# cards/forms.py
import re
from pathlib import Path
from django import forms
from django.conf import settings
from .models import Showcase, Card
import re
# ---------------- utils ----------------

def build_domain_choices():
    """
    Берём домены из settings.DOMAINS_ALLOWED и превращаем в choices.
    value — punycode (ascii), label — красивый (unicode).
    """
    raw = getattr(settings, "DOMAINS_ALLOWED", []) or []
    choices = []
    try:
        import idna
    except Exception:
        idna = None

    for d in raw:
        d = (d or "").strip()
        if not d:
            continue
        # убираем localhost и ip
        if d in ("localhost", "127.0.0.1"):
            continue
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", d):
            continue

        ascii_host = d
        label = d
        if idna:
            try:
                # если это unicode — превратим в punycode
                ascii_host = idna.encode(d, uts46=True).decode("ascii")
            except Exception:
                ascii_host = d
            try:
                # если это punycode — превратим обратно для отображения
                label = idna.decode(ascii_host)
            except Exception:
                label = d

        choices.append((ascii_host, label))

    return choices



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

class DomainCheckboxSelect(forms.CheckboxSelectMultiple):
    template_name = "widgets/domain_checkbox.html"
    option_template_name = "widgets/domain_checkbox_option.html"

class ShowcaseForm(forms.ModelForm):
    # шаблон — выпадающий список
    template = forms.ChoiceField(choices=(), required=False)
    # домены — по умолчанию как чекбоксы (если список есть)
    domains = forms.MultipleChoiceField(required=False, choices=[], widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Showcase
        fields = ["name", "template", "slug", "domains"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Название"}),
            "slug": forms.TextInput(attrs={"placeholder": "URL-имя (после /)"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # choices для тем
        self.fields["template"].choices = get_theme_choices()

        # домены из settings
        choices = build_domain_choices()
        if choices:
            self.fields["domains"].choices = choices
            self.fields["domains"].help_text = "Выберите один или несколько доменов."
            self.fields["domains"].widget = DomainCheckboxSelect()
            # проставим initial из instance.domains (там храним по строкам)
            if self.instance and self.instance.pk and self.instance.domains:
                current = [ln.strip() for ln in self.instance.domains.splitlines() if ln.strip()]
                self.initial["domains"] = current
        else:
            # если DOMAINS_ALLOWED пуст — даём textarea
            self.fields["domains"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Список пуст. Добавьте домены в settings.DOMAINS_ALLOWED."}),
                help_text="Каждый домен с новой строки."
            )

        # подписи
        self.fields["template"].label = "Тема"
        self.fields["slug"].label = "URL-имя (после /)"
        self.fields["domains"].label = "Домены"

    def clean_slug(self):
        """Нормализуем slug и при пустом — генерируем из name."""
        slug = (self.cleaned_data.get("slug") or "").strip().lower()
        if not slug:
            base = (self.cleaned_data.get("name") or "").strip().lower()
            base = re.sub(r"[^a-z0-9-_]+", "-", base).strip("-_")
            return base
        return re.sub(r"[^a-z0-9-_]+", "-", slug).strip("-_")

    def save(self, commit=True):
        sc = super().save(commit=False)

        # checkbox/textarea — сохраняем единообразно: по строкам
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

    def __init__(self, *args, showcase=None, **kwargs):
        super().__init__(*args, **kwargs)
        if showcase is not None:
            self.fields["showcase"].initial = showcase
            self.fields["showcase"].widget = forms.HiddenInput()
