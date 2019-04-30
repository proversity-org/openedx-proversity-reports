"""
This file contains the views for openedx-proversity-reports
"""
import logging

from celery.result import AsyncResult
from django.http import JsonResponse
from openedx_proversity_reports.edxapp_wrapper.get_edx_rest_framework_extensions import get_jwt_authentication
from openedx_proversity_reports.edxapp_wrapper.get_openedx_permissions import get_staff_or_owner
from openedx_proversity_reports.tasks import generate_completion_report
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

logger = logging.getLogger(__name__)


class GenerateCompletionReportView(APIView):
    """
    This class allows to initialize a celery task in order to generate completion reports.
    """

    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def post(self, request):
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

        task = generate_completion_report.delay(courses, block_report_filter)
        state_url = request.build_absolute_uri(reverse('proversity-reports:api:v0:completion-report-data'))

        logger.info("The task with id = %s has been initialize.", task.id)

        json_response["success"] = True
        json_response["state_url"] = "{}?task_id={}".format(state_url, task.id)
        json_response["message"] = "The task with id = {} has been initialize.".format(task.id)

        return JsonResponse(json_response, status=status.HTTP_202_ACCEPTED)


class CompletionReportView(APIView):
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
        This method starts a celery task that generates a report with the information about
        the required activities and its state.

        **Params**

            task_id: the identifier for the task


        **Example Requests**:

            GET /proversity-reports/api/v0/completion-report-data?task_id=4309f98a-b7e9-48e6-b9a7-996e640ece2e/

        **Response Values**:

            status: task status.
            result: the task result.

        **Example Response**:
            {
               "status":"SUCCESS",
               "result":{
                  "course-v1:edx+cs101+2019":[
                     {
                        "username":"edx",
                        "user_id":2,
                        "vertical":{
                           "Problems-Unit-2":false,
                           "Rocketchat Teams-Unit":false,
                           "Problem-Unit":true,
                           "Subsection-Unit":true,
                           "Html-Unit":true,
                           "Problems-Unit-1":false,
                           "Html-Unit-2":true,
                           "Problems-Unit":false,
                           "Discussion-Unit":true,
                           "Html-Unit-3":true,
                           "Html-Unit-1":true,
                           "Video-Unit":false
                        }
                     }
                  ]
               }
            }
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
