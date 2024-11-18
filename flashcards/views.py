from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import FlashcardSet, Flashcard, Choice
from .forms import FlashcardForm, ChoiceForm, ChoiceFormSet, FlashcardSetForm
from django.core.files.storage import default_storage
import os

def index(request):
    sets = FlashcardSet.objects.all()
    return render(request, 'index.html', {'sets': sets})

def questions(request, set_id):
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id)
    flashcards = flashcard_set.flashcard_set.all()
    return render(request, 'questions.html', {
        'flashcards': flashcards,
        'set_id': set_id,  # Pass set_id to the template
    })

def submit_answer(request, id):
    flashcard = Flashcard.objects.get(pk=id)
    user_answers = request.POST.getlist('user_answer')
    
    correct_choices = [choice for choice in flashcard.choices.filter(is_correct=True)]
    correct_choice_ids = {str(choice.id) for choice in correct_choices}
    user_answer_ids = set(user_answers)

    if correct_choice_ids == user_answer_ids:
        feedback = 'correct'
        messages.success(request, 'Correct!')  # Use Django messages
    else:
        feedback = 'incorrect'
        messages.error(request, 'Incorrect.')

    # Serialize messages to include them in the JSON response
    messages_list = list(messages.get_messages(request))
    messages_data = [{'level': message.level_tag, 'message': message.message} for message in messages_list]

    return JsonResponse({
        'feedback': feedback,
        'messages': messages_data,  # Include messages in the response
        'correct_choice_ids': list(correct_choice_ids),
        'card_id': flashcard.id,
        'user_answer_ids': list(user_answer_ids),
        'show_explanation': True,
        'explanation': flashcard.explanation
    })

def add_flashcard(request, set_id=None):
    # Fetch the flashcard set based on set_id or let user choose
    flashcard_set = None
    if set_id:
        flashcard_set = get_object_or_404(FlashcardSet, id=set_id)

    if request.method == 'POST':
        flashcard_form = FlashcardForm(request.POST, initial={'set': flashcard_set})
        choice_formset = ChoiceFormSet(request.POST, queryset=Choice.objects.none())

        if flashcard_form.is_valid() and choice_formset.is_valid():
            # Save the flashcard and associate it with the selected flashcard set
            flashcard = flashcard_form.save(commit=False)
            flashcard.set = flashcard_set
            flashcard.save()
            
            # Save associated choices
            for form in choice_formset:
                if form.cleaned_data:
                    choice = form.save(commit=False)
                    choice.flashcard = flashcard
                    choice.save()
                    
            return redirect('questions', set_id=flashcard.set.id)  # Redirect to the flashcard set

    else:
        flashcard_form = FlashcardForm(initial={'set': flashcard_set})
        choice_formset = ChoiceFormSet(queryset=Choice.objects.none())

    return render(request, 'add_flashcard.html', {
        'flashcard_form': flashcard_form,
        'choice_formset': choice_formset,
        'set_id': set_id,
    })

def add_flashcard_set(request):
    if request.method == 'POST':
        form = FlashcardSetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')  # Redirect to the index page or wherever appropriate
    else:
        form = FlashcardSetForm()
    return render(request, 'add_flashcard_set.html', {'form': form})

def edit_flashcard(request, id):
    flashcard = Flashcard.objects.get(pk=id)  # Get Id
    if request.method == 'POST':
        flashcard_form = FlashcardForm(request.POST, instance=flashcard)
        choice_formset = ChoiceFormSet(request.POST, queryset=flashcard.choices.all())
        print("Is POST")

        # Print form errors if validation fails
        if not flashcard_form.is_valid():
            print("Flashcard form errors:", flashcard_form.errors)
        
        if not all(cf.is_valid() for cf in choice_formset):
            print("Choice formset errors:", [cf.errors for cf in choice_formset])
            
        valid_choices = True
        for cf in choice_formset:
            if cf.cleaned_data and not cf.cleaned_data.get('content') and cf.instance.pk:
                print(f"Deleting choice {cf.instance.pk}")
                cf.instance.delete()  # Delete choices where content is empty
            elif cf.cleaned_data.get('content'):
                if not cf.is_valid():  # Validate only forms with content
                    print("Invalid choice form:", cf.errors)
                    valid_choices = False

        # Only proceed if both the flashcard form and formset are valid
        if flashcard_form.is_valid() and valid_choices:
            flashcard_form.save()

            for cf in choice_formset:
                if cf.cleaned_data.get('content'):
                    # Save valid forms
                    choice = cf.save(commit=False)
                    choice.flashcard = flashcard
                    choice.save()

            return redirect('index')
    else:
        flashcard_form = FlashcardForm(instance=flashcard)
        choice_formset = ChoiceFormSet(queryset=flashcard.choices.all())

    return render(request, 'edit_flashcard.html', {
        'flashcard_form': flashcard_form,
        'choice_formset': choice_formset,
        'flashcard': flashcard
    })


def delete_flashcard(request, id):
    flashcard = get_object_or_404(Flashcard, pk=id)
    flashcard.delete()
    return redirect('index')

def upload_file(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file part'}, status=400)
    
    file = request.FILES['file']
    if file.name == '':
        return JsonResponse({'error': 'No selected file'}, status=400)
    
    # Save file with secure filename
    filename = default_storage.save(file.name, file)
    file_url = default_storage.url(filename)
    
    return JsonResponse({'location': file_url})