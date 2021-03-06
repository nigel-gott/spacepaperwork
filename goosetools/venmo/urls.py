from django.urls import path

from goosetools.venmo.views import (
    VirtualCurrencyCreateView,
    VirtualCurrencyDeleteView,
    VirtualCurrencyDetailView,
    VirtualCurrencyListView,
    VirtualCurrencyUpdateView,
    approve_transaction,
    deny_transaction,
    deposit,
    other_dashboard,
    other_user_transactions_list,
    own_dashboard,
    pending,
    pending_list,
    transfer,
    withdraw,
)

app_name = "venmo"

urlpatterns = [
    path("dashboard/", own_dashboard, name="dashboard"),
    path("user/<int:pk>/dashboard/", other_dashboard, name="other_dashboard"),
    path(
        "user/<int:pk>/transactions",
        other_user_transactions_list,
        name="transactions-list",
    ),
    path("transactions/pending", pending_list, name="pending-list"),
    path("withdraw/", withdraw, name="withdraw"),
    path("deposit/", deposit, name="deposit"),
    path("transfer/", transfer, name="transfer"),
    path("pending/", pending, name="pending"),
    path("pending/<int:pk>/approve", approve_transaction, name="approve_transaction"),
    path("pending/<int:pk>/deny", deny_transaction, name="deny_transaction"),
    path("currency/", VirtualCurrencyListView.as_view(), name="currency-list"),
    path(
        "currency/<int:pk>/",
        VirtualCurrencyDetailView.as_view(),
        name="currency-detail",
    ),
    path(
        "currency/create/", VirtualCurrencyCreateView.as_view(), name="currency-create"
    ),
    path(
        "currency/<int:pk>/update/",
        VirtualCurrencyUpdateView.as_view(),
        name="currency-update",
    ),
    path(
        "currency/<int:pk>/delete/",
        VirtualCurrencyDeleteView.as_view(),
        name="currency-delete",
    ),
]
