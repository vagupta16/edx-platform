"""
:class:`~xblock.field_data.FieldData` subclasses used by the CMS
"""

from django.conf import settings

from xblock.field_data import ConfigurationFieldData, SplitFieldData
from xblock.fields import Scope


class CmsFieldData(SplitFieldData):
    """
    A :class:`~xblock.field_data.FieldData` that
    reads all UserScope.ONE and UserScope.ALL fields from `student_data`
    and most UserScope.NONE fields from `authored_data`. UserScope.NONE,
    BlockScope.TYPE (i.e., Scope.configuration) is read from 'platform_data'.
    It allows writing to `student_data` and `authored_data`, but not 
    `platform_data`.
    """
    def __init__(self, authored_data, student_data):
        # Make sure that we don't repeatedly nest CmsFieldData instances
        if isinstance(authored_data, CmsFieldData):
            authored_data = authored_data._authored_data  # pylint: disable=protected-access
        platform_data = ConfigurationFieldData(getattr(settings, 'XBLOCK_CONFIGURATION', {}))

        self._authored_data = authored_data
        self._student_data = student_data
        self._platform_data = platform_data
        import wtf; wtf.wtf(wvars=['settings', 'authored_data', 'student_data', 'platform_data'])
        print "********************\n{}\n********************".format(str(platform_data._data))

        super(CmsFieldData, self).__init__({
            Scope.configuration: platform_data,
            Scope.content: authored_data,
            Scope.settings: authored_data,
            Scope.parent: authored_data,
            Scope.children: authored_data,
            Scope.user_state_summary: student_data,
            Scope.user_state: student_data,
            Scope.user_info: student_data,
            Scope.preferences: student_data,
        })
