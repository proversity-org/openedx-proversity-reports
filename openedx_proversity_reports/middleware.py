"""
Middlewares for openedx-proversity-reports.
"""
import json
from datetime import datetime, timedelta

from django.conf import settings
from openedx_proversity_reports.edxapp_wrapper.get_student_library import get_user_profile


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
            meta = json.loads(user_profile.meta)
            last_session = meta.get(self.LAST_SESSION_LABEL)
            last_session = datetime.strptime(last_session, '%Y-%m-%d %H:%M:%S.%f')
            avg_session = float(meta.get(self.AVG_SESSION_LABEL, 0))
            length_current_session = float(meta.get(self.LENGTH_CURRENT_SESSION_LABEL, 0))
            time_between_sessions = float(meta.get(self.TIME_BETWEEN_SESSIONS_LABEL, 0))
            session_number = int(meta.get(self.SESSION_NUMBER_LABEL, 0))
        except ValueError:
            meta = {}

        if not meta:
            user_profile.meta = self.get_meta_session_data(0, 0, 0, 1)
            user_profile.save()
            return None

        delta_time = datetime.now() - last_session

        if delta_time > timedelta(minutes=settings.OPR_TIME_BETWEEN_SESSIONS) and length_current_session:
            avg_session = ((avg_session * (session_number - 1)) + length_current_session) / session_number
            time_between_sessions = (
                (time_between_sessions * (session_number - 1)) + (delta_time.total_seconds() / 60)
            ) / session_number
            length_current_session = 0
            session_number += 1
        elif delta_time < timedelta(minutes=settings.OPR_TIME_BETWEEN_SESSIONS):
            length_current_session = delta_time + timedelta(minutes=length_current_session)
            length_current_session = length_current_session.total_seconds() / 60

        user_profile.meta = self.get_meta_session_data(
            avg_session,
            length_current_session,
            time_between_sessions,
            session_number
        )
        user_profile.save()

        return None

    def get_meta_session_data(self, avg_session, length_current_session, time_between_sessions, session_number):
        """
        Return a dict as string for the given arguments.".
        Args:
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
                    "length_current_session": "0.782830416667"
                }
        """
        return json.dumps({
            self.LAST_SESSION_LABEL: str(datetime.now()),
            self.AVG_SESSION_LABEL: str(avg_session),
            self.LENGTH_CURRENT_SESSION_LABEL: str(length_current_session),
            self.TIME_BETWEEN_SESSIONS_LABEL: str(time_between_sessions),
            self.SESSION_NUMBER_LABEL: str(session_number)
        })
