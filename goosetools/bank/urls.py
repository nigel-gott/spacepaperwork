from django.urls import path

from goosetools.bank.views import own_user_transactions, user_transactions

urlpatterns = [
    path("transactions/own/", own_user_transactions, name="own_user_transactions"),
    path("transactions/<int:pk>/", user_transactions, name="user_transactions"),
]
