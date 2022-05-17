from factory.django import DjangoModelFactory
from lecture.models import SemesterLecture

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