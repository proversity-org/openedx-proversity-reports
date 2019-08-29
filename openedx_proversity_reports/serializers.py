"""
Serializers for openedx-proversity-reports.
"""
from rest_framework import serializers


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
    Serializer for the activity completion report.
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
