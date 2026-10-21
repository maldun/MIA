"""
The intake of a literature review (ui/REQUIREMENTS_RESEARCH.md R0, RV4, RV30): the question, the date up to which literature may be used, and the hard limits
of the run. Nothing here calls a model or the internet.

  B1  every run has limits set before it starts (sources screened, sources read, model calls, tokens, seconds, API requests); spend() refuses what would cross a limit
      instead of letting it happen, and the first refusal is remembered (hit) so that the report can say which limit ended the stage
  B2  every K sources checked (checkpoint_every) the run stops for an intermediate report and the user decides whether to continue; a stage never continues by itself
  B3  the cut-off defaults to today; a date in the future is refused (it would allow nothing more than today and hides a typo)
"""
import datetime
import time

LIMITS = ("screen", "read", "calls", "tokens", "seconds", "api_requests")
DEFAULT_BUDGET = {"screen": 40, "read": 10, "calls": 150, "tokens": 400000, "seconds": 1800, "api_requests": 80, "checkpoint_every": 10}


class RequestError(ValueError):
    pass


class Budget:
    """limits and what is used; seconds are measured from start() by the clock"""

    def __init__(self, limits=None, clock=time.monotonic):
        merged = dict(DEFAULT_BUDGET)
        for key, value in (limits or {}).items():
            if key not in merged:
                raise RequestError("unknown limit %r (known: %s)" % (key, ", ".join(sorted(merged))))
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 1:
                raise RequestError("limit %r must be a number of at least 1, not %r" % (key, value))
            merged[key] = value
        self.limits = merged
        self.used = {name: 0 for name in LIMITS}
        self.hit = None
        self._clock, self._started = clock, None
        self.sources_checked = 0

    def start(self):
        self._started = self._clock()

    def elapsed(self):
        return 0.0 if self._started is None else self._clock() - self._started

    def _used(self, name):
        return self.elapsed() if name == "seconds" else self.used[name]

    def remaining(self, name):
        return max(0, self.limits[name] - self._used(name))

    def spend(self, name, amount=1):
        """True and counted if it fits; False (and nothing counted) if it would cross the limit"""
        if name not in LIMITS or name == "seconds":
            raise RequestError("cannot spend %r" % name)
        if self._used(name) + amount > self.limits[name]:
            self.hit = self.hit or name
            return False
        self.used[name] += amount
        return True

    def exhausted(self):
        """the name of the first limit that is used up (seconds included), else None"""
        for name in LIMITS:
            if self.remaining(name) <= 0:
                self.hit = self.hit or name
                return name
        return None

    def checkpoint_due(self):
        """B2: true when another checkpoint_every sources have been checked since the last checkpoint"""
        every = int(self.limits["checkpoint_every"])
        return self.sources_checked > 0 and self.sources_checked % every == 0

    def note_source_checked(self):
        self.sources_checked += 1
        return self.checkpoint_due()

    def state(self):
        return {"limits": dict(self.limits), "used": {**self.used, "seconds": round(self.elapsed(), 1)}, "hit": self.hit, "sources_checked": self.sources_checked}


class ReviewRequest:
    def __init__(self, question, until=None, since=None, languages=None, fields=None, budget=None, include_transfer=False, today=None, clock=time.monotonic):
        self.today = today or datetime.date.today()
        self.question = " ".join(str(question or "").split())
        if len(self.question) < 8:
            raise RequestError("the research question is missing or too short")
        if len(self.question) > 1000:
            raise RequestError("the research question is longer than 1000 characters; state it shorter and give the rest as scope")
        self.until = _date(until, "until") or self.today
        self.since = _date(since, "since")
        if self.until > self.today:
            raise RequestError("the cut-off %s is in the future (today is %s)" % (self.until, self.today))
        if self.since and self.since > self.until:
            raise RequestError("'since' %s is after the cut-off %s" % (self.since, self.until))
        self.languages = [str(l).lower() for l in (languages or ["en"])]
        self.fields = [str(f) for f in (fields or [])]
        self.budget = budget if isinstance(budget, Budget) else Budget(budget, clock=clock)
        self.include_transfer = bool(include_transfer)          # RV48: methods from other fields, only on request

    @classmethod
    def from_config(cls, question, cfg=None, **kwargs):
        """limits from the option review_budget, the rest from the arguments"""
        return cls(question, budget=Budget((cfg or {}).get("review_budget"), clock=kwargs.pop("clock", time.monotonic)), **kwargs)

    def as_of_today(self):
        return self.until >= self.today

    def to_dict(self):
        return {"question": self.question, "until": self.until.isoformat(), "since": self.since.isoformat() if self.since else None, "languages": self.languages,
                "fields": self.fields, "include_transfer": self.include_transfer, "budget": self.budget.state(), "as_of_today": self.as_of_today()}


def _date(value, name):
    if value in (None, ""):
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value).strip())
    except ValueError:
        raise RequestError("%s must be a date like 2010-06-30, not %r" % (name, value))
