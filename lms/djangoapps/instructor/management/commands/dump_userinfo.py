# -*- coding: utf-8 -*-
#
# CME management command: dump userinfo to csv files for reporting

import csv
from datetime import datetime
from optparse import make_option
import sys
import tempfile

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from pytz import UTC

from certificates.models import GeneratedCertificate
from cme_registration.models import CmeUserProfile
from student.models import CourseEnrollment
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import PaidCourseRegistration

PROFILE_FIELDS = [
    ('user__profile__cmeuserprofile__last_name', 'Last Name'),
    ('user__profile__cmeuserprofile__middle_initial', 'Middle Initial'),
    ('user__profile__cmeuserprofile__first_name', 'First Name'),
    ('user__email', 'Email Address'),
    ('user__profile__cmeuserprofile__birth_date', 'Birth Date'),
    ('user__profile__cmeuserprofile__professional_designation', 'Professional Designation'),
    ('user__profile__cmeuserprofile__license_number', 'Professional License Number'),
    ('user__profile__cmeuserprofile__license_country', 'Professional License Country'),
    ('user__profile__cmeuserprofile__license_state', 'Professional License State'),
    ('user__profile__cmeuserprofile__physician_status', 'Physician Status'),
    ('user__profile__cmeuserprofile__patient_population', 'Patient Population'),
    ('user__profile__cmeuserprofile__specialty', 'Specialty'),
    ('user__profile__cmeuserprofile__sub_specialty', 'Sub Specialty'),
    ('user__profile__cmeuserprofile__affiliation', 'Stanford Medicine Affiliation'),
    ('user__profile__cmeuserprofile__sub_affiliation', 'Stanford Sub Affiliation'),
    ('user__profile__cmeuserprofile__stanford_department', 'Stanford Department'),
    ('user__profile__cmeuserprofile__sunet_id', 'SUNet ID'),
    ('user__profile__cmeuserprofile__other_affiliation', 'Other Affiliation'),
    ('user__profile__cmeuserprofile__job_title_position_untracked', 'Job Title or Position'),
    ('user__profile__cmeuserprofile__address_1', 'Address 1'),
    ('user__profile__cmeuserprofile__address_2', 'Address 2'),
    ('user__profile__cmeuserprofile__city', 'City'),
    ('user__profile__cmeuserprofile__state', 'State'),
    ('user__profile__cmeuserprofile__postal_code', 'Postal Code'),
    ('user__profile__cmeuserprofile__county_province', 'County/Province'),
    ('user__profile__cmeuserprofile__country_cme', 'Country'),
    ('user__profile__cmeuserprofile__phone_number_untracked', 'Phone Number'),
    ('user__profile__cmeuserprofile__gender', 'Gender'),
    ('user__profile__cmeuserprofile__marketing_opt_in_untracked', 'Marketing Opt-In'),
    ('user__id', '')
]

REGISTRATION_FIELDS = [
    ('system_id_untracked', 'System ID'),
    ('line_cost', 'Fee Charged'),
    ('line_cost', 'Amount Paid'),
    ('reference_untracked', 'Reference'),
    ('dietary_restrictions_untracked', 'Dietary Restrictions'),
    ('marketing_source_untracked', 'Marketing Source'),
]

ORDER_FIELDS = [
    ('purchase_time', 'Date Registered'),
    ('bill_to_cardtype', 'Payment Type'),
    ('bill_to_ccnum', 'Reference Number'),
    (['bill_to_first', 'bill_to_last'], 'Paid By'),
]

CERTIFICATE_FIELDS = [
    ('credits_special_case', 'Credits Issued'),
    ('created_date', 'Credit Date'),
    ('has_certificate_special_case', 'Certif'),
]

