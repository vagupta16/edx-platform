"""
Helpers for instructor dashboard, data download, ora2 report
"""


from data_downloads.util import collect_ora2_data


def collect_anonymous_ora2_data(course_id):
    """
    Call collect_ora2_data for anonymized, aggregated ORA2 response data.
    """
    return collect_ora2_data(course_id, False)


def collect_email_ora2_data(course_id):
    """
    Call collect_ora2_data for aggregated ORA2 response data including users' email addresses
    """
    return collect_ora2_data(course_id, True)
