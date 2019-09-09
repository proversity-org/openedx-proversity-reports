"""
This file contains the views for openedx-proversity-reports.
"""
import json
import logging

from celery.result import AsyncResult
from django.conf import settings
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from openedx_proversity_reports.edxapp_wrapper.get_edx_rest_framework_extensions import \
    get_jwt_authentication
from openedx_proversity_reports.edxapp_wrapper.get_openedx_permissions import get_staff_or_owner
from openedx_proversity_reports.edxapp_wrapper.get_student_account_library import \
    get_user_salesforce_contact_id
from openedx_proversity_reports.reports.activity_completion_report import GenerateCompletionReport
from openedx_proversity_reports.serializers import SalesforceContactIdSerializer, ActivityCompletionReportSerializer
from openedx_proversity_reports.utils import (
    get_attribute_from_module,
    get_exisiting_users_by_email,
    get_user_course_enrollments,
)

logger = logging.getLogger(__name__)

SUPPORTED_TASKS_MODULE = 'openedx_proversity_reports.tasks'


class GenerateReportView(APIView):
    """
    This class allows to initialize a celery task in order to generate reports.
    """

    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def post(self, request, report_name):
        """
        This method starts a general task in order to build reports using the platform data.

        **Params**
            block_report_filter: List of block types to retrieve. **Optional**
            ** Example **
                    block_types_filter = [
                        'course',
                        'chapter',
                        'sequential',
                        'vertical',
                        'html',
                        'problem',
                        'video',
                        'discussion',
                        'drag-and-drop-v2',
                        'poll',
                        'word_cloud'
                    ]
            course_ids: List of course ids. This parameter must contain at least one value.
        **Example Requests**:
            POST /proversity-reports/proversity-reports/api/v0/generate-<supported-report-name>
        **Response Values**:
            * success: If the task has been started correctly.
            * status_url: This url provides the status and result for the task.
            * message: Response message.
        """
        report_name = report_name.replace('-', '_')
        task = get_attribute_from_module(SUPPORTED_TASKS_MODULE, report_name)

        if not (report_name in settings.OPR_SUPPORTED_TASKS or task):
            raise Http404

        courses = request.data.get("course_ids", [])

        json_response = dict(
            success=False,
            state_url=None,
            message=None
        )

        if not courses:
            message = 'The parameter course_ids has not been provided.'
            json_response['message'] = message
            logger.info(message)
            return JsonResponse(
                json_response,
                status=status.HTTP_400_BAD_REQUEST
            )

        task = task.delay(courses, **request.data)
        state_url = request.build_absolute_uri(reverse('proversity-reports:api:v0:get-report-data'))

        logger.info('The task with id = %s has been initialize.', task.id)

        json_response['success'] = True
        json_response['state_url'] = '{}?task_id={}'.format(state_url, task.id)
        json_response['message'] = 'The task with id = {} has been initialize.'.format(task.id)

        return JsonResponse(json_response, status=status.HTTP_202_ACCEPTED)


class GetReportView(APIView):
    """
    This class verifies the status for the given task id and returns the result.
    """

    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def get(self, request):
        """
        This method retrieves the requested celery task data by task id.

        **Params**
            task_id: the identifier for the task
        **Example Requests**:
            GET /proversity-reports/api/v0/get-report-data?task_id=<celery-uuid>/
        **Response Values**:
            status: task status.
            result: the task result.
        **Example Response**:
        """

        task_id = request.GET.get('task_id')

        if not task_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        task = AsyncResult(id=task_id)
        response_data = {
            'data': {
                'status': task.status,
                'result': None,
            },
            'status': status.HTTP_200_OK,
        }

        if task.successful():
            response_data['data']['result'] = task.result
        elif task.failed():
            logger.info(
                "The task with id = %s has been finalized with the following error %s.",
                task.id,
                task.info.message
            )

            try:
                response_data = json.loads(task.result.message)
            except ValueError:
                response_data['status'] = status.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            return JsonResponse(**response_data)
        except TypeError:
            response_data['status'] = status.HTTP_503_SERVICE_UNAVAILABLE
            response_data['data']['result'] = None

        return JsonResponse(**response_data)


