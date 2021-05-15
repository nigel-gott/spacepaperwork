from django.utils import timezone


def cron_header_line(code):
    sep = "-" * 5
    print(f"{sep} RUNNING {code} @ {timezone.now()} {sep}")
