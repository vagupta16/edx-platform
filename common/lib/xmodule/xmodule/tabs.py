"""
Implement CourseTab
"""

from abc import ABCMeta
import logging

from xblock.fields import List
<<<<<<< HEAD
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
=======
from openedx.core.lib.api.plugins import PluginError
>>>>>>> hotfix-2015-08-20

# We should only scrape strings for i18n in this file, since the target language is known only when
# they are rendered in the template.  So ugettext gets called in the template.
_ = lambda text: text

log = logging.getLogger("edx.courseware")


class CourseTab(object):
    """
    The Course Tab class is a data abstraction for all tabs (i.e., course navigation links) within a course.
    It is an abstract class - to be inherited by various tab types.
    Derived classes are expected to override methods as needed.
    When a new tab class is created, it should define the type and add it in this class' factory method.
    """
    __metaclass__ = ABCMeta

    # Class property that specifies the type of the tab.  It is generally a constant value for a
    # subclass, shared by all instances of the subclass.
    type = ''

    # The title of the tab, which should be internationalized using
    # ugettext_noop since the user won't be available in this context.
    title = None

    # Class property that specifies whether the tab can be hidden for a particular course
    is_hideable = False

    # Class property that specifies whether the tab is hidden for a particular course
    is_hidden = False

    # The relative priority of this view that affects the ordering (lower numbers shown first)
    priority = None

    # Class property that specifies whether the tab can be moved within a course's list of tabs
    is_movable = True

    # Class property that specifies whether the tab is a collection of other tabs
    is_collection = False

    # True if this tab is dynamically added to the list of tabs
    is_dynamic = False

    # True if this tab is a default for the course (when enabled)
    is_default = True

    # True if this tab can be included more than once for a course.
    allow_multiple = False

    # If there is a single view associated with this tab, this is the name of it
    view_name = None

    def __init__(self, tab_dict):
        """
        Initializes class members with values passed in by subclasses.

        Args:
            tab_dict (dict) - a dictionary of parameters used to build the tab.
        """

        self.name = tab_dict.get('name', self.title)
        self.tab_id = tab_dict.get('tab_id', getattr(self, 'tab_id', self.type))
        self.link_func = tab_dict.get('link_func', link_reverse_func(self.view_name))

        self.is_hidden = tab_dict.get('is_hidden', False)

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        """Returns true if this course tab is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): an optional user interacting with the course (defaults to None)
        """
        raise NotImplementedError()

    def get(self, key, default=None):
        """
        Akin to the get method on Python dictionary objects, gracefully returns the value associated with the
        given key, or the default if key does not exist.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        """
        This method allows callers to access CourseTab members with the d[key] syntax as is done with
        Python dictionary objects.
        """
        if key == 'name':
            return self.name
        elif key == 'type':
            return self.type
        elif key == 'tab_id':
            return self.tab_id
        elif key == 'is_hidden':
            return self.is_hidden
        else:
            raise KeyError('Key {0} not present in tab {1}'.format(key, self.to_json()))

    def __setitem__(self, key, value):
        """
        This method allows callers to change CourseTab members with the d[key]=value syntax as is done with
        Python dictionary objects.  For example: course_tab['name'] = new_name

        Note: the 'type' member can be 'get', but not 'set'.
        """
        if key == 'name':
            self.name = value
        elif key == 'tab_id':
            self.tab_id = value
        elif key == 'is_hidden':
            self.is_hidden = value
        else:
            raise KeyError('Key {0} cannot be set in tab {1}'.format(key, self.to_json()))

    def __eq__(self, other):
        """
        Overrides the equal operator to check equality of member variables rather than the object's address.
        Also allows comparison with dict-type tabs (needed to support callers implemented before this class
        was implemented).
        """

        if isinstance(other, dict) and not self.validate(other, raise_error=False):
            # 'other' is a dict-type tab and did not validate
            return False

        # allow tabs without names; if a name is required, its presence was checked in the validator.
        name_is_eq = (other.get('name') is None or self.name == other['name'])

        # only compare the persisted/serialized members: 'type' and 'name'
        return self.type == other.get('type') and name_is_eq

    def __ne__(self, other):
        """
        Overrides the not equal operator as a partner to the equal operator.
        """
        return not self == other

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """
        Validates the given dict-type tab object to ensure it contains the expected keys.
        This method should be overridden by subclasses that require certain keys to be persisted in the tab.
        """
        return key_checker(['type'])(tab_dict, raise_error)

    @classmethod
    def load(cls, type_name, **kwargs):
        """
        Constructs a tab of the given type_name.

        Args:
            type_name (str) - the type of tab that should be constructed
            **kwargs - any other keyword arguments needed for constructing this tab

        Returns:
            an instance of the CourseTab subclass that matches the type_name
        """
        json_dict = kwargs.copy()
        json_dict['type'] = type_name
        return cls.from_json(json_dict)

    def to_json(self):
        """
        Serializes the necessary members of the CourseTab object to a json-serializable representation.
        This method is overridden by subclasses that have more members to serialize.

        Returns:
            a dictionary with keys for the properties of the CourseTab object.
        """
        to_json_val = {'type': self.type, 'name': self.name}
        if self.is_hidden:
            to_json_val.update({'is_hidden': True})
        return to_json_val

    @staticmethod
    def from_json(tab_dict):
        """
        Deserializes a CourseTab from a json-like representation.

        The subclass that is instantiated is determined by the value of the 'type' key in the
        given dict-type tab. The given dict-type tab is validated before instantiating the CourseTab object.

        If the tab_type is not recognized, then an exception is logged and None is returned.
        The intention is that the user should still be able to use the course even if a
        particular tab is not found for some reason.

        Args:
            tab: a dictionary with keys for the properties of the tab.

        Raises:
            InvalidTabsException if the given tab doesn't have the right keys.
        """
        # TODO: don't import openedx capabilities from common
        from openedx.core.lib.course_tabs import CourseTabPluginManager
        tab_type_name = tab_dict.get('type')
        if tab_type_name is None:
            log.error('No type included in tab_dict: %r', tab_dict)
            return None
        try:
            tab_type = CourseTabPluginManager.get_plugin(tab_type_name)
        except PluginError:
            log.exception(
                "Unknown tab type %r Known types: %r.",
                tab_type_name,
                CourseTabPluginManager.get_tab_types()
            )
            return None

        tab_type.validate(tab_dict)
        return tab_type(tab_dict=tab_dict)


class StaticTab(CourseTab):
    """
    A custom tab.
    """
    type = 'static_tab'
    is_default = False  # A static tab is never added to a course by default
    allow_multiple = True

    def __init__(self, tab_dict=None, name=None, url_slug=None):
        def link_func(course, reverse_func):
            """ Returns a url for a given course and reverse function. """
            return reverse_func(self.type, args=[course.id.to_deprecated_string(), self.url_slug])

        self.url_slug = tab_dict.get('url_slug') if tab_dict else url_slug

        if tab_dict is None:
            tab_dict = dict()

        if name is not None:
            tab_dict['name'] = name

        tab_dict['link_func'] = link_func
        tab_dict['tab_id'] = 'static_tab_{0}'.format(self.url_slug)

        super(StaticTab, self).__init__(tab_dict)

    @classmethod
    def is_enabled(cls, course, user=None):  # pylint: disable=unused-argument
        """
        Static tabs are viewable to everyone, even anonymous users.
        """
        return True

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        """
        Ensures that the specified tab_dict is valid.
        """
        return (super(StaticTab, cls).validate(tab_dict, raise_error)
                and key_checker(['name', 'url_slug'])(tab_dict, raise_error))

    def __getitem__(self, key):
        if key == 'url_slug':
            return self.url_slug
        else:
            return super(StaticTab, self).__getitem__(key)

    def __setitem__(self, key, value):
        if key == 'url_slug':
            self.url_slug = value
        else:
            super(StaticTab, self).__setitem__(key, value)

    def to_json(self):
        """ Return a dictionary representation of this tab. """
        to_json_val = super(StaticTab, self).to_json()
        to_json_val.update({'url_slug': self.url_slug})
        return to_json_val

    def __eq__(self, other):
        if not super(StaticTab, self).__eq__(other):
            return False
        return self.url_slug == other.get('url_slug')


<<<<<<< HEAD
class SingleTextbookTab(CourseTab):
    """
    A tab representing a single textbook.  It is created temporarily when enumerating all textbooks within a
    Textbook collection tab.  It should not be serialized or persisted.
    """
    type = 'single_textbook'
    is_movable = False
    is_collection_item = True

    def to_json(self):
        raise NotImplementedError('SingleTextbookTab should not be serialized.')


class TextbookTabsBase(AuthenticatedCourseTab):
    """
    Abstract class for textbook collection tabs classes.
    """
    is_collection = True

    def __init__(self, tab_id):
        # Translators: 'Textbooks' refers to the tab in the course that leads to the course' textbooks
        super(TextbookTabsBase, self).__init__(
            name=_("Textbooks"),
            tab_id=tab_id,
            link_func=None,
        )

    @abstractmethod
    def items(self, course):
        """
        A generator for iterating through all the SingleTextbookTab book objects associated with this
        collection of textbooks.
        """
        pass


class TextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all textbook tabs.
    """
    type = 'textbooks'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(TextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def can_display(self, course, settings, is_user_authenticated, is_user_staff, is_user_enrolled):
        return settings.FEATURES.get('ENABLE_TEXTBOOK')

    def items(self, course):
        for index, textbook in enumerate(course.textbooks):
            yield SingleTextbookTab(
                name=textbook.title,
                tab_id='textbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class PDFTextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all PDF textbook tabs.
    """
    type = 'pdf_textbooks'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(PDFTextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def items(self, course):
        for index, textbook in enumerate(course.pdf_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='pdftextbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'pdf_book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class HtmlTextbookTabs(TextbookTabsBase):
    """
    A tab representing the collection of all Html textbook tabs.
    """
    type = 'html_textbooks'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(HtmlTextbookTabs, self).__init__(
            tab_id=self.type,
        )

    def items(self, course):
        for index, textbook in enumerate(course.html_textbooks):
            yield SingleTextbookTab(
                name=textbook['tab_title'],
                tab_id='htmltextbook/{0}'.format(index),
                link_func=lambda course, reverse_func, index=index: reverse_func(
                    'html_book', args=[course.id.to_deprecated_string(), index]
                ),
            )


class GradingTab(object):
    """
    Abstract class for tabs that involve Grading.
    """
    pass


class StaffGradingTab(StaffTab, GradingTab):
    """
    A tab for staff grading.
    """
    type = 'staff_grading'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(StaffGradingTab, self).__init__(
            # Translators: "Staff grading" appears on a tab that allows
            # staff to view open-ended problems that require staff grading
            name=_("Staff grading"),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class PeerGradingTab(AuthenticatedCourseTab, GradingTab):
    """
    A tab for peer grading.
    """
    type = 'peer_grading'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(PeerGradingTab, self).__init__(
            # Translators: "Peer grading" appears on a tab that allows
            # students to view open-ended problems that require grading
            name=_("Peer grading"),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class OpenEndedGradingTab(AuthenticatedCourseTab, GradingTab):
    """
    A tab for open ended grading.
    """
    type = 'open_ended'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(OpenEndedGradingTab, self).__init__(
            # Translators: "Assessment Panel" appears on a tab that, when clicked, opens up a panel that
            # displays information about open-ended problems that a user has submitted or needs to grade
            name=_("Assessment Panel"),
            tab_id=self.type,
            link_func=link_reverse_func('open_ended_notifications'),
        )


class SyllabusTab(CourseTab):
    """
    A tab for the course syllabus.
    """
    type = 'syllabus'

    def can_display(self, course, settings, is_user_authenticated, is_user_staff, is_user_enrolled):
        return hasattr(course, 'syllabus_present') and course.syllabus_present

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(SyllabusTab, self).__init__(
            # Translators: "Syllabus" appears on a tab that, when clicked, opens the syllabus of the course.
            name=_('Syllabus'),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )


class NotesTab(AuthenticatedCourseTab):
    """
    A tab for the course notes.
    """
    type = 'notes'

    def can_display(self, course, settings, is_user_authenticated, is_user_staff, is_user_enrolled):
        return settings.FEATURES.get('ENABLE_STUDENT_NOTES')

    def __init__(self, tab_dict=None):
        super(NotesTab, self).__init__(
            name=tab_dict['name'],
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(NotesTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class EdxNotesTab(AuthenticatedCourseTab):
    """
    A tab for the course student notes.
    """
    type = 'edxnotes'

    def can_display(self, course, settings, is_user_authenticated, is_user_staff, is_user_enrolled):
        return settings.FEATURES.get('ENABLE_EDXNOTES')

    def __init__(self, tab_dict=None):
        super(EdxNotesTab, self).__init__(
            name=tab_dict['name'] if tab_dict else _('Notes'),
            tab_id=self.type,
            link_func=link_reverse_func(self.type),
        )

    @classmethod
    def validate(cls, tab_dict, raise_error=True):
        return super(EdxNotesTab, cls).validate(tab_dict, raise_error) and need_name(tab_dict, raise_error)


class InstructorTab(StaffTab):
    """
    A tab for the course instructors.
    """
    type = 'instructor'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(InstructorTab, self).__init__(
            # Translators: 'Instructor' appears on the tab that leads to the instructor dashboard, which is
            # a portal where an instructor can get data and perform various actions on their course
            name=_('Instructor'),
            tab_id=self.type,
            link_func=link_reverse_func('instructor_dashboard'),
        )


class CcxCoachTab(CourseTab):
    """
    A tab for the custom course coaches.
    """
    type = 'ccx_coach'

    def __init__(self, tab_dict=None):  # pylint: disable=unused-argument
        super(CcxCoachTab, self).__init__(
            name=_('CCX Coach'),
            tab_id=self.type,
            link_func=link_reverse_func('ccx_coach_dashboard'),
        )

    def can_display(self, course, settings, *args, **kw):
        """
        Since we don't get the user here, we use a thread local defined in the ccx
        overrides to get it, then use the course to get the coach role and find out if
        the user is one.
        """
        user_is_coach = False
        if settings.FEATURES.get('CUSTOM_COURSES_EDX', False):
            from opaque_keys.edx.locations import SlashSeparatedCourseKey
            from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
            from ccx.overrides import get_current_request  # pylint: disable=import-error
            course_id = course.id.to_deprecated_string()
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
            role = CourseCcxCoachRole(course_key)
            request = get_current_request()
            if request is not None:
                user_is_coach = role.has_user(request.user)
        super_can_display = super(CcxCoachTab, self).can_display(
            course, settings, *args, **kw
        )
        return user_is_coach and super_can_display


=======
>>>>>>> hotfix-2015-08-20
class CourseTabList(List):
    """
    An XBlock field class that encapsulates a collection of Tabs in a course.
    It is automatically created and can be retrieved through a CourseDescriptor object: course.tabs
    """

    # TODO: Ideally, we'd like for this list of tabs to be dynamically
    # generated by the tabs plugin code. For now, we're leaving it like this to
    # preserve backwards compatibility.
    @staticmethod
    def initialize_default(course):
        """
        An explicit initialize method is used to set the default values, rather than implementing an
        __init__ method.  This is because the default values are dependent on other information from
        within the course.
        """

        course.tabs.extend([
            CourseTab.load('courseware'),
            CourseTab.load('course_info')
        ])

        # Presence of syllabus tab is indicated by a course attribute
        if hasattr(course, 'syllabus_present') and course.syllabus_present:
            course.tabs.append(CourseTab.load('syllabus'))

        # If the course has a discussion link specified, use that even if we feature
        # flag discussions off. Disabling that is mostly a server safety feature
        # at this point, and we don't need to worry about external sites.
        if course.discussion_link:
            discussion_tab = CourseTab.load(
                'external_discussion', name=_('External Discussion'), link=course.discussion_link
            )
        else:
            discussion_tab = CourseTab.load('discussion')

        course.tabs.extend([
            CourseTab.load('textbooks'),
            discussion_tab,
            CourseTab.load('wiki'),
            CourseTab.load('progress'),
        ])

    @staticmethod
    def get_discussion(course):
        """
        Returns the discussion tab for the given course.  It can be either of type 'discussion'
        or 'external_discussion'.  The returned tab object is self-aware of the 'link' that it corresponds to.
        """

        # the discussion_link setting overrides everything else, even if there is a discussion tab in the course tabs
        if course.discussion_link:
            return CourseTab.load(
                'external_discussion', name=_('External Discussion'), link=course.discussion_link
            )

        # find one of the discussion tab types in the course tabs
        for tab in course.tabs:
            if tab.type == 'discussion' or tab.type == 'external_discussion':
                return tab
        return None

    @staticmethod
    def get_tab_by_slug(tab_list, url_slug):
        """
        Look for a tab with the specified 'url_slug'.  Returns the tab or None if not found.
        """
        return next((tab for tab in tab_list if tab.get('url_slug') == url_slug), None)

    @staticmethod
    def get_tab_by_type(tab_list, tab_type):
        """
        Look for a tab with the specified type.  Returns the first matching tab.
        """
        return next((tab for tab in tab_list if tab.type == tab_type), None)

    @staticmethod
    def get_tab_by_id(tab_list, tab_id):
        """
        Look for a tab with the specified tab_id.  Returns the first matching tab.
        """
        return next((tab for tab in tab_list if tab.tab_id == tab_id), None)

    SNEAKPEEK_TAB_TYPES = [CoursewareTab, CourseInfoTab, StaticTab, SyllabusTab]

    @staticmethod
<<<<<<< HEAD
    def iterate_displayable(
            course,
            settings,
            is_user_authenticated=True,
            is_user_staff=True,
            is_user_enrolled=False,
            is_user_sneakpeek=False,
    ):
=======
    def iterate_displayable(course, user=None, inline_collections=True):
>>>>>>> hotfix-2015-08-20
        """
        Generator method for iterating through all tabs that can be displayed for the given course and
        the given user with the provided access settings.
        """
        for tab in course.tabs:
<<<<<<< HEAD
            if (
                tab.can_display(course, settings, is_user_authenticated, is_user_staff, is_user_enrolled) and
                (not tab.is_hideable or not tab.is_hidden) and
                (not is_user_sneakpeek or any([isinstance(tab, t) for t in CourseTabList.SNEAKPEEK_TAB_TYPES]))
            ):
=======
            if tab.is_enabled(course, user=user) and not (user and tab.is_hidden):
>>>>>>> hotfix-2015-08-20
                if tab.is_collection:
                    # If rendering inline that add each item in the collection,
                    # else just show the tab itself as long as it is not empty.
                    if inline_collections:
                        for item in tab.items(course):
                            yield item
                    elif len(list(tab.items(course))) > 0:
                        yield tab
                else:
                    yield tab

    @classmethod
    def validate_tabs(cls, tabs):
        """
        Check that the tabs set for the specified course is valid.  If it
        isn't, raise InvalidTabsException with the complaint.

        Specific rules checked:
        - if no tabs specified, that's fine
        - if tabs specified, first two must have type 'courseware' and 'course_info', in that order.

        """
        if tabs is None or len(tabs) == 0:
            return

        if len(tabs) < 2:
            raise InvalidTabsException("Expected at least two tabs.  tabs: '{0}'".format(tabs))

        if tabs[0].get('type') != 'courseware':
            raise InvalidTabsException(
                "Expected first tab to have type 'courseware'.  tabs: '{0}'".format(tabs))

        if tabs[1].get('type') != 'course_info':
            raise InvalidTabsException(
                "Expected second tab to have type 'course_info'.  tabs: '{0}'".format(tabs))

        # the following tabs should appear only once
        # TODO: don't import openedx capabilities from common
        from openedx.core.lib.course_tabs import CourseTabPluginManager
        for tab_type in CourseTabPluginManager.get_tab_types():
            if not tab_type.allow_multiple:
                cls._validate_num_tabs_of_type(tabs, tab_type.type, 1)

    @staticmethod
    def _validate_num_tabs_of_type(tabs, tab_type, max_num):
        """
        Check that the number of times that the given 'tab_type' appears in 'tabs' is less than or equal to 'max_num'.
        """
        count = sum(1 for tab in tabs if tab.get('type') == tab_type)
        if count > max_num:
            msg = (
                "Tab of type '{type}' appears {count} time(s). "
                "Expected maximum of {max} time(s)."
            ).format(
                type=tab_type, count=count, max=max_num,
            )
            raise InvalidTabsException(msg)

    def to_json(self, values):
        """
        Overrides the to_json method to serialize all the CourseTab objects to a json-serializable representation.
        """
        json_data = []
        if values:
            for val in values:
                if isinstance(val, CourseTab):
                    json_data.append(val.to_json())
                elif isinstance(val, dict):
                    json_data.append(val)
                else:
                    continue
        return json_data

    def from_json(self, values):
        """
        Overrides the from_json method to de-serialize the CourseTab objects from a json-like representation.
        """
        self.validate_tabs(values)
        tabs = []
        for tab_dict in values:
            tab = CourseTab.from_json(tab_dict)
            if tab:
                tabs.append(tab)
        return tabs


# Validators
#  A validator takes a dict and raises InvalidTabsException if required fields are missing or otherwise wrong.
# (e.g. "is there a 'name' field?).  Validators can assume that the type field is valid.
def key_checker(expected_keys):
    """
    Returns a function that checks that specified keys are present in a dict.
    """

    def check(actual_dict, raise_error=True):
        """
        Function that checks whether all keys in the expected_keys object is in the given actual_dict object.
        """
        missing = set(expected_keys) - set(actual_dict.keys())
        if not missing:
            return True
        if raise_error:
            raise InvalidTabsException(
                "Expected keys '{0}' are not present in the given dict: {1}".format(expected_keys, actual_dict)
            )
        else:
            return False

    return check


def link_reverse_func(reverse_name):
    """
    Returns a function that takes in a course and reverse_url_func,
    and calls the reverse_url_func with the given reverse_name and course's ID.

    This is used to generate the url for a CourseTab without having access to Django's reverse function.
    """
    return lambda course, reverse_url_func: reverse_url_func(reverse_name, args=[course.id.to_deprecated_string()])


def need_name(dictionary, raise_error=True):
    """
    Returns whether the 'name' key exists in the given dictionary.
    """
    return key_checker(['name'])(dictionary, raise_error)


class InvalidTabsException(Exception):
    """
    A complaint about invalid tabs.
    """
    pass


class UnequalTabsException(Exception):
    """
    A complaint about tab lists being unequal
    """
    pass


# Tab functions
def validate_args(num, tab_type):
    "Throws for the disallowed cases."
    if num <= 1:
        raise ValueError('Tabs 1 and 2 cannot be edited')
    if tab_type == 'static_tab':
        raise ValueError('Tabs of type static_tab cannot be edited here (use Studio)')


def primitive_delete(course, num):
    "Deletes the given tab number (0 based)."
    tabs = course.tabs
    validate_args(num, tabs[num].get('type', ''))
    del tabs[num]
    # Note for future implementations: if you delete a static_tab, then Chris Dodge
    # points out that there's other stuff to delete beyond this element.
    # This code happens to not delete static_tab so it doesn't come up.
    modulestore().update_item(course, ModuleStoreEnum.UserID.primitive_command)


def primitive_insert(course, num, tab_type, name):
    "Inserts a new tab at the given number (0 based)."
    validate_args(num, tab_type)
    new_tab = CourseTab.from_json({u'type': unicode(tab_type), u'name': unicode(name)})
    tabs = course.tabs
    tabs.insert(num, new_tab)
    modulestore().update_item(course, ModuleStoreEnum.UserID.primitive_command)
