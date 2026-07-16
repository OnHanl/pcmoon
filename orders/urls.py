from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.index, name="index"),

    # CRM: заявки (kanban)
    path("dashboard/", views.dashboard, name="dashboard"),
    path("api/orders/", views.api_orders, name="api_orders"),
    path("api/orders/<int:order_id>/status/", views.api_order_set_status, name="api_order_set_status"),
    path("api/orders/<int:order_id>/calls/", views.api_order_add_call, name="api_order_add_call"),

    # CRM: прайс-лист
    path("dashboard/prices/", views.crm_prices, name="crm_prices"),
    path("dashboard/prices/category/new/", views.crm_category_form, name="crm_category_add"),
    path("dashboard/prices/category/<int:category_id>/edit/", views.crm_category_form, name="crm_category_edit"),
    path("dashboard/prices/category/<int:category_id>/delete/", views.crm_category_delete, name="crm_category_delete"),
    path("dashboard/prices/service/new/", views.crm_service_form, name="crm_service_add"),
    path("dashboard/prices/service/<int:service_id>/edit/", views.crm_service_form, name="crm_service_edit"),
    path("dashboard/prices/service/<int:service_id>/delete/", views.crm_service_delete, name="crm_service_delete"),

    # CRM: портфолио
    path("dashboard/portfolio/", views.crm_portfolio, name="crm_portfolio"),
    path("dashboard/portfolio/new/", views.crm_portfolio_form, name="crm_portfolio_add"),
    path("dashboard/portfolio/<int:item_id>/edit/", views.crm_portfolio_form, name="crm_portfolio_edit"),
    path("dashboard/portfolio/<int:item_id>/delete/", views.crm_portfolio_delete, name="crm_portfolio_delete"),

    # CRM: отзывы
    path("dashboard/reviews/", views.crm_reviews, name="crm_reviews"),
    path("dashboard/reviews/new/", views.crm_review_form, name="crm_review_add"),
    path("dashboard/reviews/<int:review_id>/edit/", views.crm_review_form, name="crm_review_edit"),
    path("dashboard/reviews/<int:review_id>/delete/", views.crm_review_delete, name="crm_review_delete"),

    # CRM: FAQ
    path("dashboard/faq/", views.crm_faq, name="crm_faq"),
    path("dashboard/faq/new/", views.crm_faq_form, name="crm_faq_add"),
    path("dashboard/faq/<int:item_id>/edit/", views.crm_faq_form, name="crm_faq_edit"),
    path("dashboard/faq/<int:item_id>/delete/", views.crm_faq_delete, name="crm_faq_delete"),

    # CRM: контакты
    path("dashboard/contact/", views.crm_contact, name="crm_contact"),
]
