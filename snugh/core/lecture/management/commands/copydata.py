from django.core.management.base import BaseCommand, CommandError
from core.lecture.models import Lecture
from core.major.models import Major
from core.requirement.models import Requirement


class Command(BaseCommand):
    help = "Copies data for testing from remote database 'remote'"

    src_db = 'remote'
    dest_db = 'default'

    def handle(self, *args, **options):
        self.notice('Starting migration')
        self.notice('Loading lectures')
        lectures = Lecture.objects.using(self.src_db).all()
        self.success('Successfully loaded lectures')
        self.notice('Loading majors')
        majors = Major.objects.using(self.src_db).all()
        self.success('Successfully loaded majors')
        self.notice('Loading requirements')
        requirements = Requirement.objects.using(self.src_db).all()
        self.success('Successfully loaded requirements')
        self.notice('Saving lectures')
        Lecture.objects.using(self.dest_db).bulk_create(lectures)
        self.success('Successfully saved lectures')
        self.notice('Saving majors')
        Major.objects.using(self.dest_db).bulk_create(majors)
        self.success('Successfully saved majors')
        self.notice('Saving requirements')
        Requirement.objects.using(self.dest_db).bulk_create(requirements)
        self.success('Successfully saved requirements')
        self.success('Successfully finished migration')

    def notice(self, msg):
        self.stdout.write(self.style.NOTICE(msg))

    def success(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))