class Command(BaseCommand):
    help = """Export data required by Stanford SCCME Tracker Project to .csv file."""

    option_list = BaseCommand.option_list + (
        make_option(
            '-c',
            '--course',
            metavar='COURSE_ID',
            dest='course',
            default=False,
            help='The course id (e.g., CME/001/2013-2015) to select from.',
        ),
        make_option(
            '-o',
            '--outfile',
            metavar='OUTFILE',
            dest='outfile',
            default=False,
            help='The file path to which to write the output.',
        ),
    )

    def handle(self, *args, **options):
        course_id = options['course']
        outfile_name = options['outfile']
        verbose = int(options['verbosity']) > 1

        if not (course_id):
            raise CommandError('--course must be specified')

        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        if outfile_name:
            outfile = open(outfile_name, 'wb')
        else:
            outfile = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
            outfile_name = outfile.name

        all_fields = PROFILE_FIELDS + REGISTRATION_FIELDS + ORDER_FIELDS + CERTIFICATE_FIELDS

        csv_fieldnames = [label for field, label in all_fields if len(label) > 0]
        csvwriter = csv.DictWriter(outfile, fieldnames=csv_fieldnames, delimiter=',', quoting=csv.QUOTE_ALL)
        csvwriter.writeheader()

        sys.stdout.write("Fetching enrolled students for {course}...".format(course=course_id))

        cme_profiles = CourseEnrollment.objects.select_related('user__profile__cmeuserprofile').filter(course_id=course_id).values(
            *[field for field, label in PROFILE_FIELDS if 'untracked' not in field]).order_by('user__username')

        registrations = PaidCourseRegistration.objects.filter(status='purchased', course_id=course_id)
        certificates = GeneratedCertificate.objects.filter(course_id=course_id)

        registration_table = self.build_user_table(registrations)
        certificate_table = self.build_user_table(certificates)

        sys.stdout.write(" done.\n")

        count = 0
        total = cme_profiles.count()
        start = datetime.now(UTC)

        intervals = int(0.10 * total)
        if intervals > 100 and verbose:
            intervals = 101
        
        sys.stdout.write("Processing users")

        for cme_profile in cme_profiles:
            student_dict = {
                'Credits Issued': None,
                'Credit Date': None,
                'Certif': False
            } 

            for field, label in PROFILE_FIELDS:
                try:
                    if len(label) > 0:
                        student_dict[label] = cme_profile[field] if cme_profile[field] != None else ''
                except KeyError:
                    student_dict[label] = ''

            user_id = cme_profile['user__id']

            registration = self.add_fields_to(student_dict, REGISTRATION_FIELDS, registration_table, user_id)

            if registration:
                self.add_fields_to(student_dict, ORDER_FIELDS, {user_id : registration.order}, user_id)

            certificate = self.add_fields_to(student_dict, CERTIFICATE_FIELDS, certificate_table, user_id)

            #Certificate special case values
            certificate_status = getattr(certificate, 'status', '')
            student_dict['Certif'] = (certificate_status in ('downloadable', 'generating'))

            #XXX should be revisited when credit count functionality implemented
            if student_dict['Certif']:
                student_dict['Credits Issued'] = 23.5

            for item in student_dict:
                student_dict[item] = self.preprocess(student_dict[item])

            csvwriter.writerow(student_dict)

            count += 1
            if count % intervals == 0:
                if verbose:
                    diff = datetime.now(UTC) - start
                    timeleft = diff * (total - count) / intervals
                    hours, remainder = divmod(timeleft.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    sys.stdout.write("\n{count}/{total} completed ~{hours:02}:{minutes:02} remaining\n"
                        .format(count=count, total=total, hours=hours, minutes=minutes))
                    start = datetime.now(UTC)
                else:
                    sys.stdout.write('.')

        outfile.close()
        sys.stdout.write("Data written to {name}\n".format(name=outfile_name))

    def build_user_table(self, data_rows):
        table = {}

        for row in data_rows:
            table[getattr(row, 'user_id')] = row

        return table

    def add_fields_to(self, values, fields, table, user_id):
        try:
            registration = table[user_id]
        except KeyError:
            registration = None

        for field, label in fields:
            if type(field) is list:
                values[label] = ' '.join([getattr(registration, f, '') for f in field])
            else:
                values[label] = getattr(registration, field, '')

        return registration

    def preprocess(self, value):
      if type(value) is datetime:
        value = value.strftime("%m/%d/%Y")

      value = unicode(value).encode('utf-8')
      value = value.replace("_"," ")

      return value

