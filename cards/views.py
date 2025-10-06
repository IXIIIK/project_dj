from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Card, Showcase, Logo
from .forms import CardForm, ShowcaseForm, build_domain_choices, LogoForm
from django.views.decorators.http import require_POST
from django.http import Http404
from cards.utils.host import canonical_host
from django.shortcuts import get_object_or_404, redirect
from .models import Showcase
from config import settings
import idna




def _domains_ascii_set(domains_text: str) -> set[str]:
    """Разбираем TextField с доменами (запятые/переносы), приводим к punycode ascii, lower."""
    raw = (domains_text or "").replace(",", "\n")
    out = set()
    for line in raw.splitlines():
        h = line.strip()
        if not h:
            continue
        try:
            out.add(idna.encode(h, uts46=True).decode("ascii").lower())
        except Exception:
            out.add(h.lower())
    return out

def _showcase_matches_host(showcase: Showcase, ascii_host: str) -> bool:
    return ascii_host.lower() in _domains_ascii_set(showcase.domains)


# ---------- публичка ----------
def index(request):
    """Корень сайта: находим витрину по домену и ведём на неё (или 404)."""
    host = canonical_host(request)
    qs = Showcase.objects.order_by("-created_at", "-id")

    candidates = [s for s in qs if _showcase_matches_host(s, host)]
    if not candidates:
        raise Http404("Витрина для этого домена не настроена")

    # приоритет витрине со slug='main', иначе первая
    sc = next((s for s in candidates if (s.slug or "").lower() == "main"), candidates[0])

    # редирект на ЧПУ витрины (если имя маршрута другое — поменяй на своё)
    return redirect("showcase_detail", slug=sc.slug)



@login_required
def showcase_add(request):
    if request.method == "POST":
        form = ShowcaseForm(request.POST)
        if form.is_valid():
            sc = form.save()
            # при желании — сразу перейти к редактированию карточек:
            # return redirect("cards_admin", pk=sc.pk)
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm()

    return render(
        request,
        "admin_showcase_form.html",
        {
            "form": form,
            "showcase": None,  # чтобы шаблон не ожидал существующий объект
            "dom_choices_dbg": build_domain_choices(),
        },
    )


def showcase_detail(request, slug):
    """Витрина: выбираем по slug + домен, рендерим нужную тему, отдаём только её карточки."""
    host = canonical_host(request)

    # берём все витрины с таким slug и выбираем подходящую по домену
    qs = Showcase.objects.filter(slug=slug).order_by("-created_at", "-id")
    sc = None
    for s in qs:
        if _showcase_matches_host(s, host):
            sc = s
            break
    if sc is None:
        # в DEBUG можно показать первую попавшуюся, в PROD — 404
        if settings.DEBUG and qs.exists():
            sc = qs.first()
        else:
            raise Http404("Витрина не найдена для этого домена")

    cards = (sc.cards.filter(active=True)
             .select_related("logo")
             .order_by("order_index", "id"))

    template_name = f"themes/{sc.template}/index.html" if sc.template else "index.html"
    return render(request, template_name, {"showcase": sc, "cards": cards})


# ---------- админка ----------
@login_required
def showcases_admin(request):
    qs = Showcase.objects.order_by("-created_at", "-id")
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "admin_showcases.html", {"page_obj": page_obj})

@login_required
def cards_admin(request, pk):
    showcase = get_object_or_404(Showcase, pk=pk)
    qs = showcase.cards.order_by("order_index", "id")
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "admin_cards.html", {"showcase": showcase, "page_obj": page_obj})



from django.db import transaction


@login_required
@require_POST  # если делаешь кнопкой-формой; можно убрать, если хочешь GET
def showcase_duplicate(request, pk):
    src = get_object_or_404(Showcase, pk=pk)
    # глубокое копирование + карточки
    new = Showcase.objects.get(pk=src.pk)
    new.pk = None
    if new.slug:
        new.slug = f"{new.slug}-copy"
    new.save()

    # копируем карточки
    cards = list(src.cards.all())
    for c in cards:
        old_id = c.pk
        c.pk = None
        c.showcase = new
        c.save()
    return redirect("showcases_admin")



@login_required
@require_POST
def card_toggle(request, pk, cid):
    showcase = get_object_or_404(Showcase, pk=pk)
    card = get_object_or_404(Card, pk=cid, showcase=showcase)
    card.active = not card.active
    card.save()
    return redirect("cards_admin", pk=showcase.pk)


@login_required
def card_add(request, pk):
    showcase = get_object_or_404(Showcase, pk=pk)
    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, showcase=showcase)
        if form.is_valid():
            card = form.save(commit=False)
            card.showcase = showcase
            card.save()
            return redirect("cards_admin", pk=showcase.pk)
    else:
        form = CardForm(showcase=showcase)
    return render(request, "admin_card_form.html", {"form": form, "showcase": showcase})

@login_required
def card_edit(request, pk, cid):
    showcase = get_object_or_404(Showcase, pk=pk)
    card = get_object_or_404(Card, pk=cid, showcase=showcase)
    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, instance=card, showcase=showcase)
        if form.is_valid():
            form.save()
            return redirect("cards_admin", pk=showcase.pk)
    else:
        form = CardForm(instance=card, showcase=showcase)
    return render(request, "admin_card_form.html", {"form": form, "showcase": showcase, "card": card})


@login_required
@require_POST
def card_delete(request, pk, cid):
    showcase = get_object_or_404(Showcase, pk=pk)
    card = get_object_or_404(Card, pk=cid, showcase=showcase)
    card.delete()
    return redirect("cards_admin", pk=showcase.pk)


@login_required
def showcase_edit(request, pk):
    showcase = get_object_or_404(Showcase, pk=pk)
    if request.method == "POST":
        form = ShowcaseForm(request.POST, instance=showcase)
        if form.is_valid():
            form.save()
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm(instance=showcase)
    return render(request, "admin_showcase_form.html", {"form": form, "showcase": showcase, "dom_choices_dbg": build_domain_choices()})


@login_required
@require_POST
def showcase_delete(request, pk):
    showcase = get_object_or_404(Showcase, pk=pk)
    showcase.delete()
    return redirect("showcases_admin")



@login_required
def logos_admin(request):
    qs = Logo.objects.order_by("-id")
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "admin_logos.html", {"page_obj": page_obj})

@login_required
def logo_add(request):
    if request.method == "POST":
        form = LogoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("logos_admin")
    else:
        form = LogoForm()
    return render(request, "admin_logo_form.html", {"form": form})

@login_required
def logo_delete(request, pk):
    logo = get_object_or_404(Logo, pk=pk)
    logo.delete()
    return redirect("logos_admin")
