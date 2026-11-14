"""Fakes for the checks of the run recorder (TR-PANEL-003, protected): the storage keeps versions, notifies subscribers and refuses a record of
skill_runs without a required field of IF-302 v8; the clock gives monotonic seconds and a UTC time string that the check sets."""
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "mocks"))

from errors import StorageError                      # noqa: E402
from if_102_storage import StorageMock               # noqa: E402
from if_302_record_tables import RecordTablesMock    # noqa: E402

DAY = datetime.datetime(2026, 11, 8, tzinfo=datetime.timezone.utc)


class FakeSkillRunStorage(StorageMock):
    """IF-102 mock with the required fields of IF-302 v8 for skill_runs, and a list of the tables that were written."""

    def __init__(self):
        super().__init__()
        self.tables_written, self._record_tables = [], RecordTablesMock()

    def put(self, table, record_id, doc, author, expected_version=None):
        if table == "skill_runs":
            broken = self._record_tables.validate(table, doc)
            if broken:
                raise StorageError("invalid", rule=broken["rule"], detail=broken["detail"])
        self.tables_written.append(table)
        return super().put(table, record_id, doc, author, expected_version)


class FakeClock:
    """`monotonic()` in seconds and `now()` as a UTC string; the check moves both with `at("10:00:05")` or `advance(seconds)`."""

    def __init__(self, time_of_day="10:00:00"):
        self._seconds = 0.0
        self._moment = None
        self.at(time_of_day)

    def at(self, time_of_day):
        hours, minutes, seconds = (int(part) for part in time_of_day.split(":"))
        moment = DAY + datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        if self._moment is not None:
            self._seconds += (moment - self._moment).total_seconds()
        self._moment = moment

    def advance(self, seconds):
        self._moment += datetime.timedelta(seconds=seconds)
        self._seconds += seconds

    def monotonic(self):
        return self._seconds

    def now(self):
        return self._moment.strftime("%Y-%m-%dT%H:%M:%SZ")
