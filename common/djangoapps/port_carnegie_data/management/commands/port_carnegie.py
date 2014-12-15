from django.core.management.base import BaseCommand, CommandError, make_option
from django.db.models import Q
from student.models import User, CourseEnrollment
from courseware.models import StudentModule
from certificates.models import GeneratedCertificate
from opaque_keys.edx.locations import SlashSeparatedCourseKey
import logging
from django.db import transaction

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Copies users over from one database to another.
    """
    help = 'Port over carnegie data.'

    option_list = BaseCommand.option_list + (
        make_option('--write',
                    action='store_true',
                    default=False,
                    dest="write",
                    help='Actually perform database writes.  If not set, we just make db reads and print messages'),
        make_option('--copy-student-module',
                    action='store_true',
                    default=False,
                    dest="copy_student_module",
                    help='Copy over courseware_studentmodule.  Default False'),
        make_option('--from-db',
                    action='store',
                    default="",
                    help='The database key (from settings.DATABASES) from which data is copied'),
        make_option('--to-db',
                    action='store',
                    default="",
                    help='The database key (from settings.DATABASES) to which data is written'),
    )

    def handle(self, *args, **options):
        from_db_name = options['from_db']
        to_db_name = options['to_db']
        write = options['write']

        print("Actually going to write to to_db: {}".format(write))
        from_db = DatabaseWrapper(from_db_name)
        to_db = DatabaseWrapper(to_db_name)

        self.copy_users(from_db, to_db, write)
        self.copy_enrollments(from_db, to_db, "Training/Carnegie/CLASlite", "Training/Carnegie/CLASlite", write)
        self.copy_enrollments(from_db, to_db, "Aula/Carnegie/CLASlite", "Aula/Carnegie/CLASlite", write)
        self.copy_certs(from_db, to_db, "Training/Carnegie/CLASlite", "Training/Carnegie/CLASlite", write)
        self.copy_certs(from_db, to_db, "Aula/Carnegie/CLASlite", "Aula/Carnegie/CLASlite", write)
        if options['copy_student_module']:
            self.copy_student_module(from_db, to_db, "Training/Carnegie/CLASlite", "Training/Carnegie/CLASlite", write)
            self.copy_student_module(from_db, to_db, "Aula/Carnegie/CLASlite", "Aula/Carnegie/CLASlite", write)

    def copy_users(self, from_db, to_db, write):
        all_users = from_db.all_users()
        for user in all_users:
            if to_db.user_matching_email_exists(user.email):
                log.info("Not creating User w/email <{}>, already exists.".format(user.email))
            else:
                new_username = to_db.get_unclaimed_username(user.username)
                log.info("Creating user w/email <{}>, username: {}".format(user.email, new_username))
                if write:
                    to_db.copy_user(user, new_username)

    def copy_enrollments(self, from_db, to_db, from_course_id, to_course_id, write):
        from_course_key = SlashSeparatedCourseKey.from_deprecated_string(from_course_id)
        to_course_key = SlashSeparatedCourseKey.from_deprecated_string(to_course_id)

        all_enrollments = from_db.all_enrollments(from_course_key)
        for enrollment in all_enrollments:
            to_user = to_db.get_user_matching_email(enrollment.user.email)
            if to_db.course_enrollment_exists(to_course_key, to_user):
                log.info("User w/email <{}> already enrolled in {}".format(to_user.email, to_course_id))
            else:
                log.info("Enrolling user w/email <{}> in {}".format(to_user.email, to_course_id))
                if write:
                    to_db.copy_enrollment(enrollment, to_course_key, to_user)

    def copy_certs(self, from_db, to_db, from_course_id, to_course_id, write):
        from_course_key = SlashSeparatedCourseKey.from_deprecated_string(from_course_id)
        to_course_key = SlashSeparatedCourseKey.from_deprecated_string(to_course_id)

        all_certs = from_db.all_certs(from_course_key)
        for cert in all_certs:
            to_user = to_db.get_user_matching_email(cert.user.email)
            if to_db.user_has_cert(to_course_key, to_user):
                log.info("Cert for User w/email <{}> already exists for {}".format(to_user.email, to_course_id))
            else:
                log.info("Copying cert for user w/email <{}> for {}".format(to_user.email, to_course_id))
                if write:
                    to_db.copy_cert(cert, to_course_key, to_user)

    def copy_student_module(self, from_db, to_db, from_course_id, to_course_id, write):
        from_course_key = SlashSeparatedCourseKey.from_deprecated_string(from_course_id)
        to_course_key = SlashSeparatedCourseKey.from_deprecated_string(to_course_id)

        all_enrollments = from_db.all_enrollments(from_course_key)
        for enrollment in all_enrollments:
            from_user = from_db.get_user_matching_email(enrollment.user.email)
            to_user = to_db.get_user_matching_email(enrollment.user.email)
            student_modules = from_db.get_student_modules_for_course(from_course_key, from_user)
            modules_copied = 0
            modules_overwritten = 0
            for module in student_modules:
                to_module = to_db.get_matching_student_module(module, to_user)
                if not to_module:
                    modules_copied += 1
                    if write:
                        to_db.copy_student_module_for_course(module, to_course_key, to_user)
                elif module.modified > to_module.modified:
                    modules_overwritten += 1
                    if write:
                        to_db.overwrite_student_module_for_course(module, to_module, to_course_key, to_user)

            log.info("{}/{} StudentModules copied/overwritten for user w/email <{}> for {}".format(
                modules_copied,
                modules_overwritten,
                to_user.email,
                to_course_id,
            ))


class DatabaseWrapper(object):
    """
    A class to wrap read/writes to a particular db.
    """
    def __init__(self, db_name):
        self._db_name = db_name

    @transaction.commit_on_success
    def copy_user(self, user, username):
        profile = user.profile
        user.pk = None
        user.username = username
        user._state.db = self._db_name
        user.save(using=self._db_name)
        profile._state.db = self._db_name
        profile.pk = None
        profile.user = user
        profile.save(using=self._db_name)

    @transaction.commit_on_success
    def copy_enrollment(self, enrollment, new_course_key, user):
        enrollment._state.db = self._db_name
        enrollment.pk = None
        enrollment.user = user
        enrollment.course_id = new_course_key
        enrollment.save(using=self._db_name)

    @transaction.commit_on_success
    def copy_cert(self, cert, new_course_key, user):
        cert._state.db = self._db_name
        cert.pk = None
        cert.user = user
        cert.course_id = new_course_key
        cert.save(using=self._db_name)

    @transaction.commit_on_success
    def copy_student_module_for_course(self, module, new_course_key, user):
        module._state.db = self._db_name
        module.pk = None
        module.student = user
        module.course_id = new_course_key
        module.save(using=self._db_name, force_insert=True)

    @transaction.commit_on_success
    def overwrite_student_module_for_course(self, from_module, to_module, new_course_key, user):
        from_module._state.db = self._db_name
        from_module.pk = to_module.pk
        from_module.student = user
        from_module.course_id = new_course_key
        from_module.save(using=self._db_name, force_update=True)

    def get_unclaimed_username(self, username):
        if not self.user_matching_username_exists(username):
            return username
        suffix = 1
        while True:
            new_username = "{}{}".format(username, suffix)
            if not self.user_matching_username_exists(new_username):
                return new_username
            suffix += 1

    def user_matching_username_exists(self, username):
        return User.objects.filter(username=username).using(self._db_name).exists()

    def user_matching_email_exists(self, email):
        return User.objects.filter(email=email).using(self._db_name).exists()

    def get_user_matching_email(self, email):
        return User.objects.using(self._db_name).get(email=email)

    def get_student_modules_for_course(self, course_key, user):
        return StudentModule.objects.filter(course_id=course_key, student=user).using(self._db_name)

    def course_enrollment_exists(self, course_key, user):
        return CourseEnrollment.objects.filter(course_id=course_key, user=user).using(self._db_name).exists()

    def user_has_cert(self, course_key, user):
        return GeneratedCertificate.objects.filter(course_id=course_key, user=user).using(self._db_name).exists()

    def student_module_exists_for_course(self, course_key, user):
        return self.get_student_modules_for_course(course_key, user).exists()

    def get_matching_student_module(self, module, user):
        try:
            return (
                StudentModule.objects
                .using(self._db_name)
                .get(module_state_key=module.module_state_key, student=user)
            )
        except StudentModule.DoesNotExist:
            return None

    def all_users(self):
        return User.objects.all().select_related('profile').using(self._db_name)

    def all_enrollments(self, course_key):
        return CourseEnrollment.objects.filter(course_id=course_key).select_related('user').using(self._db_name)

    def all_certs(self, course_key):
        return GeneratedCertificate.objects.filter(course_id=course_key).select_related('user').using(self._db_name)
