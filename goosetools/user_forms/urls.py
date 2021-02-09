from django.urls import path

from goosetools.user_forms.views import (
    FormCreate,
    FormDelete,
    FormDetail,
    FormList,
    FormUpdate,
)

app_name = "user_forms"

urlpatterns = [
    path("form/", FormList.as_view(), name="form-list"),
    path("form/<int:pk>/", FormDetail.as_view(), name="form-detail"),
    path("form/create/", FormCreate.as_view(), name="form-create"),
    path("form/<int:pk>/update", FormUpdate.as_view(), name="form-update"),
    path("form/<int:pk>/delete/", FormDelete.as_view(), name="form-delete"),
]
