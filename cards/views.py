from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Card, Showcase
from .forms import CardForm, ShowcaseForm

def index(request):
    cards = Card.objects.filter(active=True)
    return render(request, "index.html", {"cards": cards})

@login_required
def cards_admin(request):
    cards = Card.objects.all()
    return render(request, "admin_cards.html", {"cards": cards})

@login_required
def card_add(request, showcase_id: int):
    showcase = get_object_or_404(Showcase, pk=showcase_id)
    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, showcase=showcase)
        if form.is_valid():
            form.save()
            return redirect("cards_admin", showcase_id=showcase.id)
    else:
        form = CardForm(showcase=showcase)
    return render(request, "admin_card_form.html", {"form": form, "showcase": showcase})

@login_required
def card_edit(request, showcase_id: int, pk: int):
    showcase = get_object_or_404(Showcase, pk=showcase_id)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    if request.method == "POST":
        form = CardForm(request.POST, request.FILES, instance=card, showcase=showcase)
        if form.is_valid():
            form.save()
            return redirect("cards_admin", showcase_id=showcase.id)
    else:
        form = CardForm(instance=card, showcase=showcase)
    return render(request, "admin_card_form.html", {"form": form, "showcase": showcase, "card": card})

@login_required
def card_delete(request, showcase_id: int, pk: int):
    showcase = get_object_or_404(Showcase, pk=showcase_id)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    card.delete()
    return redirect("cards_admin", showcase_id=showcase.id)

@login_required
def card_toggle(request, showcase_id: int, pk: int):
    showcase = get_object_or_404(Showcase, pk=showcase_id)
    card = get_object_or_404(Card, pk=pk, showcase=showcase)
    card.active = not card.active
    card.save()
    return redirect("cards_admin", showcase_id=showcase.id)


@login_required
def card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk)
    card.delete()
    return redirect("cards_admin")

@login_required
def card_toggle(request, pk):
    card = get_object_or_404(Card, pk=pk)
    card.active = not card.active
    card.save()
    return redirect("cards_admin")


@login_required
def showcases_admin(request):
    qs = Showcase.objects.order_by("-created_at", "-id")
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "admin_showcases.html", {"page_obj": page_obj})

@login_required
def cards_admin(request, showcase_id: int):
    showcase = get_object_or_404(Showcase, pk=showcase_id)
    qs = showcase.cards.order_by("order_index", "id")
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    ctx = {"showcase": showcase, "page_obj": page_obj}
    return render(request, "admin_cards.html", ctx)

#Add showcase
@login_required
def showcase_add(request):
    if request.method == "POST":
        form = ShowcaseForm(request.POST)
        if form.is_valid():
            showcase = form.save()
            return redirect("showcases_admin")
    else:
        form = ShowcaseForm()
    return render(request, "admin_showcase_form.html", {"form": form})

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
    return render(request, "admin_showcase_form.html", {"form": form, "showcase": showcase})

@login_required
def showcase_delete(request, pk):
    showcase = get_object_or_404(Showcase, pk=pk)
    showcase.delete()
    return redirect("showcases_admin")

def showcase_detail(request, pk):
    showcase = get_object_or_404(Showcase, pk=pk)
    cards = showcase.cards.filter(active=True)
    return render(request, "index.html", {"cards": cards, "showcase": showcase})
