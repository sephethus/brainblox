import re, sqlite3
from flashcards.models import FlashcardSet, Flashcard, Choice  # Adjust import as needed
from flashcards.models import Flashcard as OldFlashcard

OLD_DB_PATH = '../../flash/flashcards.db'
conn = sqlite3.connect(OLD_DB_PATH)
cursor = conn.cursor()

def migrate_flashcards():
    # Connect to the old SQLite database
    query = "SELECT id, question, answer, additional_content FROM flashcard"
    cursor.execute(query)
    flashcards = cursor.fetchall()


    # 1. Create Flashcard Sets for GCP and Azure

    gcp_set, created = FlashcardSet.objects.get_or_create(name="Google Professional Cloud Architect")
    # azure_set, created = FlashcardSet.objects.get_or_create(name="AZ-305")

    # Find the options first and separate those out into the choices. Return the question only.
    
    for old_card in flashcards:
        new_flashcard = Flashcard.objects.create(
            set=gcp_set,
            question=old_card.question,
            explanation=old_card.answer,
            additional_content=old_card.additional_content
        )
        parse_and_create_choices(new_flashcard, old_card.answer)

    # 3. Migrate Azure Flashcards
    # azure_flashcards = OldFlashcard.query.filter_by(set_name="Azure Questions")  # Adjust filter as needed
    # for old_card in azure_flashcards:
    #     new_flashcard = Flashcard.objects.create(
    #         set=azure_set,
    #         question=old_card.question,
    #         explanation=old_card.answer,
    #         additional_content=old_card.additional_content
    #     )
    #     parse_and_create_choices(new_flashcard, old_card.answer)

def migrate_set(cursor, old_set_name, new_set):
    """
    Migrate a specific set of flashcards from the old database to the new one.
    """
    # Query for flashcards in the specified set
    query = "SELECT id, question, answer, additional_content FROM flashcard"
    cursor.execute(query, (old_set_name,))

    for card_id, question, answer, additional_content in flashcards:
        flashcards = cursor.fetchall()
        question_only, choices_only = split_question_and_choices(question)
        # Create the flashcard in the new database

        new_flashcard = Flashcard.objects.create(
            set=new_set,
            question=question_only,
            explanation=answer,
            additional_content=additional_content
        )

        # Parse answer text to create choices and set question
        parse_and_create_choices(new_flashcard, choices_only)

def split_question_and_choices(question_text):
    # Regex pattern to split question text at the first choice label
    choice_pattern = r'([A-G]\.\s)'
    split_text = re.split(choice_pattern, question_text, maxsplit=1)

    question_only = split_text[0].strip()  # Text before first answer label
    choices_only = ''.join(split_text[1:]).strip()  # Text after first answer label

    return question_only, choices_only

def parse_and_create_choices(flashcard, choices_only):
    # Iterate over split parts, combining each label with its following text
    choice_pattern = r'([A-G]\.\s)'
    parts = re.split(choice_pattern, choices_only)
    choices = [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]

    for label, content in choices:
        is_correct = "correct" in content.lower()  # Customize based on actual content
        Choice.objects.create(
            flashcard=flashcard,
            content=content.replace('correct', '').strip(),  # Clean "correct" label if included
            is_correct=is_correct
        )