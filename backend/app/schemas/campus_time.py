"""Campus clock handling.

The database runs on campus time (Asia/Kolkata, see docker-compose.yml) and its
TIMESTAMP columns are timezone-less. Sent to a browser as a bare string, JavaScript
would read them in the *viewer's* zone and show the wrong time. Tagging them with the
campus UTC offset (+05:30, India has no DST) makes every client convert correctly.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

from pydantic import AfterValidator

CAMPUS_TZ = timezone(timedelta(hours=5, minutes=30), name="IST")


def _tag_campus(value: datetime) -> datetime:
    return value.replace(tzinfo=CAMPUS_TZ) if value.tzinfo is None else value


CampusDateTime = Annotated[datetime, AfterValidator(_tag_campus)]
