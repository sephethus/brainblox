from django.db import models

class FlashcardSet(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Flashcard(models.Model):
    set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE)
    question = models.TextField()
    explanation = models.TextField(blank=True, null=True)  # Ensure this field is present
    additional_content = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'flashcard'

class Choice(models.Model):
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='choices')
    content = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = 'choice'

    def __str__(self):
        return self.content