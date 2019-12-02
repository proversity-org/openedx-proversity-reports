"""
Module containing the Time spent per user report.
"""
import logging

from django.conf import settings
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery
from google.cloud.bigquery.client import Client
from google.oauth2 import service_account

from openedx_proversity_reports.edxapp_wrapper.get_block_structure_library import get_course_in_cache
from openedx_proversity_reports.edxapp_wrapper.get_course_cohort import get_course_cohort
from openedx_proversity_reports.edxapp_wrapper.get_course_teams import get_course_teams
from openedx_proversity_reports.edxapp_wrapper.get_modulestore import item_not_found_error


BIGQUERY_API_SCOPES = (
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/bigquery.readonly',
)
logger = logging.getLogger(__name__)


class GenerateTimeSpentPerUserReport(object):
    """
    Class to generate the time spent per user report.
    """

    def __init__(self, users, course_key, query_date):
        self.users = users
        self.course_key = course_key
        self.course_block_structure = None
        self.course_blocks = self.get_course_blocks()
        self.query_date = query_date

    def get_course_blocks(self):
        """
        Return the course blocks filtered by block_type_filter().

        Returns:
            openedx.core.djangoapps.content.block_structure.block_structure.BlockStructure.topological_traversal instance.
        """
        try:
            course_block_structure = get_course_in_cache(self.course_key)
        except item_not_found_error():
            return []

        course_component_blocks = course_block_structure.topological_traversal(
            filter_func=block_type_filter,
            yield_descendants_of_unyielded=True,
        )
        self.course_block_structure = course_block_structure

        return course_component_blocks

    def get_google_bigquery_course_id(self):
        """
        Return the course id as it is used in Google Big Query for the dataset name.
        Get the deprecated course key string and then replaces the fordward slash characters '/'
        with underscore characters '_' e.g. course-v1:edX+DemoX+Demo_Course -> edX-DemoX-Demo_Course
        """
        deprecated_course_key = self.course_key._to_deprecated_string()  # pylint: disable=protected-access

        return deprecated_course_key.replace('/', '_')

    def get_google_bigquery_data(self):
        """
        Return the Google BigQuery data.

        Return:
            google.cloud.bigquery.job.QueryJob.result() instance.
        """
        bigquery_client = get_google_bigquery_api_client()
        query_job = bigquery_client.query(
            get_google_bigquery_query(
                course_dataset_name=self.get_google_bigquery_course_id(),
                date=self.query_date,
                course_id=str(self.course_key),
            ),
            job_config=get_google_bigquery_job_config(),
        )

        try:
            query_job.exception()
        except GoogleAPIError as api_error:
            for error_item in api_error.errors:
                logger.error('Google BigQuery API error: %s', error_item.get('message', ''))
                return []

        if query_job.errors:
            for error_item in query_job.errors:
                logger.error('Google BigQuery query error: %s', error_item.get('message', ''))
                return []

        return query_job.result()

    def generate_report_data(self):
        """
        Return the time spent per user report data.
        """
        if not (self.course_block_structure or self.course_blocks):
            return []

        time_on_asset_column_name = getattr(
            settings,
            'OPR_GOOGLE_BIGQUERY_TIME_ON_ASSET_DAILY_COLUMN_NAME',
            '',
        )
        bigquery_data = list(self.get_google_bigquery_data())

        if not bigquery_data:
            return []

        course_blocks = list(self.course_blocks)
        user_data = []

        for user in self.users:
            user_course_cohort = get_course_cohort(user=user, course_key=self.course_key)
            user_course_teams = get_course_teams(membership__user=user, course_id=self.course_key)
            block_data = []
            chapter_name = ''
            chapter_position = 0
            sequential_name = ''
            sequential_position = 0
            vertical_name = ''
            vertical_position = 0

            for course_block in course_blocks:
                bigquery_item = {}

                for item_data in bigquery_data:
                    if (item_data.get('username', '') == user.username and
                            course_block.block_id in item_data.get('module_id', '')):
                        bigquery_item = item_data
                        break

                if course_block.block_type == 'chapter':
                    chapter_name = self.course_block_structure.get_xblock_field(
                        course_block,
                        'display_name',
                    ) or ''
                    sequential_position = 0
                    chapter_position += 1
                elif course_block.block_type == 'sequential':
                    sequential_name = self.course_block_structure.get_xblock_field(
                        course_block,
                        'display_name',
                    ) or ''
                    sequential_position += 1
                elif course_block.block_type == 'vertical':
                    vertical_name = self.course_block_structure.get_xblock_field(
                        course_block,
                        'display_name',
                    ) or ''
                    # The vertical position must be only incremental.
                    vertical_position += 1

                    block_data.append({
                        'average_time_spent': bigquery_item.get(
                            time_on_asset_column_name,
                            0,
                        ) if bigquery_item else 0,
                        'chapter_name': chapter_name,
                        'chapter_position': chapter_position,
                        'sequential_name': sequential_name,
                        'sequential_position': sequential_position,
                        'vertical_name': vertical_name,
                        'vertical_position': vertical_position,
                    })

            user_data.append({
                'username': user.username,
                'user_cohort': user_course_cohort.name if user_course_cohort else '',
                'user_teams': user_course_teams[0].name if user_course_teams else '',
                'blocks': block_data,
            })

        return user_data


