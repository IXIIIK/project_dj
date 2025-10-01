from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Card, Showcase
from .forms import CardForm, ShowcaseForm, build_domain_choices
from django.views.decorators.http import require_POST
from django.http import Http404
from config import settings


def _get_showcase_by_key(request, key: str) -> Showcase:
    s = str(key).strip()
    qs = Showcase.objects.all()

    # сначала пробуем по id
    if s.isdigit():
        try:
            return qs.get(pk=int(s))
        except Showcase.DoesNotExist:
            # если витрины с таким id нет — пробуем искать как slug
            pass

    qs = qs.filter(slug=s)

    from django.conf import settings
    if settings.DEBUG:
        if not qs.exists():
            raise Http404("Showcase not found")
        return qs.first()

    host = request.get_host().split(":")[0]
    candidates = [sc for sc in qs if host in sc.domains_list()]
    if not candidates:
        raise Http404("Showcase not found")
    return candidates[0]


# ---------- публичка ----------
def index(request):
    cards = Card.objects.filter(active=True).order_by("order_index", "id")
    return render(request, "index.html", {"cards": cards})

def showcase_detail(request, key):
    showcase = _get_showcase_by_key(request, key)
    cards = showcase.cards.filter(active=True).order_by("order_index", "id")

    templates = []
    tpl = (showcase.template or "").strip()
    if tpl and tpl != "default":
        templates.append(f"themes/{tpl}/index.html")
    templates.append("index.html")  # дефолт

    return render(request, templates, {"cards": cards, "showcase": showcase})


# ---------- админка ----------
@login_required
def showcases_admin(request):
    qs = Showcase.objects.order_by("-created_at", "-id")
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "admin_showcases.html", {"page_obj": page_obj})

@login_required
def cards_admin(request, key):
    showcase = _get_showcase_by_key(request, key)
    qs = showcase.cards.order_by("order_index", "id")
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "admin_cards.html", {"showcase": showcase, "page_obj": page_obj})

@login_required
def showcase_add(request):
    if request.method == "POST":
        form = ShowcaseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm()
    return render(
        request,
        "admin_showcase_form.html",
        {"form": form, "dom_choices_dbg": build_domain_choices()},
    )


from django.db import transaction

@login_required
def showcase_duplicate(request, key):
    original = _get_showcase_by_key(request, key)

    # создаём копию витрины
    new_showcase = Showcase.objects.get(pk=original.pk)
    new_showcase.pk = None  # чтобы сохранился как новый
    if new_showcase.slug:
        base_slug = new_showcase.slug
        # проверяем, нет ли дублей
        counter = 1
        new_slug = f"{base_slug}-copy"
        while Showcase.objects.filter(slug=new_slug).exists():
            counter += 1
            new_slug = f"{base_slug}-copy{counter}"
        new_showcase.slug = new_slug
    new_showcase.save()

    # копируем карточки
    for card in original.cards.all():
        new_card = Card.objects.get(pk=card.pk)
        new_card.pk = None  # новая запись
        new_card.showcase = new_showcase  # привязываем к новой витрине
        new_card.save()

    return redirect("showcases_admin")




@login_required
def card_add(request, key):
    showcase = _get_showcase_by_key(request, key)

    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, showcase=showcase)
        if form.is_valid():
            card = form.save(commit=False)
            card.showcase = showcase
            card.save()
            return redirect("cards_admin", key=showcase.slug)
    else:
        form = CardForm(showcase=showcase)

    return render(
        request,
        "admin_card_form.html",
        {"form": form, "showcase": showcase},
    )



@login_required
def card_edit(request, key, pk):
    showcase = _get_showcase_by_key(request, key)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, instance=card, showcase=showcase)
        if form.is_valid():
            form.save()
            return redirect("cards_admin", key=showcase.slug)
    else:
        form = CardForm(instance=card, showcase=showcase)
    return render(request, "admin_card_form.html", {"form": form, "showcase": showcase, "card": card})

@login_required
@require_POST
def card_delete(request, key, pk):
    showcase = _get_showcase_by_key(request, key)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    card.delete()
    return redirect("cards_admin", key=showcase.slug)

@login_required
@require_POST
def card_toggle(request, key, pk):
    showcase = _get_showcase_by_key(request, key)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    card.active = not card.active
    card.save()
    return redirect("cards_admin", key=showcase.slug)


@login_required
def showcase_edit(request, key):
    showcase = _get_showcase_by_key(request, key)
    if request.method == "POST":
        form = ShowcaseForm(request.POST, instance=showcase)
        if form.is_valid():
            form.save()
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm(instance=showcase)
    return render(
        request,
        "admin_showcase_form.html",
        {"form": form, "showcase": showcase, "dom_choices_dbg": build_domain_choices()},
    )

@login_required
@require_POST
def showcase_delete(request, key):
    showcase = _get_showcase_by_key(request, key)
    showcase.delete()
    return redirect("showcases_admin")
