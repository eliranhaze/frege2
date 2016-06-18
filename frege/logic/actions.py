# -*- coding: utf-8 -*-
import csv

from django.http import HttpResponse

"""
Based on: https://djangosnippets.org/snippets/2369/
"""

# TODO: i don't have to use this general purpose function. can just write my own with all i need
def export_as_csv_action(description="ייצוא נתונים לאקסל",
                         fields=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        """
        opts = modeladmin.model._meta
        filename = unicode(opts).replace('.', '_')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % filename

        writer = csv.writer(response)
        if header:
            writer.writerow(fields.keys())
        for obj in queryset:
            writer.writerow([unicode(getattr(obj, field)).encode("utf-8","replace") for field in fields.values()])
        return response
    export_as_csv.short_description = description
    return export_as_csv
