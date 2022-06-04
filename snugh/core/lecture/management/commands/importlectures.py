from datetime import date
import re

from django.core.management.base import BaseCommand, CommandError
import requests
import xlrd

from core.lecture.models import Lecture
import core.semester.const as SEMESTER_TYPES
import core.lecture.const as LECTURE_TYPES


class Command(BaseCommand):
    help = "Import lectures from sugang.snu.ac.kr"

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, choices=range(2013, date.today().year + 1), help='Year to import.')
        parser.add_argument('semester', choices=[SEMESTER_TYPES.FIRST,
                                                 SEMESTER_TYPES.SECOND,
                                                 SEMESTER_TYPES.SUMMER,
                                                 SEMESTER_TYPES.WINTER],
                            help='Semester to import.')
        parser.add_argument('--dry-run', action='store_true', help="Show the number of lectures that will be modified; don't actually update them.")
        parser.add_argument('--ignore-errors', action='store_true', help='Ignore unexpected errors detected while importing.')
        parser.add_argument('--noinput', '--no-input', action='store_false', dest='interactive', help='Do NOT prompt the user for input of any kind.')

    def handle(self, *args, **options):
        year = options['year']
        semester = options['semester']

        self.dry_run = options['dry_run']
        self.ignore_errors = options['ignore_errors']
        self.interactive = options['interactive']

        url = 'https://sugang.snu.ac.kr/sugang/cc/cc100InterfaceExcel.action'
        semester_params = { SEMESTER_TYPES.FIRST: 'U000200001U000300001',
                            SEMESTER_TYPES.SECOND: 'U000200002U000300001',
                            SEMESTER_TYPES.SUMMER: 'U000200001U000300002',
                            SEMESTER_TYPES.WINTER: 'U000200002U000300002' }
        params = { 'workType': 'EX', 'srchOpenSchyy': f'{year}', 'srchOpenShtm': semester_params[semester], 'srchPageSize': '9999', 'srchCurrPage': '1' }
        empty_keys = ['srchBdNo', 'srchCamp', 'srchCptnCorsFg', 'srchExcept', 'srchLsnProgType', 'srchMrksGvMthd',
                      'srchOpenDeptCd', 'srchOpenMjCd', 'srchOpenPntMax', 'srchOpenPntMin', 'srchOpenSbjtDayNm',
                      'srchOpenSbjtFldCd', 'srchOpenSbjtNm', 'srchOpenSbjtTm', 'srchOpenSbjtTmNm', 'srchOpenShyr',
                      'srchOpenSubmattCorsFg', 'srchOpenSubmattFgCd1', 'srchOpenSubmattFgCd2', 'srchOpenSubmattFgCd3',
                      'srchOpenSubmattFgCd4', 'srchOpenSubmattFgCd5', 'srchOpenSubmattFgCd6', 'srchOpenSubmattFgCd7',
                      'srchOpenSubmattFgCd8', 'srchOpenSubmattFgCd9', 'srchOpenUpDeptCd', 'srchOpenUpSbjtFldCd',
                      'srchProfNm', 'srchSbjtCd', 'srchSbjtNm', 'srchTlsnAplyCapaCntMax', 'srchTlsnAplyCapaCntMin',
                      'srchTlsnRcntMax', 'srchTlsnRcntMin']
        params |= { key: '' for key in empty_keys }

        self.notice(f'Downloading data for {year} {semester} semester from {url}...')
        r = requests.get(url, params=params)
        try:
            book = xlrd.open_workbook(file_contents=r.content)
            sh = book.sheet_by_index(0)
        except xlrd.biffh.XLRDError:
            raise CommandError(f'Unexpected spreadsheet data from {url}.')

        self.notice('Starting import...')

        infoheader = sh.cell_value(1, 0)
        m = re.search(r'(\d+)학년도.*(1|2|여름|겨울)학기', infoheader)
        detected_year = int(m.group(1))

        if year != detected_year:
            self.warn_error(f'Expected year {year}, but detected {detected_year}.')

        if m.group(2) == '1':
            detected_semester = SEMESTER_TYPES.FIRST
        elif m.group(2) == '2':
            detected_semester = SEMESTER_TYPES.SECOND
        elif m.group(2) == '여름':
            detected_semester = SEMESTER_TYPES.SUMMER
        elif m.group(2) == '겨울':
            detected_semester = SEMESTER_TYPES.WINTER
        else:
            detected_semester = SEMESTER_TYPES.UNKNOWN

        if semester != detected_semester:
            self.warn_error(f'Expected semester {semester}, but detected {detected_semester}.')

        lecture_values_list = []
        for r in range(3, sh.nrows):
            row = [sh.cell_value(r, c) for c in range(sh.ncols)]
            if row[0] == '전필':
                lecture_type = LECTURE_TYPES.MAJOR_REQUIREMENT
            elif row[0] == '전선':
                lecture_type = LECTURE_TYPES.MAJOR_ELECTIVE
            elif row[0] == '교양':
                lecture_type = LECTURE_TYPES.GENERAL
            elif row[0] == '일선':
                lecture_type = LECTURE_TYPES.GENERAL_ELECTIVE
            elif row[0] == '교직':
                lecture_type = LECTURE_TYPES.TEACHING
            elif row[0] in ['공통', '논문', '대학원']:
                lecture_type = LECTURE_TYPES.NONE
            else:
                self.warn_error(f'Unexpected lecture type {row[0]}.')
                lecture_type = LECTURE_TYPES.NONE

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

        if semester in [SEMESTER_TYPES.FIRST, SEMESTER_TYPES.SECOND]:
            insignificant_semesters = [SEMESTER_TYPES.UNKNOWN, SEMESTER_TYPES.SUMMER, SEMESTER_TYPES.WINTER]
            other_semester = SEMESTER_TYPES.SECOND if semester == SEMESTER_TYPES.FIRST else SEMESTER_TYPES.FIRST
        elif semester in [SEMESTER_TYPES.SUMMER, SEMESTER_TYPES.WINTER]:
            insignificant_semesters = [SEMESTER_TYPES.UNKNOWN]
            other_semester = SEMESTER_TYPES.WINTER if semester == SEMESTER_TYPES.SUMMER else SEMESTER_TYPES.SUMMER
        else:
            insignificant_semesters = []
            other_semester = SEMESTER_TYPES.UNKNOWN

        lectures_to_set_semester = existing_lectures.filter(open_semester__in=insignificant_semesters)
        lectures_to_add_semester = existing_lectures.filter(open_semester=other_semester)

        self.info(f'{lectures_to_set_year.count()} lectures will be updated recent_open_year to {year}.')
        self.info(f'{lectures_to_set_semester.count()} lectures will be updated open_semester to {semester}.')
        self.info(f'{lectures_to_add_semester.count()} lectures will be updated open_semester to {SEMESTER_TYPES.ALL}.')

        if not self.dry_run:
            self.notice('Creating new lectures...')
            Lecture.objects.bulk_create(new_lectures)

            self.notice('Updating open year of existing lectures...')
            lectures_to_set_year.update(recent_open_year=year)
            self.notice('Updating open semester of existing lectures...')
            if semester in [SEMESTER_TYPES.FIRST, SEMESTER_TYPES.SECOND]:
                lectures_to_set_semester.update(open_semester=semester)
                lectures_to_add_semester.update(open_semester=SEMESTER_TYPES.ALL)
            elif semester in [SEMESTER_TYPES.SUMMER, SEMESTER_TYPES.WINTER]:
                lectures_to_set_semester.update(open_semester=semester)
                lectures_to_add_semester.update(open_semester=SEMESTER_TYPES.ALL)
                existing_lectures.filter(open_semester=SEMESTER_TYPES.UNKNOWN).update(open_semester=semester)
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
        elif self.boolean_input(self.style.WARNING(f'Possible error found: {msg}'), 'Ignore this specific error and continue? [y/N]', False):
            self.info('Continuing. To ignore all errors, try the --ignore-errors option.')
        else:
            raise CommandError('Aborted due to user request.')

    def info(self, msg, ending=None):
        self.stdout.write(msg, ending=ending)

    def notice(self, msg, ending=None):
        self.stdout.write(self.style.NOTICE(msg), ending=ending)

    def warning(self, msg, ending=None):
        self.stdout.write(self.style.WARNING(msg), ending=ending)

    def success(self, msg, ending=None):
        self.stdout.write(self.style.SUCCESS(msg), ending=ending)
