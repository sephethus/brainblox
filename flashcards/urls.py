from django.urls import path
from flashcards import views

urlpatterns = [
    path('', views.index, name='index'),
    path('submit_answer/<int:id>/', views.submit_answer, name='submit_answer'),
    path('add/<int:set_id>/', views.add_flashcard, name='add_flashcard'),
    path('edit/<int:id>/', views.edit_flashcard, name='edit_flashcard'),
    path('delete/<int:id>/', views.delete_flashcard, name='delete_flashcard'),
    path('upload/', views.upload_file, name='upload_file'),
    path('sets/<int:set_id>/', views.questions, name='questions'),
    path('add_flashcard_set/', views.add_flashcard_set, name='add_flashcard_set'),
]
