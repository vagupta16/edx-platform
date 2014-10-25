# -*- coding: utf-8 -*-
#
# CME management command: dump userinfo to csv files for reporting

import csv
from datetime import datetime
from optparse import make_option
import sys
import tempfile

from django.core.management.base import BaseCommand, CommandError
from pytz import UTC

from certificates.models import GeneratedCertificate
from cme_registration.models import CmeUserProfile
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import PaidCourseRegistration

from unidecode import unidecode

PROFILE_FIELDS = [
    ('last_name', 'Last Name'),
    ('middle_initial', 'Middle Initial'),
    ('first_name', 'First Name'),
    ('user__email', 'Email Address'),
    ('birth_date', 'Birth Date'),
    ('professional_designation', 'Professional Designation'),
    ('license_number', 'Professional License Number'),
    ('license_country', 'Professional License Country'),
    ('license_state', 'Professional License State'),
    ('physician_status', 'Physician Status'),
    ('patient_population', 'Patient Population'),
    ('specialty', 'Specialty'),
    ('sub_specialty', 'Sub Specialty'),
    ('affiliation', 'Stanford Medicine Affiliation'),
    ('sub_affiliation', 'Stanford Sub Affiliation'),
    ('stanford_department', 'Stanford Department'),
    ('sunet_id', 'SUNet ID'),
    ('other_affiliation', 'Other Affiliation'),
    ('job_title_position_untracked', 'Job Title or Position'),
    ('address_1', 'Address 1'),
    ('address_2', 'Address 2'),
    ('city_cme', 'City'),
    ('state', 'State'),
    ('postal_code', 'Postal Code'),
    ('county_province', 'County/Province'),
    ('country_cme', 'Country'),
    ('phone_number_untracked', 'Phone Number'),
    ('gender', 'Gender'),
    ('marketing_opt_in_untracked', 'Marketing Opt-In'),
    ('user_id', ''),
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

        csvwriter = csv.DictWriter(outfile, fieldnames=csv_fieldnames, delimiter='\t', quoting=csv.QUOTE_ALL)
        csvwriter.writeheader()

        sys.stdout.write("Fetching enrolled students for {course}...".format(course=course_id))

        certificates, profiles, registrations = self.query_database_for(course_id)

        registration_table = self.build_user_table(registrations)
        certificate_table = self.build_user_table(certificates)

        sys.stdout.write(" done.\n")

        count = 0
        total = len(profiles)
        start = datetime.now(UTC)

        intervals = int(0.10 * total)
        if intervals > 100 and verbose:
            intervals = 101
        
        sys.stdout.write("Processing users")

        for profile in profiles:
            user_id = profile['user_id']
            self.print_progress(count, intervals, verbose)

            student_dict = {
                'Credits Issued': 23.5, #XXX should be revisited when credit count functionality implemented
                'Credit Date': None,
                'Certif': True,
            } 

            for field, label in PROFILE_FIELDS:
                if 'untracked' not in field and len(label) > 0:
                    student_dict[label] = profile[field]

            registration = self.add_fields_to(student_dict, REGISTRATION_FIELDS, registration_table, user_id)

            if registration:
                self.add_fields_to(student_dict, ORDER_FIELDS, {user_id : registration.order}, user_id)

                #Registration order special case values
                if student_dict['Payment Type'] == 'Visa':
                    student_dict['Payment Type'] = 'VISA'

                if student_dict['Payment Type'] == 'MasterCard':
                    student_dict['Payment Type'] = 'MC'

            certificate = self.add_fields_to(student_dict, CERTIFICATE_FIELDS, certificate_table, user_id)

            for item in student_dict:
                student_dict[item] = self.preprocess(student_dict[item])

            csvwriter.writerow(student_dict)

            count += 1

        outfile.close()
        sys.stdout.write("Data written to {name}\n".format(name=outfile_name))

    def query_database_for(self, course_id):
        certificates = GeneratedCertificate.objects.filter(course_id=course_id, status__in=['downloadable', 'generating'])
        
        credited_user_ids = [getattr(certificate, 'user_id') for certificate in certificates]

        cme_profiles = CmeUserProfile.objects.select_related('user').filter(user_id__in=credited_user_ids).values(
            *[field for field, label in PROFILE_FIELDS if 'untracked' not in field]).order_by('user__username')

        registrations = PaidCourseRegistration.objects.filter(course_id=course_id, status='purchased', user_id__in=credited_user_ids)

        return certificates, cme_profiles, registrations

    def build_user_table(self, data_rows):
        table = {}

        for row in data_rows:
            table[getattr(row, 'user_id')] = row

        return table

    def add_fields_to(self, values, fields, table, user_id):
        try:
            raw_data = table[user_id]
        except KeyError:
            raw_data = None

        for field, label in fields:
            if label not in values:
                if type(field) is list:
                    values[label] = ' '.join([getattr(raw_data, f, '') for f in field])
                else:
                    values[label] = getattr(raw_data, field, '')

        return raw_data

    def preprocess(self, value):
        if type(value) is datetime:
            value = value.strftime("%m/%d/%Y")

        value = unidecode(unicode(value))
        value = value.replace("_"," ")

        return value

    def print_progress(self, count, intervals, verbose):
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
