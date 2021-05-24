from django.utils import timezone


def cron_header_line(code):
    sep = "-" * 5
    print(f"{sep} RUNNING {code} @ {timezone.now()} {sep}")


class PassRequestToFormViewMixin:
    def get_form_kwargs(self):
        # noinspection PyUnresolvedReferences
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs