import csv
import re

from django.core.management.base import BaseCommand, CommandError
from lecture.models import Lecture


class Command(BaseCommand):
    help = "Imports data from csv search file"

    def add_arguments(self, parser):
        parser.add_argument('filepath', help='Path of the CSV file to import.')
        parser.add_argument('--dry-run', action='store_true', help="Show the number of lectures that will be modified; don't actually update them.")
        parser.add_argument('--ignore-errors', action='store_true', help='Ignore unexpected errors detected while importing.')
        parser.add_argument('--noinput', '--no-input', action='store_false', dest='interactive', help='Do NOT prompt the user for input of any kind.')

    def handle(self, *args, **options):
        filepath = options['filepath']
        self.ignore_errors = options['ignore_errors']
        self.dry_run = options['dry_run']
        self.interactive = options['interactive']

        self.notice(f'Starting import from {filepath}')
        with open(filepath, newline='') as csvfile:
            csvreader = csv.reader(csvfile)

            next(csvreader)
            infoheader = next(csvreader)[0]
            m = re.search(r'(\d+)학년도.*(1|2|여름|겨울)학기', infoheader)
            year = int(m.group(1))
            if not 2010 <= year <= 2030:
                self.warn_error(f'Unexpected year {year}.')

            if m.group(2) == '1':
                semester = Lecture.FIRST
            elif m.group(2) == '2':
                semester = Lecture.SECOND
            elif m.group(2) == '여름':
                semester = Lecture.SUMMER
            elif m.group(2) == '겨울':
                semester = Lecture.WINTER
            else:
                self.warn_error(f'Unexpected semester type {m.group(2)}.')
                semester = Lecture.UNKNOWN

            if not self.boolean_input(f'Detected file as {year} {semester} semester.', 'Continue? [Y/n]', True):
                raise CommandError('Aborted due to user request.')

            next(csvreader)

            lecture_values_list = []
            for row in csvreader:
                # create variables
                if row[0] == '전필':
                    lecture_type = Lecture.MAJOR_REQUIREMENT
                elif row[0] == '전선':
                    lecture_type = Lecture.MAJOR_ELECTIVE
                elif row[0] == '교양':
                    lecture_type = Lecture.GENERAL
                elif row[0] == '일선':
                    lecture_type = Lecture.GENERAL_ELECTIVE
                elif row[0] == '교직':
                    lecture_type = Lecture.TEACHING
                elif row[0] in ['공통', '논문', '대학원']:
                    lecture_type = Lecture.NONE
                else:
                    self.warn_error(f'Unexpected lecture type {row[0]}.')
                    lecture_type = Lecture.NONE

                try:
                    credit = int(row[9])
                except ValueError:
                    self.warn_error(f'Unexpected credit {row[9]}.')
                    credit = 0

                lecture_values_list.append({
                    'lecture_code': row[5],
                    'lecture_name': row[7],
                    'open_department': row[1],
                    'open_major': row[2],
                    'open_semester': semester,
                    'lecture_type': lecture_type,
                    'credit': credit,
                    'recent_open_year': year
                })


        existing_lectures = Lecture.objects.filter(lecture_code__in=[values['lecture_code'] for values in lecture_values_list])
        self.info(f'{existing_lectures.count()} lectures already exist.')
        existing_lecture_codes = [lecture.lecture_code for lecture in existing_lectures]
        new_lectures = [Lecture(**values) for values in lecture_values_list if values['lecture_code'] not in existing_lecture_codes]
        self.info(f'{len(new_lectures)} lectures will be created.')

        lectures_to_set_year = existing_lectures.filter(recent_open_year__lt=year)

        if semester in [Lecture.FIRST, Lecture.SECOND]:
            insignificant_semesters = [Lecture.UNKNOWN, Lecture.SUMMER, Lecture.WINTER]
            other_semester = Lecture.SECOND if semester == Lecture.FIRST else Lecture.FIRST
        elif semester in [Lecture.SUMMER, Lecture.WINTER]:
            insignificant_semesters = [Lecture.UNKNOWN]
            other_semester = Lecture.WINTER if semester == Lecture.SUMMER else Lecture.SUMMER
        else:
            insignificant_semesters = []
            other_semester = Lecture.UNKNOWN

        lectures_to_set_semester = existing_lectures.filter(open_semester__in=insignificant_semesters)
        lectures_to_add_semester = existing_lectures.filter(open_semester=other_semester)

        self.info(f'{lectures_to_set_year.count()} lectures will be updated recent_open_year to {year}.')
        self.info(f'{lectures_to_set_semester.count()} lectures will be updated open_semester to {semester}.')
        self.info(f'{lectures_to_add_semester.count()} lectures will be updated open_semester to {Lecture.ALL}.')

        if not self.dry_run:
            self.notice('Creating new lectures...')
            Lecture.objects.bulk_create(new_lectures)

            self.notice('Updating open year of existing lectures...')
            lectures_to_set_year.update(recent_open_year=year)
            self.notice('Updating open semester of existing lectures...')
            if semester in [Lecture.FIRST, Lecture.SECOND]:
                lectures_to_set_semester.update(open_semester=semester)
                lectures_to_add_semester.update(open_semester=Lecture.ALL)
            elif semester in [Lecture.SUMMER, Lecture.WINTER]:
                lectures_to_set_semester.update(open_semester=semester)
                lectures_to_add_semester.update(open_semester=Lecture.ALL)
                existing_lectures.filter(open_semester=Lecture.UNKNOWN).update(open_semester=semester)
            self.success('Successfully imported all lectures.')
        else:
            self.notice('No lectures were created or updated because --dry-run was requested.')

    def boolean_input(self, message, question, default=None):
        self.stdout.write(message, ending=' ' if self.interactive else '\n')
        if not self.interactive:
            if default is not None:
                return default
            else:
                raise CommandError(f"No default action for question: {question}")
        result = input(f"{question} ")
        if not result and default is not None:
            return default
        while not result or result[0].lower() not in "yn":
            result = input("Please answer yes or no: ")
        return result[0].lower() == "y"


    def warn_error(self, msg):
        if self.ignore_errors:
            self.warning(msg)
        else:
            raise CommandError(f'Possible error found: {msg}\n' \
                               'To ignore errors, try the --ignore-errors option.')

    def info(self, msg, ending=None):
        self.stdout.write(msg, ending=ending)

    def notice(self, msg, ending=None):
        self.stdout.write(self.style.NOTICE(msg), ending=ending)

    def warning(self, msg, ending=None):
        self.stdout.write(self.style.WARNING(msg), ending=ending)

    def success(self, msg, ending=None):
        self.stdout.write(self.style.SUCCESS(msg), ending=ending)
