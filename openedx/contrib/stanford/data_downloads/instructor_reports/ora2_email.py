# -*- coding: utf-8 -*-
"""
Generate report of ORA2 data with email address
"""


from __future__ import absolute_import
from openedx.contrib.stanford.data_downloads.util import collect_ora2_data


def collect_email_ora2_data(course_id):
    """
    Call collect_ora2_data for aggregated ORA2 response data including users' email addresses
    """
    return collect_ora2_data(course_id, True)
