"""
This module contains some Google BigQuery API abstract functions.
"""
import logging

from django.conf import settings
from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery
from google.cloud.bigquery.client import Client
from google.oauth2 import service_account

BIGQUERY_API_SCOPES = (
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/bigquery.readonly',
)
CCX_CANONICAL_NAMESPACE = 'ccx-v1'
logger = logging.getLogger(__name__)


def get_google_bigquery_data(query_string):
    """
    Return the Google BigQuery data.

    Return:
        google.cloud.bigquery.job.QueryJob.result() instance.
    """
    bigquery_client = get_google_bigquery_api_client()
    query_job = bigquery_client.query(
        query_string,
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


def get_google_bigquery_course_id(course_key):
    """
    Return the course id as it is used in Google Big Query for the dataset name.
    Get the deprecated course key string and then replaces the fordward slash characters '/'
    with underscore characters '_' e.g. course-v1:edX+DemoX+Demo_Course -> edX-DemoX-Demo_Course
    """
    if course_key.CANONICAL_NAMESPACE == CCX_CANONICAL_NAMESPACE:
        deprecated_course_key = to_ccx_string(course_key)
    else:
        deprecated_course_key = course_key._to_deprecated_string()  # pylint: disable=protected-access

    return replace_course_id_characters(deprecated_course_key)


def to_ccx_string(course_key):
    """
    Returns a forward slash style CCX course id string similar to a deprecated course id style.
    This function is required because the _to_deprecated_string method in the CCXLocator class
    is not implemented because the CCX course keys are not supposed to have a deprecated value.

    e.g. ccx-v1:edX+DemoX.1+2014+ccx@10 -> edX/DemoX.1/2014/10

    Args:
        course_key: opaque_keys.edx.keys.CourseKey instance.
    Returns:
        CCX course id string.
    """
    return '{org}/{course_number}/{course_run}/{ccx_id}'.format(
        org=course_key.org,
        course_number=course_key.course,
        course_run=course_key.run,
        ccx_id=course_key.ccx,
    )


def replace_course_id_characters(course_id):
    """
    Replace some characters in the given course id value.

    These characters ('/', '.', '-') are replaced with '_' to avoid problems with
    the Google BigQuery name notation.

    Args:
        course_id: Course id value string.
    Returns:
        course_id: Replaced course id value.
    """
    for character in ['/', '.', '-']:
        if character in course_id:
            course_id = course_id.replace(character, '_')

    return course_id


class GoogleBigQueryInformationError(Exception):
    """
    Exception class raised when some of the required information
    by Google BigQuery were not provided.
    """
    pass