def get_google_bigquery_api_client():
    """
    Return the Google BigQuery API client.

    Returns:
        google_bigquery_client: google.cloud.bigquery.client.Client instance.
    """
    service_account_credentials = getattr(settings, 'OPR_GOOGLE_SERVICE_ACCOUNT_CREDENTIALS', {})
    google_project_id = getattr(settings, 'OPR_GOOGLE_CLOUD_PROJECT_ID', '')

    if not (service_account_credentials or google_project_id):
        logger.error('Google Service Account credentials or porject ID were not provided.')
        raise GoogleBigQueryInformationError('Google Service Account credentials or porject ID were not provided.')

    credentials = service_account.Credentials.from_service_account_info(
        service_account_credentials,
        scopes=BIGQUERY_API_SCOPES,
    )

    return Client(
        project=google_project_id,
        credentials=credentials,
    )


def block_type_filter(block_item):
    """
    Return True if the block type exists in block_type_whitelist otherwise False.
    This functionallity is to get only the required block types and discard the other block types.

    Args:
        block_item: Course block item to be matched.
    """
    block_type_whitelist = (
        'chapter',
        'sequential',
        'vertical',
    )

    return block_item.block_type in block_type_whitelist


def get_google_bigquery_job_config():
    """
    Return the Google BigQuery job configuration.

    Returns:
        job_config: google.cloud.bigquery.job.QueryJobConfig instance.
    """
    job_config = bigquery.QueryJobConfig()
    job_config.maximum_bytes_billed = getattr(settings, 'OPR_GOOGLE_BIGQUERY_MAX_PROCESS_BYTES', None)
    job_config.use_query_cache = getattr(settings, 'OPR_GOOGLE_BIGQUERY_USE_CACHE', False)

    return job_config


def get_google_bigquery_query(course_dataset_name, date, course_id):
    """
    Return the Google BigQuery query for the time_on_asset_daily table.

    Args:
        course_dataset_name: Dataset name where the table is stored.
        date: Date to filter the query. Date format: '%Y-%m-%d' e.g. '2019-01-01'
        course_id: Course id string.
    Returns:
        query_string: The query string to make the query.
    Raises:
        GoogleBigQueryInformationError: If OPR_GOOGLE_CLOUD_PROJECT_ID or course_dataset_name
                                        were not provided or are None.
    """
    google_project_id = getattr(settings, 'OPR_GOOGLE_CLOUD_PROJECT_ID', '')
    query_max_result_number = getattr(settings, 'OPR_GOOGLE_BIGQUERY_MAX_NUMBER_RESULTS_PER_QUERY', 1000)

    if not (google_project_id or course_dataset_name):
        raise GoogleBigQueryInformationError('Google cloud project id or course_dataset_name are missing.')

    query_string = """
        SELECT course_id, username, module_id, time_umid5, time_umid30
        FROM `{google_project_id}.{bigquery_dataset}.time_on_asset_daily`
        WHERE module_id LIKE '%vertical%'
        AND course_id = '{course_id}'
        AND time_umid5 IS NOT NULL
        AND time_umid30 IS NOT NULL
        AND PARSE_DATETIME('%Y-%m-%d', date) = '{query_date}' LIMIT {max_result_number}
    """.format(
        google_project_id=google_project_id,
        bigquery_dataset=course_dataset_name,
        course_id=course_id,
        query_date=date,
        max_result_number=query_max_result_number,
    )

    return query_string


class GoogleBigQueryInformationError(Exception):
    """
    Exception class raised when some of the required information
    by Google BigQuery were not provided.
    """
    pass
