from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Card, Showcase
from .forms import CardForm, ShowcaseForm
from django.views.decorators.http import require_POST


def _get_showcase_by_key(key: str) -> Showcase:
    s = str(key).strip()
    if s.isdigit():
        return get_object_or_404(Showcase, pk=int(s))
    return get_object_or_404(Showcase, slug=s)

# ---------- публичка ----------
def index(request):
    cards = Card.objects.filter(active=True).order_by("order_index", "id")
    return render(request, "index.html", {"cards": cards})

def showcase_detail(request, key):
    showcase = _get_showcase_by_key(key)
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
    for sc in page_obj.object_list:
        sc._domains_list = sc.domains_list()
    return render(request, "admin_showcases.html", {"page_obj": page_obj})

@login_required
def cards_admin(request, key):
    showcase = _get_showcase_by_key(key)
    qs = showcase.cards.order_by("order_index", "id")
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "admin_cards.html", {"showcase": showcase, "page_obj": page_obj})

@login_required
def card_add(request, key):
    showcase = _get_showcase_by_key(key)
    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, showcase=showcase)   # ← CardForm
        if form.is_valid():
            card = form.save(commit=False)
            card.showcase = showcase
            card.save()
            return redirect("cards_admin", key=showcase.slug)
    else:
        form = CardForm(showcase=showcase)   # ← тоже CardForm
    return render(request, "admin_card_form.html", {"form": form, "showcase": showcase})


@login_required
def card_edit(request, key, pk):
    showcase = _get_showcase_by_key(key)
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
    showcase = _get_showcase_by_key(key)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    card.delete()
    return redirect("cards_admin", key=showcase.slug)

@login_required
@require_POST
def card_toggle(request, key, pk):
    showcase = _get_showcase_by_key(key)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    card.active = not card.active
    card.save()
    return redirect("cards_admin", key=showcase.slug)

@login_required
def showcase_add(request):
    if request.method == "POST":
        form = ShowcaseForm(request.POST)
        if form.is_valid():
            form.save()   # slug сгенерится в модели, если пустой
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm()
    return render(request, "admin_showcase_form.html", {"form": form})

@login_required
def showcase_edit(request, key):
    showcase = _get_showcase_by_key(key)
    if request.method == "POST":
        form = ShowcaseForm(request.POST, instance=showcase)
        if form.is_valid():
            form.save()
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm(instance=showcase)
    return render(request, "admin_showcase_form.html", {"form": form, "showcase": showcase})

@login_required
@require_POST
def showcase_delete(request, key):
    showcase = _get_showcase_by_key(key)
    showcase.delete()
    return redirect("showcases_admin")
