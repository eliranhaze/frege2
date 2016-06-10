from django.contrib import admin

from .models import Question

class QuestionAdmin(admin.ModelAdmin):
#    fields = ['date', 'text']
    fieldsets = [
        (None,               {'fields':['text']}),
        ('Date information', {'fields':['date']}),
    ] 


admin.site.register(Question, QuestionAdmin)

