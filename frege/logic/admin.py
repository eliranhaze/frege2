from django.contrib import admin

from .models import (
    Chapter,
    OpenQuestion,
    FormulationQuestion,
    ChoiceQuestion,
    TruthTableQuestion,
    DeductionQuestion,
)

admin.site.register(Chapter)
admin.site.register(OpenQuestion)
admin.site.register(FormulationQuestion)
admin.site.register(ChoiceQuestion)
admin.site.register(TruthTableQuestion)
admin.site.register(DeductionQuestion)