class SalesforceContactId(APIView):
    """
    API class to interact with the UserSalesforceContactId model.
    """
    DEFAULT_CONTACT_ID_SOURCE = 'Salesforce'
    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def post(self, request):
        """
        This method creates a new record in the UserSalesforceContactId model
        for the given Salesforce contact id and user id.

        It's possible to create multiple records in the same request.

        **Params**

            records: List containing dict/s with the user id and contact id values. **Required**

            **Example**
                records = [
                    {
                        user_id: '',
                        contact_id: ''
                    },
                    ...
                ]

        **Example Requests**:

            POST /proversity-reports/api/v0/salesforce-contact-id

        **Response Values**:

            * success: Either, True if the operation was successful or False if not.
            * details: Operation message.
        """
        records_to_create = request.data.get('records', [])

        if not records_to_create:
            raise ValidationError(detail={'records': 'The records field cannot be empty.'})

        serialized_data = SalesforceContactIdSerializer(data=records_to_create, many=True)

        serialized_data.is_valid(raise_exception=True)

        salesforce_model = get_user_salesforce_contact_id()
        operation_errors = []

        for record in serialized_data.data:
            try:
                user = User.objects.get(id=record.get('user_id'))
            except User.DoesNotExist:
                message = 'User with id: {} does not exists, skipped.'.format(record.get('user_id'))
                operation_errors.append(message)
                continue

            salesforce_model.objects.get_or_create(
                user=user,
                contact_id=record.get('contact_id', ''),
                contact_id_source=self.DEFAULT_CONTACT_ID_SOURCE,
            )

        if operation_errors:
            json_response = dict(
                success=False,
                details=operation_errors,
            )
        else:
            json_response = dict(
                success=True,
                details='All records were created successfully.',
            )

        return JsonResponse(json_response, status=status.HTTP_200_OK)


class UserActivityCompletionView(APIView):
    """
    This class is intended to return the activity completion data per user.
    """

    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def post(self, request):
        """
        Return a JSON representation of the activity completion data by user.

        **Params**
            users: List of the email of the users. This parameter may be empty but it must contain at least one value to get data.
            course_ids: List of course ids to filter only by those courses. This parameter may be empty.
            block_types: List of the block types to get the completion data.
                This parameter may be empty but it must contain at least one value to get data
            passing_score: Integer between 0 and 1, which is the percentage of videos that must be viewed.

            **Example**
            {
                "course_ids": [
                    "course-v1:edX+DemoX+Demo_Course"
                ],
                "block_types": ["video"],
                "passing_score": 0.75,
                "users": [
                    "honor@example.com",
                    "audit@example.com"
                ]
            }
        **Example Requests**:
            POST /proversity-reports/proversity-reports/api/v0/user-activity-completion-data
        **Response Values**:
            * result: Activity completion data per user.

            **Example**
            {
                "result": {
                    "users": {
                        "audit@example.com": {
                            "course-v1:edX+DemoX+Demo_Course": {
                                "Activity name 5": "not_completed",
                                "Activity name 4": "not_completed",
                                "course_is_complete": true,
                                "Activity name 2": "completed",
                                "total_activities": 5,
                                "Activity name": "completed",
                                "Activity name 3": "completed",
                                "completed_activities": 3
                            }
                        },
                    }
                }
            }
        """
        completion_data = {}
        serialized_data = ActivityCompletionReportSerializer(data=request.data)

        serialized_data.is_valid(raise_exception=True)

        user_list = get_exisiting_users_by_email(serialized_data.data.get('users', []))

        for user in user_list:
            user_course_keys = serialized_data.data.get('course_keys', []) or get_user_course_enrollments(user)
            course_user_completion_data = {}

            for course_key in user_course_keys:
                activity_completion_data = GenerateCompletionReport.activity_completion_data_per_user(
                    user=user,
                    course_key=course_key,
                    block_types=serialized_data.data.get('block_types', []),
                    passing_score=serialized_data.data.get('passing_score', 0),
                ).get_user_completion_data()

                course_data = {
                    str(course_key): activity_completion_data,
                }

                course_user_completion_data.update(course_data)

            completion_data.update({
                user.email: course_user_completion_data,
            })

        json_response = {
            'result': {
                'users': completion_data,
            }
        }

        return JsonResponse(json_response, status=status.HTTP_200_OK)
