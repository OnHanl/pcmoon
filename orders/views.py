import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ContactForm, FAQItemForm, OrderForm, PortfolioItemForm, ReviewForm,
    ServiceCategoryForm, ServiceForm,
)
from .models import (
    CallLog, Contact, FAQItem, Order, PortfolioItem, Review, Service,
    ServiceCategory,
)


# ==================== Публичный сайт ====================

def index(request):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if order.consent:
                order.consent_at = timezone.now()
            order.save()
            success_text = "Спасибо! Заявка принята, мы перезвоним вам в ближайшее время."
            if is_ajax:
                return JsonResponse({"ok": True, "message": success_text})
            messages.success(request, success_text)
            return redirect("orders:index")
        elif is_ajax:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    else:
        form = OrderForm()

    reviews = Review.objects.filter(is_published=True)
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    context = {
        "categories": ServiceCategory.objects.prefetch_related("services").all(),
        "portfolio_items": PortfolioItem.objects.filter(is_published=True),
        "reviews": reviews,
        "avg_rating": avg_rating,
        "done_orders_count": Order.objects.filter(status=Order.Status.DONE).count(),
        "faq_items": FAQItem.objects.filter(is_published=True),
        "contact": Contact.objects.first(),
        "form": form,
    }
    return render(request, "orders/index.html", context)


# ==================== CRM: Kanban-панель заявок ====================

DASHBOARD_STATUSES = [
    {"key": "new", "label": "Новая заявка", "color": "var(--blue, #5B9DF9)"},
    {"key": "calling", "label": "Нужно перезвонить", "color": "var(--accent)"},
    {"key": "confirmed", "label": "Подтверждена", "color": "var(--purple, #A78BFA)"},
    {"key": "in_progress", "label": "В работе", "color": "var(--teal)"},
    {"key": "waiting_parts", "label": "Ожидание запчастей", "color": "var(--muted-2)"},
    {"key": "ready", "label": "Готово, ждёт клиента", "color": "var(--success, #4ADE80)"},
    {"key": "done", "label": "Завершена", "color": "var(--muted-2)"},
]


@staff_member_required
def dashboard(request):
    """Kanban-панель для ежедневной работы с заявками — главный экран CRM."""
    return render(request, "orders/dashboard.html", {
        "statuses": DASHBOARD_STATUSES, "active": "orders",
    })


@staff_member_required
def api_orders(request):
    """JSON со всеми активными заявками + краткая статистика для карточек сверху."""
    orders = (
        Order.objects
        .exclude(status=Order.Status.CANCELED)
        .select_related("service")
        .prefetch_related("call_logs")
        .order_by("-created_at")
    )

    def humanize(dt):
        diff = timezone.now() - dt
        if diff < timedelta(minutes=1):
            return "только что"
        if diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() // 60)} мин назад"
        if diff < timedelta(days=1):
            return f"{int(diff.total_seconds() // 3600)} ч назад"
        if diff < timedelta(days=2):
            return "вчера"
        return f"{diff.days} дн назад"

    data = []
    for o in orders:
        data.append({
            "id": o.id,
            "name": o.name,
            "phone": o.phone,
            "service": o.service.name if o.service else "—",
            "status": o.status,
            "priority": o.priority,
            "comment": o.comment,
            "estimated_price": float(o.estimated_price) if o.estimated_price else None,
            "time": humanize(o.created_at),
            "calls": [
                {"date": c.date.strftime("%d.%m, %H:%M"), "note": c.note}
                for c in o.call_logs.all()
            ],
        })

    today = timezone.now().date()
    month_start = today.replace(day=1)
    revenue_month = sum(
        o.estimated_price for o in Order.objects.filter(
            status=Order.Status.DONE, updated_at__date__gte=month_start
        ).exclude(estimated_price=None)
    ) or 0

    stats = {
        "new_today": Order.objects.filter(created_at__date=today).count(),
        "in_progress": Order.objects.filter(status=Order.Status.IN_PROGRESS).count(),
        "active_total": Order.objects.exclude(
            status__in=[Order.Status.DONE, Order.Status.CANCELED]
        ).count(),
        "revenue_month": float(revenue_month),
    }

    return JsonResponse({"orders": data, "statuses": DASHBOARD_STATUSES, "stats": stats})


@staff_member_required
@require_POST
def api_order_set_status(request, order_id):
    """Обновляет статус заявки — вызывается при перетаскивании карточки между колонками."""
    order = get_object_or_404(Order, id=order_id)
    payload = json.loads(request.body or "{}")
    status = payload.get("status")
    valid_keys = [s.value for s in Order.Status]
    if status not in valid_keys:
        return JsonResponse({"ok": False, "error": "Неизвестный статус"}, status=400)
    order.status = status
    order.save(update_fields=["status", "updated_at"])
    return JsonResponse({"ok": True})


@staff_member_required
@require_POST
def api_order_add_call(request, order_id):
    """Добавляет запись в журнал звонков заявки прямо из панели."""
    order = get_object_or_404(Order, id=order_id)
    payload = json.loads(request.body or "{}")
    note = (payload.get("note") or "").strip()
    if not note:
        return JsonResponse({"ok": False, "error": "Пустая заметка"}, status=400)
    call = CallLog.objects.create(order=order, note=note)
    return JsonResponse({"ok": True, "date": call.date.strftime("%d.%m, %H:%M")})


