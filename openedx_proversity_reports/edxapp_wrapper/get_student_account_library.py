""" Backend abstraction. """
from importlib import import_module
from django.conf import settings


def get_user_salesforce_contact_id():
    """ Get UserSalesforceContactId model. """

    backend_function = settings.OPR_STUDENT_ACCOUNT_LIBRARY
    backend = import_module(backend_function)

    return backend.user_salesforce_contact_id()
