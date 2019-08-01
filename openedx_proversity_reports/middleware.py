"""
Middlewares for openedx-proversity-reports.
"""
import json
from datetime import datetime, timedelta

from django.conf import settings
from openedx_proversity_reports.edxapp_wrapper.get_student_library import get_user_profile
from openedx_proversity_reports.serializers import UserSessionSerializer


class UserSessionMiddleware(object):
    """
    Middleware to store session data.
    """
    AVG_SESSION_LABEL = 'avg_session'
    LAST_SESSION_LABEL = 'last_session'
    LENGTH_CURRENT_SESSION_LABEL = 'length_current_session'
    SESSION_NUMBER_LABEL = 'session_number'
    TIME_BETWEEN_SESSIONS_LABEL = 'time_between_sessions'

    def process_request(self, request):
        """
        This middleware stores the session date and calculates the
        average session time, average time between sessions and current length
        session for every authenticated user.
        """
        user = request.user

        if user.is_anonymous():
            return None

        user_profile = get_user_profile().objects.get(user_id=user.id)

        try:
            meta_as_dict = json.loads(user_profile.meta)
            serializer = UserSessionSerializer(data=meta_as_dict)
            session_data = serializer.validated_data if serializer.is_valid() else {}
        except ValueError:
            session_data = {}
            meta_as_dict = {'previous_data': user_profile.meta}

        if not session_data:
            user_profile.meta = self.get_meta_session_data(
                previous_data=meta_as_dict,
                avg_session=0,
                length_current_session=0,
                time_between_sessions=0,
                session_number=1,
            )
            user_profile.save()
            return None

        last_session = session_data.get(self.LAST_SESSION_LABEL, datetime.now())
        avg_session = session_data.get(self.AVG_SESSION_LABEL, 0)
        length_current_session = session_data.get(self.LENGTH_CURRENT_SESSION_LABEL, 0)
        time_between_sessions = session_data.get(self.TIME_BETWEEN_SESSIONS_LABEL, 0)
        session_number = session_data.get(self.SESSION_NUMBER_LABEL, 0)
        delta_time = datetime.now(last_session.tzinfo) - last_session

        if delta_time > timedelta(minutes=settings.OPR_TIME_BETWEEN_SESSIONS) and length_current_session:
            avg_session = self.calculate_average_value(avg_session, session_number, length_current_session)
            time_between_sessions = self.calculate_average_value(
                time_between_sessions,
                session_number,
                (delta_time.total_seconds() / 60),
            )
            length_current_session = 0
            session_number += 1
        elif delta_time < timedelta(minutes=settings.OPR_TIME_BETWEEN_SESSIONS):
            length_current_session = delta_time + timedelta(minutes=length_current_session)
            length_current_session = length_current_session.total_seconds() / 60

        user_profile.meta = self.get_meta_session_data(
            meta_as_dict,
            avg_session,
            length_current_session,
            time_between_sessions,
            session_number,
        )

        user_profile.save()

        return None

    def get_meta_session_data(
        self,
        previous_data,
        avg_session,
        length_current_session,
        time_between_sessions,
        session_number,
    ):
        """
        Return a dict as string for the given arguments.
        Args:
            previous_data: Dict.
            avg_session: Float.
            length_current_session: Float.
            time_between_sessions. Float.
            session_number: Int.
        Returns:
            String:
            **Example:
                {
                    "last_session": "2019-07-31 13:03:22.270898",
                    "session_number": "1",
                    "time_between_sessions": "0.0",
                    "avg_session": "0.0",
                    "length_current_session": "0.782830416667",
                    ...
                    ...
                    ...
                }
        """
        serializer = UserSessionSerializer(data={
            self.LAST_SESSION_LABEL: datetime.now(),
            self.AVG_SESSION_LABEL: avg_session,
            self.LENGTH_CURRENT_SESSION_LABEL: length_current_session,
            self.TIME_BETWEEN_SESSIONS_LABEL: time_between_sessions,
            self.SESSION_NUMBER_LABEL: session_number,
        })

        if serializer.is_valid():
            previous_data.update(serializer.data)

        return json.dumps(previous_data)

    def calculate_average_value(self, previous_avg, data_number, new_data):
        """
        This calculates the average value for the given values using the following formula.

                      (previous_avg * (data_number - 1 )) + new_data
        average =    ------------------------------------------------
                                    data_number

        Args:
            previous_avg: (Float) The average for the data set number minus 1.
            data_number: (Int) Data set number.
            new_data: (Float) Value for the last data.

        Returns:
            Float: Average value.
        """
        return ((previous_avg * (data_number - 1)) + new_data) / data_number
