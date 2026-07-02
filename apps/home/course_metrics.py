from apps.course.models.course import Course
from apps.course.models.note import Note


def get_course_metrics(request):
    total_courses = Course.objects.filter(user=request.user).count()
    total_notes = Note.objects.filter(user_id=request.user).count()
    avg_notes = 0
    if total_notes and total_courses:
        avg_notes = total_notes / total_courses

    return dict(
        total_courses=total_courses,
        total_notes=total_notes,
        avg_notes=avg_notes,
    )
