"""
Tests for keyword_substitution.py
"""

from django.test import TestCase
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory

from student.models import anonymous_id_for_user
from util.keyword_substitution import substitute_keywords_with_data


class KeywordSubTest(TestCase):

    def setUp(self):
        self.user = UserFactory.create(
            email="testuser@edx.org",
            username="testuser",
            profile__name="Test User"
        )
        self.course = CourseFactory.create(
            org='edx',
            course='999'
        )

    def test_anonymous_id_sub(self):
        test_string = "This is the test string. sub this: %%USER_ID%% into anon_id"
        anon_id = anonymous_id_for_user(self.user, self.course.id)
        result = substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertIn("this: " + anon_id + " into", result)
        self.assertNotIn("%%USER_ID%%", result)

    def test_name_sub(self):
        test_string = "This is the test string. subthis:  %%USER_FULLNAME%% into user name"
        user_name = self.user.profile.name
        result = substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertRegexpMatches(result, ".* " + user_name + " .*")

    def test_anonymous_id_sub_html(self):
        """
        Test that sub-ing works in html tags as well
        """
        test_string = "<some tag>%%USER_ID%%</some tag>"
        anon_id = anonymous_id_for_user(self.user, self.course.id)
        result = substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertEquals(result, "<some tag>" + anon_id + "</some tag>")

    def test_illegal_subtag(self):
        """
        Test that sub-ing doesn't ocurr with illegal tags
        """
        test_string = "%%user_id%%"
        result = substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertEquals(test_string, result)

    def test_should_not_sub(self):
        """
        Test that sub-ing doesn't work with no subtags
        """
        test_string = "this string has no subtags"
        result = substitute_keywords_with_data(test_string, self.user.id, self.course.id)

        self.assertEquals(test_string, result)
