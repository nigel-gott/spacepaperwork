from django.urls import path

from goosetools.venmo.views import transactions

app_name = "venmo"

urlpatterns = [
    path("transactions/", transactions, name="transactions"),
]
