"""OLI analytics service event tracker backend."""

from __future__ import absolute_import

import json
import logging

import requests
from requests.exceptions import RequestException

from django.contrib.auth.models import User

from student.models import anonymous_id_for_user
from track.backends import BaseBackend


log = logging.getLogger(__name__)


class OLIAnalyticsBackend(BaseBackend):

    def __init__(self, **kwargs):
        super(OLIAnalyticsBackend, self).__init__(**kwargs)

        # the oli analytics service endpoint will be at
        # "{}{}".format(oli_analytics_service_url, path)
        self.oli_analytics_service_url = kwargs.get('oli_analytics_service_url', '')
        self.path = kwargs.get('path', '')

        # shared secret for OLI analytics service
        self.secret = kwargs.get('secret', '')

        # timeout for synchronous PUT attempt
        self.timeout_in_secs = kwargs.get('timeout_in_secs', 1.0)

        # only courses with id in this set will have their data sent
        self.course_id_set = set(kwargs.get('course_ids', []))

    def send(self, event):
        """
        Forward the event to the OLI analytics server
        """
        if not self.oli_analytics_service_url or not self.secret:
            return

        # Only currently passing problem_check events, which are CAPA only
        if event.get('event_type', '') != 'problem_check':
            return

        if event.get('event_source', '') != 'server':
            return

        context = event.get('context')
        if not context:
            return

        course_id = context.get('course_id')
        if not course_id or course_id not in self.course_id_set:
            return

        user_id = context.get('user_id')
        if not user_id:
            return

        event_data = event.get('event', {})
        if not event_data:
            return

        problem_id = event_data.get('problem_id')
        if not problem_id:
            return

        success = event_data.get('success')
        if not success:
            return

        is_correct = success == 'correct'

        # put the most expensive operation (DB access) at the end, to not do it needlessly
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return

        payload = {
            'course_id': course_id,
            'resource_id': problem_id,
            'student_id': self._get_student_id(user),
            'result': is_correct
        }

        headers = {
            'Authorization': self._get_authorization_header(self.secret)
        }

        request_payload_string = json.dumps({'payload': json.dumps(payload)})
        request_payload = {'request': request_payload_string}
        endpoint = self.oli_analytics_service_url + self.path
        try:
            log.info(endpoint)
            log.info(request_payload_string)
            response = requests.put(
                endpoint,
                data=request_payload,
                timeout=self.timeout_in_secs,
                headers=headers
            )
            response.raise_for_status()
            log.info(response.text)
        except RequestException:
            log.warning('Unable to send event to OLI analytics service', exc_info=True)

    def _get_student_id(self, user):
        return anonymous_id_for_user(user, None)

    def _get_authorization_header(self, secret):
        return secret
