from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ServiceCategory(models.Model):
    """Категория услуг, например 'Сборка ПК', 'Диагностика', 'Ремонт'."""
    name = models.CharField("Название категории", max_length=120)
    order = models.PositiveIntegerField("Порядок вывода", default=0)

    class Meta:
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    """Позиция прайс-листа."""
    category = models.ForeignKey(
        ServiceCategory, verbose_name="Категория",
        related_name="services", on_delete=models.CASCADE
    )
    name = models.CharField("Название услуги", max_length=200)
    description = models.CharField("Краткое описание", max_length=300, blank=True)
    price = models.DecimalField("Цена, BYN", max_digits=8, decimal_places=2)
    price_from = models.BooleanField("Цена от (не фиксированная)", default=False)
    is_active = models.BooleanField("Показывать на сайте", default=True)
    order = models.PositiveIntegerField("Порядок вывода", default=0)

    class Meta:
        verbose_name = "Услуга / позиция прайс-листа"
        verbose_name_plural = "Прайс-лист"
        ordering = ["category__order", "order", "name"]

    def __str__(self):
        return f"{self.name} — {self.price}BYN"


class PortfolioItem(models.Model):
    """Пример выполненной работы — с фото «до» и «после» для слайдера сравнения."""
    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание работы", blank=True)
    before_image = models.ImageField(
        "Фото «до»", upload_to="portfolio/before/", blank=True, null=True,
        help_text="Необязательно. Если не загружено — слайдер сравнения не показывается."
    )
    image = models.ImageField("Фото «после»", upload_to="portfolio/", blank=True, null=True)
    tags = models.CharField(
        "Метки", max_length=200, blank=True,
        help_text="Через запятую, например: 1440p / игры, 3 часа работы, Гарантия 12 мес"
    )
    date_done = models.DateField("Дата выполнения", default=timezone.now)
    is_published = models.BooleanField("Опубликовано", default=True)
    order = models.PositiveIntegerField("Порядок вывода", default=0)

    class Meta:
        verbose_name = "Пример работы"
        verbose_name_plural = "Примеры работ"
        ordering = ["order", "-date_done"]

    def __str__(self):
        return self.title

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class Review(models.Model):
    """Отзыв клиента."""
    client_name = models.CharField("Имя клиента", max_length=120)
    text = models.TextField("Текст отзыва")
    rating = models.PositiveSmallIntegerField(
        "Оценка", default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    service_label = models.CharField(
        "Услуга (метка)", max_length=80, blank=True,
        help_text="Например: Сборка ПК, Ремонт, Диагностика"
    )
    is_verified = models.BooleanField("Подтверждённый заказ", default=True)
    created_at = models.DateField("Дата", default=timezone.now)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client_name} ({self.rating}★)"


class Order(models.Model):
    """Заявка клиента — основной объект мини-CRM."""

    class Status(models.TextChoices):
        NEW = "new", "Новая заявка"
        CALLING = "calling", "Нужно перезвонить"
        CONFIRMED = "confirmed", "Подтверждена"
        IN_PROGRESS = "in_progress", "В работе"
        WAITING_PARTS = "waiting_parts", "Ожидание запчастей"
        READY = "ready", "Готово, ждёт клиента"
        DONE = "done", "Завершена"
        CANCELED = "canceled", "Отменена"

    class Priority(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Обычный"
        HIGH = "high", "Высокий"

    name = models.CharField("Имя клиента", max_length=120)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)
    service = models.ForeignKey(
        Service, verbose_name="Интересующая услуга",
        related_name="orders", on_delete=models.SET_NULL,
        null=True, blank=True
    )
    comment = models.TextField("Комментарий клиента", blank=True)

    status = models.CharField(
        "Статус", max_length=20, choices=Status.choices, default=Status.NEW
    )
    priority = models.CharField(
        "Приоритет", max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    manager_comment = models.TextField(
        "Внутренний комментарий менеджера", blank=True,
        help_text="Не видно клиенту. Общие заметки по заявке."
    )
    estimated_price = models.DecimalField(
        "Итоговая стоимость, BYN", max_digits=8, decimal_places=2,
        null=True, blank=True
    )

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заявка №{self.pk} — {self.name} ({self.get_status_display()})"


class CallLog(models.Model):
    """Журнал звонков/контактов по заявке — для отслеживания истории общения."""
    order = models.ForeignKey(
        Order, verbose_name="Заявка", related_name="call_logs",
        on_delete=models.CASCADE
    )
    date = models.DateTimeField("Дата и время", default=timezone.now)
    note = models.TextField("Что обсуждалось / результат звонка")

    class Meta:
        verbose_name = "Запись звонка"
        verbose_name_plural = "Журнал звонков"
        ordering = ["-date"]

    def __str__(self):
        return f"Звонок по заявке №{self.order_id} от {self.date:%d.%m.%Y %H:%M}"


class Contact(models.Model):
    """Контактные данные, выводятся на сайте. Обычно одна запись."""
    phone = models.CharField("Телефон", max_length=32)
    telegram = models.CharField("Telegram", max_length=120, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    address = models.CharField("Адрес / город", max_length=200, blank=True)
    work_hours = models.CharField("Часы работы", max_length=120, blank=True)

    class Meta:
        verbose_name = "Контактная информация"
        verbose_name_plural = "Контактная информация"

    def __str__(self):
        return "Контакты"


class FAQItem(models.Model):
    """Вопрос-ответ для блока FAQ на сайте."""
    question = models.CharField("Вопрос", max_length=250)
    answer = models.TextField("Ответ")
    order = models.PositiveIntegerField("Порядок вывода", default=0)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Вопрос FAQ"
        verbose_name_plural = "FAQ — частые вопросы"
        ordering = ["order"]

    def __str__(self):
        return self.question
