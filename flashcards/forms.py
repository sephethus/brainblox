from django import forms
from .models import Flashcard, Choice, FlashcardSet

class FlashcardSetForm(forms.ModelForm):
    class Meta:
        model = FlashcardSet
        fields = ['name']


class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ['question', 'explanation', 'additional_content']
        widgets = {
            'question': forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'style': 'display:none;'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'additional_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'style': 'display:none;'}),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['content', 'is_correct']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Optional: Formset to handle multiple choices dynamically
ChoiceFormSet = forms.modelformset_factory(
    Choice,
    fields=('content', 'is_correct'),
    extra=7,
    can_delete=True  # To allow deletion of existing choices
)