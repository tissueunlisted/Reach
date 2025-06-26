# C:\entc\core_app\management\commands\import_flashcards.py

import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from core_app.models import FlashcardSet, Flashcard

User = get_user_model() # Get the active user model

class Command(BaseCommand):
    help = 'Imports flashcard sets and flashcards from a CSV file.'

    def add_arguments(self, parser):
        # Define the argument for the CSV file path
        parser.add_argument('csv_file', type=str, help='The path to the CSV file containing flashcard data.')
        # Optional argument to specify a user to associate flashcards with
        parser.add_argument(
            '--user',
            type=str,
            default='admin', # Default to 'admin' username
            help='Username of the teacher to associate imported flashcards with. Defaults to "admin".'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        username = options['user']

        try:
            # Attempt to find the specified user, correctly traversing to the UserProfile
            teacher = User.objects.get(username=username, profile__user_type='teacher')
        except User.DoesNotExist:
            raise CommandError(f'Teacher user "{username}" does not exist or is not a teacher. Please create one or specify a valid teacher username using --user.')
        except Exception as e:
            raise CommandError(f"An unexpected error occurred during teacher lookup: {e}")
        
        self.stdout.write(self.style.SUCCESS(f'Importing flashcards for teacher: {teacher.username}'))

        # Use a dictionary to store flashcard sets created during import to avoid duplicates
        flashcard_sets_cache = {}

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check for required columns
                required_headers = [
                    'set_title', 'set_description', 'set_subject', 'set_topic',
                    'set_year_group', 'question_text', 'answer_text'
                ]
                if not all(header in reader.fieldnames for header in required_headers):
                    missing = [header for header in required_headers if header not in reader.fieldnames]
                    # CORRECTED LINE BELOW: Removed 'actomyosin'
                    raise CommandError(f"CSV file is missing required headers: {', '.join(missing)}. Expected headers: {', '.join(required_headers)}")

                flashcards_imported_count = 0
                sets_created_count = 0

                for row in reader:
                    set_title = row['set_title']
                    set_description = row['set_description']
                    set_subject = row['set_subject']
                    set_topic = row['set_topic']
                    set_year_group = row['set_year_group']
                    question_text = row['question_text']
                    answer_text = row['answer_text']

                    # Validate required fields for the flashcard itself
                    if not question_text or not answer_text:
                        self.stdout.write(self.style.WARNING(f"Skipping row due to missing question_text or answer_text: {row}"))
                        continue

                    try:
                        with transaction.atomic():
                            # Get or create the FlashcardSet
                            if set_title not in flashcard_sets_cache:
                                flashcard_set, created = FlashcardSet.objects.get_or_create(
                                    title=set_title,
                                    defaults={
                                        'description': set_description,
                                        'subject': set_subject,
                                        'topic': set_topic,
                                        'year_group': set_year_group,
                                        'created_by': teacher,
                                    }
                                )
                                flashcard_sets_cache[set_title] = flashcard_set
                                if created:
                                    sets_created_count += 1
                                    self.stdout.write(self.style.SUCCESS(f'Created new FlashcardSet: "{set_title}"'))
                                else:
                                    self.stdout.write(self.style.WARNING(f'FlashcardSet "{set_title}" already exists. Adding cards to it.'))
                            else:
                                flashcard_set = flashcard_sets_cache[set_title]

                            # Create the Flashcard
                            Flashcard.objects.create(
                                flashcard_set=flashcard_set,
                                question=question_text,
                                answer=answer_text
                            )
                            flashcards_imported_count += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error importing row {reader.line_num}: {row} - {e}'))
                        # Continue to next row even if one fails
                        continue

            self.stdout.write(self.style.SUCCESS(f'Successfully imported {flashcards_imported_count} flashcards into {sets_created_count} new sets and existing sets.'))

        except FileNotFoundError:
            raise CommandError(f'File not found at "{csv_file_path}"')
        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
