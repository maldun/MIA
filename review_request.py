"""
The intake of a literature review (ui/REQUIREMENTS_RESEARCH.md R0, RV4, RV30): the question, the date up to which literature may be used, and the hard limits
of the run. Nothing here calls a model or the internet.

  B1  every run has limits set before it starts (sources screened, sources read, model calls, tokens, seconds, API requests); spend() refuses what would cross a limit
      instead of letting it happen, and the first refusal is remembered (hit) so that the report can say which limit ended the stage
  B2  every K sources checked (checkpoint_every) the run stops for an intermediate report and the user decides whether to continue; a stage never continues by itself
  B2a time comes in slices (RV30a): the first is one minute; continue_run() adds one more (or a length the user names) and renews every limit that was used up by its first size; the
      intermediate report carries a recommendation made by code from what the last slice achieved (recommend())
  B3  the cut-off defaults to today; a date in the future is refused (it would allow nothing more than today and hides a typo)
  B4  the number of domain experts is a setting of the request (RV44): 0 = none (the fixed roles and one generalist judgement), 1 = the main field, k = the main field and the k-1 most
      relevant related fields; the fixed roles (planner, collector, source expert) do not depend on it; role_models says which role runs on a model of its own (default: all on the same one)
"""
import datetime
import time

LIMITS = ("screen", "read", "calls", "tokens", "seconds", "api_requests")
FIXED_ROLES = ("planner", "collector", "source_expert")
DEFAULT_DOMAIN_EXPERTS = 3
MAX_DOMAIN_EXPERTS = 10
# the first slice of a review is one minute (RV30a); "continue" adds another one, so seconds is the size of a slice, the other limits are ceilings that grow only when they were used up
DEFAULT_BUDGET = {"screen": 40, "read": 10, "calls": 150, "tokens": 400000, "seconds": 60, "api_requests": 80, "checkpoint_every": 10}


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
        self.initial = dict(merged)
        self.extensions = []
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

    def extend(self, name, amount=None):
        """RV30a: raise one limit by `amount` (default: its first size) and forget that it was hit; returns the new limit"""
        if name not in LIMITS:
            raise RequestError("unknown limit %r" % name)
        amount = self.initial[name] if amount is None else amount
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 1:
            raise RequestError("a limit grows by a number of at least 1, not %r" % (amount,))
        self.limits[name] += amount
        self.extensions.append({"name": name, "amount": amount, "at_seconds": round(self.elapsed(), 1)})
        if self.hit == name:
            self.hit = None
        return self.limits[name]

    def continue_run(self, seconds=None):
        """the user said continue: one more slice of time (`seconds`, default the first size) and every other limit that was used up grows by its first size"""
        grown = {"seconds": self.extend("seconds", seconds)}
        for name in LIMITS:
            if name != "seconds" and self.remaining(name) <= 0:
                grown[name] = self.extend(name)
        self.hit = None
        return grown

    def slices(self):
        """how many slices of time have been granted so far (the first one included)"""
        return 1 + sum(1 for e in self.extensions if e["name"] == "seconds")

    def state(self):
        return {"limits": dict(self.limits), "used": {**self.used, "seconds": round(self.elapsed(), 1)}, "hit": self.hit, "sources_checked": self.sources_checked,
                "slices": self.slices(), "extensions": list(self.extensions)}


class ReviewRequest:
    def __init__(self, question, until=None, since=None, languages=None, fields=None, budget=None, include_transfer=False, today=None, clock=time.monotonic,
                 domain_experts=DEFAULT_DOMAIN_EXPERTS, expert_fields=None, role_models=None):
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
        if isinstance(domain_experts, bool) or not isinstance(domain_experts, int) or not 0 <= domain_experts <= MAX_DOMAIN_EXPERTS:
            raise RequestError("domain_experts must be a whole number from 0 to %d, not %r" % (MAX_DOMAIN_EXPERTS, domain_experts))
        self.domain_experts = domain_experts
        self.expert_fields = [str(f) for f in (expert_fields or [])]
        if len(self.expert_fields) > domain_experts:
            raise RequestError("%d fields are named for the experts, but domain_experts is %d" % (len(self.expert_fields), domain_experts))
        self.role_models = {}
        for role, model in (role_models or {}).items():
            if role not in FIXED_ROLES + ("domain",):
                raise RequestError("unknown role %r in role_models (known: %s, domain)" % (role, ", ".join(FIXED_ROLES)))
            if model:
                self.role_models[role] = str(model)

    @classmethod
    def from_config(cls, question, cfg=None, **kwargs):
        """limits from the option review_budget, the rest from the arguments"""
        cfg = cfg or {}
        kwargs.setdefault("domain_experts", cfg.get("review_domain_experts", DEFAULT_DOMAIN_EXPERTS))
        kwargs.setdefault("role_models", cfg.get("review_role_models"))
        return cls(question, budget=Budget(cfg.get("review_budget"), clock=kwargs.pop("clock", time.monotonic)), **kwargs)

    def roles(self):
        """who takes part (RV44): the fixed roles, how many domain experts and for which fields (empty: chosen by relevance from the field graph), and the model of each role (None: the common one)"""
        models = {role: self.role_models.get(role) for role in FIXED_ROLES + ("domain",)}
        return {"fixed": list(FIXED_ROLES), "domain_experts": self.domain_experts, "expert_fields": list(self.expert_fields), "models": models,
                "generalist": self.domain_experts == 0}

    def as_of_today(self):
        return self.until >= self.today

    def to_dict(self):
        return {"question": self.question, "until": self.until.isoformat(), "since": self.since.isoformat() if self.since else None, "languages": self.languages,
                "fields": self.fields, "include_transfer": self.include_transfer, "budget": self.budget.state(), "as_of_today": self.as_of_today(), "roles": self.roles()}


def recommend(progress, sufficient=False, open_items=0):
    """RV30a: the advice at the end of a slice, from what the last slice achieved. progress: {"new_sources": n, "new_findings": n, "closed_slots": n} (kept sources, anchored findings,
    slots closed in the slice); sufficient: the sufficiency check of RV19a holds; open_items: open slots and unanswered sub-questions. Returns {"action": "stop" | "continue", "why": text}.
    The rule is simple and visible on purpose: the direction is clear -> stop; progress and gaps -> continue; no progress -> stop or change the keywords."""
    made = sum(int(progress.get(k, 0)) for k in ("new_sources", "new_findings", "closed_slots"))
    if sufficient:
        return {"action": "stop", "why": "the direction is clear: every sub-question has anchored findings of enough weight"}
    if made == 0:
        return {"action": "stop", "why": "the last slice brought nothing new%s: continue only with other keywords or another field" % (", and %d item(s) are still open" % open_items if open_items else "")}
    if open_items == 0:
        return {"action": "stop", "why": "the last slice brought %d new item(s) and nothing is open" % made}
    return {"action": "continue", "why": "the last slice brought %d new item(s) and %d item(s) are still open" % (made, open_items)}


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
