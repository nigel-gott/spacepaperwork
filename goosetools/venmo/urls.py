from django.urls import path

from goosetools.venmo.views import (
    TransferMethodCreateView,
    TransferMethodDeleteView,
    TransferMethodDetailView,
    TransferMethodListView,
    TransferMethodSelectCreateView,
    TransferMethodUpdateView,
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
    path("<str:ccy>/dashboard/", own_dashboard, name="dashboard"),
    path("<str:ccy>/user/<int:pk>/dashboard/", other_dashboard, name="other_dashboard"),
    path(
        "<str:ccy>/user/<int:pk>/transactions",
        other_user_transactions_list,
        name="transactions-list",
    ),
    path("<str:ccy>/transactions/pending", pending_list, name="pending-list"),
    path("<str:ccy>/withdraw/", withdraw, name="withdraw"),
    path("<str:ccy>/deposit/", deposit, name="deposit"),
    path("<str:ccy>/transfer/", transfer, name="transfer"),
    path("<str:ccy>/pending/", pending, name="pending"),
    path(
        "<str:ccy>/pending/<int:pk>/approve",
        approve_transaction,
        name="approve_transaction",
    ),
    path("<str:ccy>/pending/<int:pk>/deny", deny_transaction, name="deny_transaction"),
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
    path("transfer/", TransferMethodListView.as_view(), name="transfer-list"),
    path(
        "transfer/create/", TransferMethodCreateView.as_view(), name="transfer-create"
    ),
    path(
        "transfer/<int:pk>/update/",
        TransferMethodUpdateView.as_view(),
        name="transfer-update",
    ),
    path(
        "transfer/<int:pk>/delete/",
        TransferMethodDeleteView.as_view(),
        name="transfer-delete",
    ),
    path(
        "transfer/select/",
        TransferMethodSelectCreateView.as_view(),
        name="transfer-select",
    ),
    path(
        "transfer/<int:pk>/",
        TransferMethodDetailView.as_view(),
        name="transfer-detail",
    ),
]
