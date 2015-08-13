# -*- coding: utf-8 -*-
"""
Generate report of anonymous ORA2 data
"""


from __future__ import absolute_import
from openedx.contrib.stanford.data_downloads.util import collect_ora2_data


def collect_anonymous_ora2_data(course_id):
    """
    Call collect_ora2_data for anonymized, aggregated ORA2 response data.
    """
    return collect_ora2_data(course_id, False)
