"""
This file contains the views for openedx-proversity-reports API V1.
"""
import json
import logging

from celery.result import AsyncResult
from django.conf import settings
from django.http import Http404, JsonResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from openedx_proversity_reports.edxapp_wrapper.get_edx_rest_framework_extensions import \
    get_jwt_authentication
from openedx_proversity_reports.edxapp_wrapper.get_openedx_permissions import \
    get_staff_or_owner
from openedx_proversity_reports.serializers import GenerateReportViewSerializer
from openedx_proversity_reports.utils import (
    get_attribute_from_module,
    get_report_backend,
)

logger = logging.getLogger(__name__)


class GenerateReportView(APIView):
    """
    Select and Initialize the report backend to get the report data.
    """
    authentication_classes = (
        OAuth2Authentication,
        get_jwt_authentication(),
    )
    permission_classes = (permissions.IsAuthenticated, get_staff_or_owner())

    def post(self, request, report_name):
        """
        Select the corresponding report backend for the requested report data.

        **Params**
            course_ids: List of course ids. This parameter must contain at least one value.
        **Example Requests**:
            POST /proversity-reports/proversity-reports/api/v1/generate-<report-name>
        """
        request_data = {item: value for item, value in (request.data.items() + request.query_params.items())}
        serialized_data = GenerateReportViewSerializer(data=request_data)

        serialized_data.is_valid(raise_exception=True)

        report_backend, report_backend_settings = get_report_backend(report_name)

        if not report_backend:
            raise Http404

        backend_instance = report_backend(report_settings=report_backend_settings, **serialized_data.data)
        backend_response = backend_instance.process_request(
            request=request,
            extra_data={key: value for key, value in request.data.items() if key not in serialized_data.data},
        )

        return JsonResponse(
            backend_response,
            status=backend_response.get('status', status.HTTP_202_ACCEPTED),
        )


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
