from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from goosetools.user_forms.forms import FormQuestionFormSet, GeneratedForm
from goosetools.user_forms.models import DynamicForm


class FormList(ListView):
    queryset = DynamicForm.objects.order_by("-title")
    context_object_name = "form_list"


class FormCreate(CreateView):
    model = DynamicForm
    fields = ["title", "description"]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["questions"] = FormQuestionFormSet(self.request.POST)
        else:
            data["questions"] = FormQuestionFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context["questions"]
        if questions.is_valid():
            response = super().form_valid(form)
            questions.instance = self.object  # type: ignore
            questions.save()
            return response
        else:
            return super().form_invalid(form)


class FormUpdate(UpdateView):
    model = DynamicForm
    fields = ["title", "description"]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["questions"] = FormQuestionFormSet(self.request.POST, instance=self.object)  # type: ignore
            data["questions"].full_clean()
        else:
            data["questions"] = FormQuestionFormSet(instance=self.object)  # type: ignore
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        questions = context["questions"]
        if questions.is_valid():
            response = super().form_valid(form)
            questions.instance = self.object  # type: ignore
            questions.save()
            return response
        else:
            return super().form_invalid(form)


class FormDelete(DeleteView):
    model = DynamicForm
    success_url = reverse_lazy("user_forms:form-list")


class FormDetail(DetailView):
    model = DynamicForm

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["form"] = GeneratedForm(self.object)  # type: ignore
        return data
