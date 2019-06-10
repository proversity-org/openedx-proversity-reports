"""
Time spent reports.
"""
import logging

from apiclient.discovery import build
from django.conf import settings
from django.contrib.auth.models import User
from google.oauth2 import service_account
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx_proversity_reports.edxapp_wrapper.get_course_blocks import get_course_blocks
from openedx_proversity_reports.edxapp_wrapper.get_modulestore import get_modulestore


ANALYTICS_API_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
COURSEWARE_URL_PREFIX = '/courseware'
logger = logging.getLogger(__name__)


def get_time_spent_report_data(course_list):
    """
    Generates a dict with information about course strcuture and Google Analytics data.

    Args:
        course_list: A list of valid course ids.
    Returns:
        Course structure and Google Anlytics data or an empty dict.
        {
            <course_id>: {
                course_structure: Course structure by subsection.
                analytics_data: Google Analytics data per course.
            }
        }
    """
    course_structure = {}

    for course_id in course_list:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            continue

        analytics_data = fetch_data_from_analytics(course_id)

        # If not GA data, just continue and don't fetch users or course data.
        if not analytics_data:
            course_structure[course_id] = {}
            continue

        # Getting just the first enrolled student in the course, except staff users.
        enrolled_student = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            courseaccessrole__id=None,
            is_staff=0,
        ).first()

        if not enrolled_student:
            continue

        usage_key = get_modulestore().make_course_usage_key(course_key)
        blocks = get_course_blocks(enrolled_student, usage_key)
        course_block_data = []

        course_blocks = list(blocks.topological_traversal())
        chapter_name = ''
        chapter_id = ''
        chapter_position = 0
        sequential_name = ''
        sequential_id = ''
        sequential_position = 0
        vertical_name = ''
        vertical_id = ''
        vertical_position = 0

        for block in course_blocks:
            if block.block_type == 'course':
                continue
            elif block.block_type == 'chapter':
                chapter_name = blocks.get_xblock_field(block, 'display_name')
                chapter_id = block.block_id
                sequential_position = 0
                chapter_position += 1
            elif block.block_type == 'sequential':
                sequential_name = blocks.get_xblock_field(block, 'display_name')
                sequential_id = block.block_id
                sequential_position += 1
            elif block.block_type == 'vertical':
                vertical_name = blocks.get_xblock_field(block, 'display_name')
                vertical_id = block.block_id
                # The vertical position must be only incremental.
                vertical_position += 1

                course_block_data.append({
                    'chapter_name': chapter_name,
                    'chapter_id': chapter_id,
                    'chapter_position': chapter_position,
                    'sequential_name': sequential_name,
                    'sequential_id': sequential_id,
                    'sequential_position': sequential_position,
                    'vertical_name': vertical_name,
                    'vertical_id': vertical_id,
                    'vertical_position': vertical_position,
                })

        temp_data_dict = {
            'course_structure': course_block_data,
            'analytics_data': analytics_data
        }

        course_structure[course_id] = temp_data_dict

    return course_structure


def fetch_data_from_analytics(course_id):
    """
    Returns a dict with info of Google Analytics (GA).

    Args:
        course_id: A single course id to fetch GA data only by that course.
    Returns:
        List dict containing the page urls and the required info from GA or empty list.
        [{
            page_path: Courseware url path page from GA
            page_views: Number of url path oage views.
            avg_time_on_page: Average of time on url path page.
        }]
    """

    def initialize_analytics_reporting():
        """
        Initializes an Analytics Reporting API V4 service object.

        Returns:
            An authorized Analytics Reporting API V4 service object.
        """
        ga_credentials = getattr(settings, 'OPR_GOOGLE_ANALYTICS_CREDENTIALS', None)

        if not ga_credentials:
            logger.error('Google Analytics credentials were not provided.')
            raise GoogleAnalyticsCredentialsError('Google Analytics credentials were not provided.')

        credentials = service_account.Credentials.from_service_account_info(
            ga_credentials, scopes=ANALYTICS_API_SCOPES
        )

        # Build the service object.
        analytics = build('analyticsreporting', 'v4', credentials=credentials, cache_discovery=False)

        return analytics


    def get_analytics_report(analytics):
        """
        Queries the Analytics Reporting API V4.

        Args:
            analytics: An authorized Analytics Reporting API V4 service object.
        Returns:
            The Analytics Reporting API V4 response or None if analytics view id is not provided.
        """
        course_expression = '{}{}'.format(course_id, COURSEWARE_URL_PREFIX)
        analytics_view_id = getattr(settings, 'OPR_GOOGLE_ANALYTICS_VIEW_ID', None)

        if not analytics_view_id:
            logger.error('Google Analytics view id has not been provided.')
            raise GoogleAnalyticsCredentialsError('Google Analytics view id has not been provided.')

        return analytics.reports().batchGet(
            body={
                'reportRequests': [{
                    'viewId': analytics_view_id,
                    'dateRanges': [
                        {'startDate': '30DaysAgo', 'endDate': 'today'},
                    ],
                    'metrics': [
                        {'expression': 'ga:pageviews'},
                        {'expression': 'ga:avgTimeOnPage'},
                    ],
                    'dimensions': [{'name': 'ga:pagePath'}],
                    "dimensionFilterClauses": [{
                        "filters": [{
                            "dimensionName": 'ga:pagePath',
                            "not": False,
                            "operator": 'PARTIAL',
                            "expressions": [
                                course_expression,
                            ],
                            "caseSensitive": False
                        }]
                    }]
                }]
            }
        ).execute()


    def parse_response(response):
        """
        Parses the Analytics Reporting API V4 response.

        Args:
            response: An Analytics Reporting API V4 response.
        """
        data = []
        for report in response.get('reports', []):
            for row in report.get('data', {}).get('rows', []):
                dimensions = row.get('dimensions', [])
                metric_values = row.get('metrics', [])
                try:
                    # Only take the first list value, since only one date range is requested.
                    dimension_values = metric_values[0].get('values', [])

                    if dimension_values:
                        # dimensions[0], since only one dimension is requested.
                        # dimension_values[0], it's the ga:pageviews number.
                        # dimension_values[1], it's the ga:avgTimeOnPage time number in seconds.
                        data.append({
                            'page_path': dimensions[0],
                            'page_views': dimension_values[0],
                            'avg_time_on_page': dimension_values[1],
                        })
                except IndexError:
                    logger.error('Google Analytics API response format error.')
                    raise GoogleAnalyticsResponseError('Google Analytics API response format error.')

        return data

    analytics_service = initialize_analytics_reporting()
    analytics_response = get_analytics_report(analytics_service)
    analytics_data_per_dimension = parse_response(analytics_response)

    return analytics_data_per_dimension or []


class GoogleAnalyticsCredentialsError(Exception):
    """
    Exception class raised when some of the required credentials,
    by Google Analytics were not provided.
    """
    pass


class GoogleAnalyticsResponseError(Exception):
    """
    Exception class raised when the API response does not have
    an expected format by the data generation.
    """
    pass
