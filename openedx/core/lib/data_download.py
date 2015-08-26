"""
Utilities for data download section of instructor dashboard.
"""
from datetime import datetime
import urllib

from pytz import UTC
from instructor_task.models import PROGRESS

from instructor_task.tasks_helper import _get_current_task
from instructor_task.tasks_helper import upload_csv_to_report_store

UPDATE_STATUS_SUCCEEDED = 'succeeded'
UPDATE_STATUS_FAILED = 'failed'


def push_csv_responses_to_s3(csv_fn, filename, course_id, action_name):
    """
    Collect responses and upload them to S3 as a CSV
    """

    start_time = datetime.now(UTC)
    num_attempted = 1
    num_succeeded = 0
    num_failed = 0
    num_total = 1
    curr_step = "Collecting responses"

    def update_task_progress():
        """Return a dict containing info about current task"""
        current_time = datetime.now(UTC)
        progress = {
            'action_name': action_name,
            'attempted': num_attempted,
            'succeeded': num_succeeded,
            'failed': num_failed,
            'total': num_total,
            'duration_ms': int((current_time - start_time).total_seconds() * 1000),
            'step': curr_step,
        }
        _get_current_task().update_state(state=PROGRESS, meta=progress)

        return progress

    update_task_progress()

    try:
        header, datarows = csv_fn(course_id)
        rows = [header] + [row for row in datarows]
    # Update progress to failed regardless of error type
    # pylint: disable=bare-except
    except:
        num_failed = 1
        update_task_progress()

        return UPDATE_STATUS_FAILED

    timestamp_str = start_time.strftime('%Y-%m-%d-%H%M')
    course_id_string = urllib.quote(course_id.to_deprecated_string().replace('/', '_'))

    curr_step = "Uploading CSV"
    update_task_progress()
    upload_csv_to_report_store(
        rows,
        filename,
        course_id,
        start_time,
    )

    num_succeeded = 1
    curr_step = "Task completed successfully"
    update_task_progress()

    return UPDATE_STATUS_SUCCEEDED
