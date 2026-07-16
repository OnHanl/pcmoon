from django import forms
from .models import (
    Contact, FAQItem, Order, PortfolioItem, Review, Service, ServiceCategory,
)

# Общий класс для полей ввода в CRM-панели (тёмная тема, см. crm_base.html)
CRM_INPUT = "cf-input"
CRM_TEXTAREA = "cf-input cf-textarea"


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["name", "phone", "email", "service", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control", "id": "f-name", "placeholder": "Как к вам обращаться"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control", "id": "f-phone", "placeholder": "+375 XXX XXXXX"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control", "id": "f-email", "placeholder": "Email (необязательно)"
            }),
            "service": forms.Select(attrs={"class": "form-select", "id": "f-service"}),
            "comment": forms.Textarea(attrs={
                "class": "form-control", "id": "f-comment", "rows": 3,
                "placeholder": "Опишите проблему или что нужно собрать"
            }),
        }
        labels = {
            "name": "Имя",
            "phone": "Телефон",
            "email": "Email",
            "service": "Услуга",
            "comment": "Комментарий",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].required = False
        self.fields["service"].empty_label = "Выберите услугу (необязательно)"
        self.fields["email"].required = False
        self.fields["comment"].required = False


# ---------- Формы для CRM-панели (/dashboard/...) ----------

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ["name", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": CRM_INPUT}),
            "order": forms.NumberInput(attrs={"class": CRM_INPUT}),
        }
        labels = {"name": "Название категории", "order": "Порядок вывода"}


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["category", "name", "description", "price", "price_from", "is_active", "order"]
        widgets = {
            "category": forms.Select(attrs={"class": CRM_INPUT}),
            "name": forms.TextInput(attrs={"class": CRM_INPUT}),
            "description": forms.TextInput(attrs={"class": CRM_INPUT}),
            "price": forms.NumberInput(attrs={"class": CRM_INPUT, "step": "0.01"}),
            "order": forms.NumberInput(attrs={"class": CRM_INPUT}),
        }
        labels = {
            "category": "Категория", "name": "Название услуги",
            "description": "Краткое описание", "price": "Цена, BYN",
            "price_from": "Цена «от» (не фиксированная)",
            "is_active": "Показывать на сайте", "order": "Порядок вывода",
        }


class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ["title", "description", "tags", "before_image", "image", "date_done", "is_published", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": CRM_INPUT}),
            "description": forms.Textarea(attrs={"class": CRM_TEXTAREA, "rows": 3}),
            "tags": forms.TextInput(attrs={"class": CRM_INPUT, "placeholder": "1440p / игры, 3 часа работы, Гарантия 12 мес"}),
            "date_done": forms.DateInput(format="%Y-%m-%d", attrs={"class": CRM_INPUT, "type": "date"}),
            "order": forms.NumberInput(attrs={"class": CRM_INPUT}),
        }
        labels = {
            "title": "Заголовок", "description": "Описание работы", "tags": "Метки (через запятую)",
            "before_image": "Фото «до» (необязательно)", "image": "Фото «после»",
            "date_done": "Дата выполнения", "is_published": "Опубликовано", "order": "Порядок вывода",
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["client_name", "text", "rating", "service_label", "is_verified", "created_at", "is_published"]
        widgets = {
            "client_name": forms.TextInput(attrs={"class": CRM_INPUT}),
            "text": forms.Textarea(attrs={"class": CRM_TEXTAREA, "rows": 4}),
            "rating": forms.Select(attrs={"class": CRM_INPUT}, choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "service_label": forms.TextInput(attrs={"class": CRM_INPUT, "placeholder": "Сборка ПК, Ремонт, Диагностика…"}),
            "created_at": forms.DateInput(format="%Y-%m-%d", attrs={"class": CRM_INPUT, "type": "date"}),
        }
        labels = {
            "client_name": "Имя клиента", "text": "Текст отзыва", "rating": "Оценка",
            "service_label": "Услуга (метка)", "is_verified": "Подтверждённый заказ",
            "created_at": "Дата", "is_published": "Опубликовано",
        }


class FAQItemForm(forms.ModelForm):
    class Meta:
        model = FAQItem
        fields = ["question", "answer", "order", "is_published"]
        widgets = {
            "question": forms.TextInput(attrs={"class": CRM_INPUT}),
            "answer": forms.Textarea(attrs={"class": CRM_TEXTAREA, "rows": 4}),
            "order": forms.NumberInput(attrs={"class": CRM_INPUT}),
        }
        labels = {"question": "Вопрос", "answer": "Ответ", "order": "Порядок вывода", "is_published": "Опубликовано"}


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["phone", "telegram", "whatsapp", "email", "address", "work_hours"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": CRM_INPUT, "placeholder": "+375 XXX XXXXX"}),
            "telegram": forms.TextInput(attrs={"class": CRM_INPUT, "placeholder": "@username"}),
            "whatsapp": forms.TextInput(attrs={"class": CRM_INPUT, "placeholder": "+375 XXX XXXXX"}),
            "email": forms.EmailInput(attrs={"class": CRM_INPUT}),
            "address": forms.TextInput(attrs={"class": CRM_INPUT}),
            "work_hours": forms.TextInput(attrs={"class": CRM_INPUT, "placeholder": "Пн–Сб, 10:00–20:00"}),
        }
        labels = {
            "phone": "Телефон", "telegram": "Telegram", "whatsapp": "WhatsApp",
            "email": "Email", "address": "Адрес / город", "work_hours": "Часы работы",
        }
