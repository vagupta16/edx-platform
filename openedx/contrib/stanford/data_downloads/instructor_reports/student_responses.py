# -*- coding: utf-8 -*-
"""
Generate report of student response data
"""

from datetime import datetime
import urllib

from pytz import UTC

from courseware.courses import get_course_by_id
from instructor_analytics.basic import student_response_rows
from instructor_task.models import ReportStore


def push_student_responses_to_s3(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a responses CSV file for students that
    have submitted problem responses, and store using a `ReportStore`. Once
    created, the files can be accessed by instantiating another `ReportStore` (via
    `ReportStore.from_config()`) and calling `link_for()` on it. Writes are
    buffered, so we'll never write part of a CSV file to S3 -- i.e. any files
    that are visible in ReportStore will be complete ones.
    """
    start_time = datetime.now(UTC)

    try:
        course = get_course_by_id(course_id)
    except ValueError as e:
        TASK_LOG.error(e.message)
        return "failed"

    rows = student_response_rows(course)

    # Generate parts of the file name
    timestamp_str = start_time.strftime("%Y-%m-%d-%H%M")
    course_id_prefix = urllib.quote(course_id.to_deprecated_string().replace("/", "_"))

    # Perform the actual upload
    report_store = ReportStore.from_config()
    report_store.store_rows(
        course_id,
        u"{}_responses_report_{}.csv".format(course_id_prefix, timestamp_str),
        rows
    )

    return "succeeded"
