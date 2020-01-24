"""
Serializers for openedx-proversity-reports.
"""
from django.conf import settings
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import serializers
from rest_framework.serializers import ValidationError


class UserSessionSerializer(serializers.Serializer):
    """
    Serializer for the user session data  providing minimal data about the session.
    """
    last_session = serializers.DateTimeField()
    avg_session = serializers.FloatField()
    length_current_session = serializers.FloatField()
    time_between_sessions = serializers.FloatField()
    session_number = serializers.IntegerField(min_value=0)


class EnrollmentReportSerializer(serializers.Serializer):
    """
    Serializer for date parameters in the enrollment report.
    """
    updated_at = serializers.DateField(required=False)
    oldest = serializers.DateField(required=False)
    latest = serializers.DateField(required=False)


class SalesforceContactIdSerializer(serializers.Serializer):
    """
    Serializer for the Salesforce contact id model.
    """
    user_id = serializers.IntegerField()
    contact_id = serializers.CharField(max_length=60)
    contact_id_source = serializers.CharField(required=False, max_length=60)


class ActivityCompletionReportSerializer(serializers.Serializer):
    """
    Serializer for the activity completion report and the activity completion per user API.
    """
    required_activity_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
    )
    block_types = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
    )
    passing_score = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        coerce_to_string=False,
        max_value=1,
        min_value=0,
        required=False,
    )
    users = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
    )
    course_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
    )
    course_keys = serializers.SerializerMethodField()


    def get_course_keys(self, obj):
        """
        Return a list of opaque_keys.edx.keys.CourseKey instances according to the course_ids field.

        Args:
            obj: Serializer fields object.
        Returns:
            course_keys: List containing opaque_keys.edx.keys.CourseKey course instances.
        """
        course_keys = []

        for course_id in obj.get('course_ids', []):
            try:
                course_keys.append(CourseKey.from_string(course_id))
            except InvalidKeyError:
                continue

        return course_keys


class GenerateReportViewSerializer(serializers.Serializer):
    """
    Serializer for the POST method of the GenerateReportView API endpoint.
    """
    course_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=True,
    )
    course_keys = serializers.SerializerMethodField()
    limit = serializers.IntegerField(
        required=False,
        default=getattr(settings, 'OPR_DEFAULT_PAGE_RESULTS_LIMIT', 10),
        min_value=0,
    )

    def get_course_keys(self, obj):
        """
        Return a list of opaque_keys.edx.keys.CourseKey instances according to the course_ids field.

        Args:
            obj: Serializer fields object.
        Returns:
            course_keys: List containing opaque_keys.edx.keys.CourseKey course instances.
        """
        course_keys = []

        for course_id in obj.get('course_ids', []):
            try:
                course_keys.append(CourseKey.from_string(course_id))
            except InvalidKeyError:
                continue

        return course_keys
