from factory.django import DjangoModelFactory
from semester.models import Semester

class SemesterFactory(DjangoModelFactory):
    class Meta:
        model = Semester

    @classmethod
    def create(cls, **kwargs):

        semesters = kwargs.get("semesters")
        semesters_created = []

        for semester in semesters:
            plan = semester.get("plan")
            year = semester.get("year")
            semester_type = semester.get("semester_type")
            major_requirement_credit = semester.get("major_requirement_credit", 0)
            major_elective_credit = semester.get("major_elective_credit", 0)
            general_credit = semester.get("general_credit", 0)
            general_elective_credit = semester.get("general_elective_credit", 0)
            semesters_created.append(
                Semester(
                    plan=plan,
                    year=year,
                    semester_type=semester_type,
                    major_requirement_credit=major_requirement_credit,
                    major_elective_credit=major_elective_credit,
                    general_credit=general_credit,
                    general_elective_credit=general_elective_credit
                )
            )

        if len(semesters_created) > 0:
            return Semester.objects.bulk_create(semesters_created)

        return None
