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
from django.http import JsonResponse
from django.db.models import Q, Case, When, IntegerField





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
    host = canonical_host(request)
    qs = Showcase.objects.order_by("-created_at", "-id")
    candidates = [s for s in qs if s.matches_host(host)]
    if not candidates:
        raise Http404("Витрина для этого домена не настроена")
    sc = next((s for s in candidates if (s.slug or "").lower() == "main"), candidates[0])
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
    host = canonical_host(request)
    qs = Showcase.objects.filter(slug=slug).order_by("-created_at", "-id")
    sc = next((s for s in qs if s.matches_host(host)), None)
    if sc is None:
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
    q = (request.GET.get("q") or "").strip()
    try:
        per_page = int(request.GET.get("per_page") or 10)
    except ValueError:
        per_page = 10
    per_page = max(5, min(per_page, 100))

    qs = Showcase.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))

    qs = qs.order_by("-created_at", "-id")
    page_obj = Paginator(qs, per_page).get_page(request.GET.get("page"))

    return render(
        request,
        "admin_showcases.html",
        {
            "page_obj": page_obj,
            "q": q,
            "per_page": per_page,
            "per_page_options": [10, 20, 30, 50],   # ← вот это
        },
    )


@login_required
def showcases_suggest(request):
    q = (request.GET.get("q") or "").strip()
    qs = Showcase.objects.all()

    if q:
        qs = (qs
              .filter(Q(name__icontains=q) | Q(slug__icontains=q))
              .annotate(priority=Case(
                  When(name__istartswith=q, then=0),
                  When(slug__istartswith=q, then=0),
                  default=1,
                  output_field=IntegerField(),
              ))
              .order_by("priority", "name"))
    else:
        qs = qs.order_by("-created_at")

    data = [
        {"id": s.id, "name": s.name, "slug": s.slug, "label": f"{s.name} ({s.slug})"}
        for s in qs[:10]
    ]
    return JsonResponse({"results": data})


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

    # безопасно читаем per_page из GET
    try:
        per_page = int(request.GET.get("per_page", 20))
    except ValueError:
        per_page = 20
    per_page = max(8, min(per_page, 200))  # от 8 до 200

    page_number = request.GET.get("page")
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "admin_logos.html",
        {
            "page_obj": page_obj,
            "per_page": per_page,
        },
    )

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


@login_required
def logos_search(request):
    q = (request.GET.get("q") or "").strip()
    page = int(request.GET.get("page") or 1)
    per_page = 20

    qs = Logo.objects.all().order_by("name")
    if q:
        qs = qs.filter(name__icontains=q)

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page)

    results = [
        {"id": str(logo.pk), "text": logo.name or f"Логотип #{logo.pk}", "img": (logo.image.url if logo.image else "")}
        for logo in page_obj.object_list
    ]
    return JsonResponse({"results": results, "pagination": {"more": page_obj.has_next()}})