# ==================== CRM: разделы управления контентом ====================
# Общий паттерн для каждого раздела: список -> форма добавления/редактирования -> удаление (POST).
# Всё в едином тёмном стиле панели (crm_base.html), без выхода в стандартную /admin/.

@staff_member_required
def crm_prices(request):
    categories = ServiceCategory.objects.prefetch_related("services").all()
    return render(request, "orders/crm_prices.html", {"categories": categories, "active": "prices"})


@staff_member_required
def crm_category_form(request, category_id=None):
    category = get_object_or_404(ServiceCategory, id=category_id) if category_id else None
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Категория сохранена.")
            return redirect("orders:crm_prices")
    else:
        form = ServiceCategoryForm(instance=category)
    return render(request, "orders/crm_form.html", {
        "form": form, "title": "Категория услуг", "back_url": "orders:crm_prices", "active": "prices",
        "delete_url": reverse("orders:crm_category_delete", args=[category.id]) if category else None,
    })


@staff_member_required
@require_POST
def crm_category_delete(request, category_id):
    get_object_or_404(ServiceCategory, id=category_id).delete()
    messages.success(request, "Категория удалена.")
    return redirect("orders:crm_prices")


@staff_member_required
def crm_service_form(request, service_id=None):
    service = get_object_or_404(Service, id=service_id) if service_id else None
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Услуга сохранена.")
            return redirect("orders:crm_prices")
    else:
        form = ServiceForm(instance=service)
    return render(request, "orders/crm_form.html", {
        "form": form, "title": "Услуга", "back_url": "orders:crm_prices", "active": "prices",
        "delete_url": reverse("orders:crm_service_delete", args=[service.id]) if service else None,
    })


@staff_member_required
@require_POST
def crm_service_delete(request, service_id):
    get_object_or_404(Service, id=service_id).delete()
    messages.success(request, "Услуга удалена.")
    return redirect("orders:crm_prices")


@staff_member_required
def crm_portfolio(request):
    items = PortfolioItem.objects.all()
    return render(request, "orders/crm_portfolio.html", {"items": items, "active": "portfolio"})


@staff_member_required
def crm_portfolio_form(request, item_id=None):
    item = get_object_or_404(PortfolioItem, id=item_id) if item_id else None
    if request.method == "POST":
        form = PortfolioItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Пример работы сохранён.")
            return redirect("orders:crm_portfolio")
    else:
        form = PortfolioItemForm(instance=item)
    return render(request, "orders/crm_form.html", {
        "form": form, "title": "Пример работы", "back_url": "orders:crm_portfolio",
        "is_multipart": True, "active": "portfolio",
        "delete_url": reverse("orders:crm_portfolio_delete", args=[item.id]) if item else None,
    })


@staff_member_required
@require_POST
def crm_portfolio_delete(request, item_id):
    get_object_or_404(PortfolioItem, id=item_id).delete()
    messages.success(request, "Пример работы удалён.")
    return redirect("orders:crm_portfolio")


@staff_member_required
def crm_reviews(request):
    reviews = Review.objects.all()
    return render(request, "orders/crm_reviews.html", {"reviews": reviews, "active": "reviews"})


@staff_member_required
def crm_review_form(request, review_id=None):
    review = get_object_or_404(Review, id=review_id) if review_id else None
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Отзыв сохранён.")
            return redirect("orders:crm_reviews")
    else:
        form = ReviewForm(instance=review)
    return render(request, "orders/crm_form.html", {
        "form": form, "title": "Отзыв", "back_url": "orders:crm_reviews", "active": "reviews",
        "delete_url": reverse("orders:crm_review_delete", args=[review.id]) if review else None,
    })


@staff_member_required
@require_POST
def crm_review_delete(request, review_id):
    get_object_or_404(Review, id=review_id).delete()
    messages.success(request, "Отзыв удалён.")
    return redirect("orders:crm_reviews")


@staff_member_required
def crm_faq(request):
    items = FAQItem.objects.all()
    return render(request, "orders/crm_faq.html", {"items": items, "active": "faq"})


@staff_member_required
def crm_faq_form(request, item_id=None):
    item = get_object_or_404(FAQItem, id=item_id) if item_id else None
    if request.method == "POST":
        form = FAQItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Вопрос сохранён.")
            return redirect("orders:crm_faq")
    else:
        form = FAQItemForm(instance=item)
    return render(request, "orders/crm_form.html", {
        "form": form, "title": "Вопрос FAQ", "back_url": "orders:crm_faq", "active": "faq",
        "delete_url": reverse("orders:crm_faq_delete", args=[item.id]) if item else None,
    })


@staff_member_required
@require_POST
def crm_faq_delete(request, item_id):
    get_object_or_404(FAQItem, id=item_id).delete()
    messages.success(request, "Вопрос удалён.")
    return redirect("orders:crm_faq")


@staff_member_required
def crm_contact(request):
    contact = Contact.objects.first()
    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, "Контакты обновлены.")
            return redirect("orders:crm_contact")
    else:
        form = ContactForm(instance=contact)
    return render(request, "orders/crm_form.html", {
        "form": form, "title": "Контактная информация", "back_url": "orders:crm_contact",
        "hide_delete": True, "active": "contact",
    })
