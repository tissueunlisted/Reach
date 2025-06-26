# C:\entc\core_app\management\commands\import_flashcards.py

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core_app.models import FlashcardSet, Flashcard, User # Import your models

class Command(BaseCommand):
    help = 'Imports flashcards from a CSV file into existing or new FlashcardSets.'

    def add_arguments(self, parser):
        # We'll hardcode the CSV path for this one-time deployment,
        # but keep the argument for flexibility if run locally.
        parser.add_argument('csv_file', type=str, default='flashcards_data.csv', nargs='?',
                            help='The path to the CSV file to import (defaults to flashcards_data.csv in project root)')
        # Add an optional argument for the user who created these flashcards/sets
        # IMPORTANT: Replace 'admin_render' with the actual username of a teacher/admin
        # account you created on Render's database (via createsuperuser or signup).
        parser.add_argument('--user', type=str, default='admin_render',
                            help='Username of the user who is creating these flashcards/sets. Defaults to a placeholder.')

    def handle(self, *args, **options):
        csv_file_name = options['csv_file']
        username = options['user']

        # Construct the absolute path to the CSV file
        # Render's deployment will have the CSV in the root directory relative to manage.py
        csv_file_path = os.path.join(os.getcwd(), csv_file_name)

        # Check if the CSV file exists (important for Render's build process)
        if not os.path.exists(csv_file_path):
            raise CommandError(f'CSV file "{csv_file_path}" not found. Ensure it is in your project root.')
        
        # Get the user (creator)
        try:
            creator_user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist in the database. Please ensure you have created this user (e.g., via `createsuperuser` on Render) or specified an existing one.')

        self.stdout.write(self.style.SUCCESS(f'Starting import from "{csv_file_path}" for user "{username}"...'))

        # Process the CSV file
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check for required headers
                required_headers = ['set_title', 'set_description', 'set_subject', 'set_topic', 'set_year_group', 'question_text', 'answer_text']
                if not all(header in reader.fieldnames for header in required_headers):
                    raise CommandError(f"CSV file must contain the following headers: {', '.join(required_headers)}")

                flashcard_sets_processed = {} # To keep track of created/retrieved sets
                flashcards_added_count = 0

                # Use a transaction to ensure atomicity
                with transaction.atomic():
                    for row_num, row in enumerate(reader):
                        set_title = row.get('set_title', '').strip()
                        set_description = row.get('set_description', '').strip()
                        set_subject = row.get('set_subject', '').strip()
                        set_topic = row.get('set_topic', '').strip()
                        set_year_group = row.get('set_year_group', '').strip()
                        question_text = row.get('question_text', '').strip()
                        answer_text = row.get('answer_text', '').strip()

                        if not set_title or not question_text or not answer_text:
                            self.stdout.write(self.style.WARNING(f"Skipping row {row_num + 2} (CSV line {row_num + 1}): Missing set_title, question_text, or answer_text."))
                            continue # Skip row if essential data is missing

                        # Get or create the FlashcardSet
                        if set_title not in flashcard_sets_processed:
                            flashcard_set, created = FlashcardSet.objects.get_or_create(
                                title=set_title,
                                defaults={
                                    'description': set_description,
                                    'subject': set_subject,
                                    'topic': set_topic,
                                    'year_group': set_year_group,
                                    'created_by': creator_user
                                }
                            )
                            flashcard_sets_processed[set_title] = flashcard_set
                            if created:
                                self.stdout.write(self.style.NOTICE(f'Created new FlashcardSet: "{set_title}"'))
                            else:
                                self.stdout.write(self.style.WARNING(f'Using existing FlashcardSet: "{set_title}". Note: If you modify set details in CSV for an existing set, they will be ignored on subsequent runs.'))
                        else:
                            flashcard_set = flashcard_sets_processed[set_title]

                        # Create the Flashcard
                        # Important: This will create duplicate flashcards if run multiple times
                        # with the same CSV content. This is intended for a ONE-TIME import.
                        Flashcard.objects.create(
                            flashcard_set=flashcard_set,
                            question=question_text,
                            answer=answer_text
                        )
                        flashcards_added_count += 1

                self.stdout.write(self.style.SUCCESS(f'Successfully imported {flashcards_added_count} flashcards.'))
                self.stdout.write(self.style.SUCCESS(f'Processed {len(flashcard_sets_processed)} unique flashcard sets.'))

        except FileNotFoundError:
            raise CommandError(f'The file "{csv_file_path}" was not found during execution.')
        except Exception as e:
            raise CommandError(f'An error occurred during import: {e}')
