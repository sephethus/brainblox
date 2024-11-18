from django.contrib import admin
from .models import Flashcard, Choice

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1  # How many extra empty choices to display in the admin by default

class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('question', 'explanation')  # Columns to display in the admin list view
    search_fields = ['question', 'explanation']  # Add search capability by these fields
    inlines = [ChoiceInline]  # Include the choices inline when editing a flashcard

admin.site.register(Flashcard, FlashcardAdmin)
admin.site.register(Choice)