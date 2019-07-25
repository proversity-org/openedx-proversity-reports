"""
This file contains the views for openedx-proversity-reports
"""
import logging

from celery.result import AsyncResult
from django.http import JsonResponse, Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from openedx_proversity_reports.edxapp_wrapper.get_edx_rest_framework_extensions import get_jwt_authentication
from openedx_proversity_reports.edxapp_wrapper.get_openedx_permissions import get_staff_or_owner
from openedx_proversity_reports.tasks import (
    generate_completion_report,
    generate_last_page_accessed_report,
    generate_time_spent_report,
    generate_learning_tracker_report,
)

logger = logging.getLogger(__name__)
TASKS = {
    'generate-completion-report': generate_completion_report,
    'generate-last-page-accessed-report': generate_last_page_accessed_report,
    'generate-time-spent-report': generate_time_spent_report,
    'generate-learning-tracker-report': generate_learning_tracker_report
}


class GenerateReportView(APIView):
    """
    This class allows to initialize a celery task in order to generate completion reports.
    """

    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def post(self, request, report_name):
        """
        This method starts a celery task that generates a report with the information about
        the required activities and its state.

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

            POST /proversity-reports/completion-report/

        **Response Values**:

            * success: If the task has been started correctly.

            * status_url: this url provides the satus and result for the task.

            * message: Response message.

        """

        task = TASKS.get(report_name)

        if not task:
            raise Http404

        courses = request.data.get("course_ids", [])

        json_response = dict(
            success=False,
            state_url=None,
            message=None
        )

        if not courses:
            message = "The parameter course_ids has not been provided."
            json_response["message"] = message
            logger.info(message)
            return JsonResponse(
                json_response,
                status=status.HTTP_400_BAD_REQUEST
            )

        block_report_filter = request.data.get("block_report_filter", ["vertical"])

        task = task.delay(courses, block_report_filter=block_report_filter)
        state_url = request.build_absolute_uri(reverse('proversity-reports:api:v0:get-report-data'))

        logger.info("The task with id = %s has been initialize.", task.id)

        json_response["success"] = True
        json_response["state_url"] = "{}?task_id={}".format(state_url, task.id)
        json_response["message"] = "The task with id = {} has been initialize.".format(task.id)

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

            GET /proversity-reports/api/v0/time-spent-report-data?task_id=4309f98a-b7e9-48e6-b9a7-996e640ece2e/

        **Response Values**:

            status: task status.
            result: the task result.

        **Example Response**:

        """

        task_id = request.GET.get("task_id")

        if not task_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        task = AsyncResult(id=task_id)
        result = None

        if task.successful():
            result = task.result
        elif task.failed():
            logger.info(
                "The task with id = %s has been finalized with the following error %s.",
                task.id,
                task.info.message
            )
            result = None

        try:
            return JsonResponse(
                data={"status": task.status, "result": result},
                status=status.HTTP_200_OK,
            )
        except TypeError:
            return JsonResponse(
                data={"status": "Failed", "result": None},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
