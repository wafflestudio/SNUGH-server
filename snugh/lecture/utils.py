from factory.django import DjangoModelFactory
from .models import Semester, Lecture, Semester, SemesterLecture, Major


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


class SemesterLectureFactory(DjangoModelFactory):
    class Meta:
        model = SemesterLecture

    @classmethod
    def create(cls, **kwargs):

        lectures = kwargs.get("lectures")
        lectures_created = []
        semester = kwargs.get("semester")
        recoginized_majors = kwargs.get("recognized_majors")

        if not (semester or lectures):
            return None

        for i, lecture in enumerate(lectures):
            lectures_created.append(
                SemesterLecture(
                    semester=semester,
                    lecture=lecture,
                    lecture_type=lecture.lecture_type,
                    recognized_major1=recoginized_majors[i],
                    lecture_type1=lecture.lecture_type,
                    credit=lecture.credit,
                    recent_sequence=i
                )
            )

        if len(lectures_created) > 0:
            return SemesterLecture.objects.bulk_create(lectures_created)

        return None
