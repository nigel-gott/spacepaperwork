import datetime
from collections import OrderedDict

import pytz
from django.core.exceptions import ValidationError
from django import forms


class TimeZoneFormField(forms.TypedChoiceField):

    @staticmethod
    def coerce_to_pytz(val):
        try:
            return pytz.timezone(val)
        except pytz.UnknownTimeZoneError:
            raise ValidationError("Unknown time zone: '%s'" % val)

    def __init__(self, *args, **kwargs):
        if kwargs.get('display_GMT_offset', False):
            choices = []
            by_hours = OrderedDict()
            dt = datetime.datetime.utcnow()
            for tz in pytz.common_timezones:
                a = self.coerce_to_pytz(tz)
                offset = a.utcoffset(dt)
                offset_days = offset.days
                offset_hours = offset_days * 24 + offset.seconds / 3600.0
                name = "{:s} (UTC {:+d}:{:02d})".format(tz.replace('_', ' '),
                                                        int(offset_hours),
                                                        int((offset_hours % 1) * 60))
                by_hours[offset_hours] = (tz,name)
                choices.append((tz, name))
            choices = [v for k, v in sorted(by_hours.items(), key=lambda item: item[0])]

        else:
            choices = [(tz, tz.replace('_', ' ')) for tz in pytz.common_timezones]

        defaults = {
            'coerce': self.coerce_to_pytz,
            'choices': choices,
            'empty_value': None,
        }
        if 'display_GMT_offset' in kwargs:
            del kwargs['display_GMT_offset']
        defaults.update(kwargs)
        super(TimeZoneFormField, self).__init__(*args, **defaults)
