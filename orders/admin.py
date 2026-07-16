from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CallLog, Contact, FAQItem, Order, PortfolioItem, Review, Service,
    ServiceCategory,
)

admin.site.site_header = "Управление сервисом по ремонту и сборке ПК"
admin.site.site_title = "Админка"
admin.site.index_title = "Панель управления"


# ---------- Прайс-лист ----------

class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    fields = ("name", "price", "price_from", "is_active", "order")


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "services_count")
    list_editable = ("order",)
    inlines = [ServiceInline]

    def services_count(self, obj):
        return obj.services.count()
    services_count.short_description = "Кол-во услуг"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "price_from", "is_active", "order")
    list_editable = ("price", "is_active", "order")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


# ---------- Портфолио ----------

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ("title", "date_done", "is_published", "order", "preview")
    list_editable = ("is_published", "order")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    readonly_fields = ("preview_large",)
    fields = (
        "title", "description", "tags",
        "before_image", "image", "preview_large",
        "date_done", "is_published", "order",
    )

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.image.url)
        return "—"
    preview.short_description = "Фото"

    def preview_large(self, obj):
        parts = []
        if obj.before_image:
            parts.append(format_html('<img src="{}" style="max-height:200px;border-radius:6px;margin-right:10px;" />', obj.before_image.url))
        if obj.image:
            parts.append(format_html('<img src="{}" style="max-height:200px;border-radius:6px;" />', obj.image.url))
        return format_html("".join(str(p) for p in parts)) if parts else "Фото не загружено"
    preview_large.short_description = "Предпросмотр (до / после)"


# ---------- Отзывы ----------

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("client_name", "rating", "service_label", "is_verified", "created_at", "is_published")
    list_editable = ("is_published", "is_verified")
    list_filter = ("rating", "is_published", "is_verified")
    search_fields = ("client_name", "text")


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_published")
    list_editable = ("order", "is_published")
    search_fields = ("question", "answer")


# ---------- Заявки (мини-CRM) ----------

STATUS_COLORS = {
    "new": "#0d6efd",
    "calling": "#fd7e14",
    "confirmed": "#6f42c1",
    "in_progress": "#20c997",
    "waiting_parts": "#adb5bd",
    "ready": "#0dcaf0",
    "done": "#198754",
    "canceled": "#dc3545",
}


class CallLogInline(admin.TabularInline):
    model = CallLog
    extra = 1
    fields = ("date", "note")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_list_template = "admin/orders/order_changelist.html"
    list_display = (
        "id", "name", "phone", "service", "status_badge", "priority",
        "estimated_price", "created_at", "updated_at",
    )
    list_display_links = ("id", "name")
    list_editable = ("priority",)
    list_filter = ("status", "priority", "service__category", "created_at")
    search_fields = ("name", "phone", "email", "comment")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    inlines = [CallLogInline]
    actions = ["mark_calling", "mark_confirmed", "mark_in_progress", "mark_done", "mark_canceled"]

    fieldsets = (
        ("Данные клиента", {
            "fields": ("name", "phone", "email", "service", "comment")
        }),
        ("Ведение заявки", {
            "fields": ("status", "priority", "manager_comment", "estimated_price")
        }),
        ("Служебная информация", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:12px;white-space:nowrap;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Статус"

    def _set_status(self, request, queryset, status, label):
        updated = queryset.update(status=status)
        self.message_user(request, f"Статус изменён на «{label}» у {updated} заявок.")

    def mark_calling(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CALLING, "Нужно перезвонить")
    mark_calling.short_description = "Отметить: нужно перезвонить"

    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CONFIRMED, "Подтверждена")
    mark_confirmed.short_description = "Отметить: подтверждена"

    def mark_in_progress(self, request, queryset):
        self._set_status(request, queryset, Order.Status.IN_PROGRESS, "В работе")
    mark_in_progress.short_description = "Отметить: в работе"

    def mark_done(self, request, queryset):
        self._set_status(request, queryset, Order.Status.DONE, "Завершена")
    mark_done.short_description = "Отметить: завершена"

    def mark_canceled(self, request, queryset):
        self._set_status(request, queryset, Order.Status.CANCELED, "Отменена")
    mark_canceled.short_description = "Отметить: отменена"


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("order", "date", "note_short")
    list_filter = ("date",)
    search_fields = ("note", "order__name", "order__phone")

    def note_short(self, obj):
        return (obj.note[:60] + "…") if len(obj.note) > 60 else obj.note
    note_short.short_description = "Заметка"


# ---------- Контакты ----------

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("phone", "email", "address", "work_hours")

    def has_add_permission(self, request):
        # Разрешаем только одну запись с контактами
        return Contact.objects.count() == 0
