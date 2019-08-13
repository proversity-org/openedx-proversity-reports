""" Backend abstraction. """
from lms.djangoapps.student_account.models import UserSalesforceContactId


def user_salesforce_contact_id(*args, **kwargs):
    """ Returns UserSalesforceContactId model. """
    return UserSalesforceContactId
