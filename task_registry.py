"""
The tasks of the chat (REQ-WFM-029, REQ-WFM-030): every skill that runs as a task has ONE id, which is also its command (`/review`), and declares its own options. The chat core knows no
skill by name: it asks this registry what a text means. A skill registers a Task, and nothing in the core changes.

  /<id> argument                              the task with its default options (the config key `skill_options` may change the defaults)
  /<id> options name[=value] ... -- argument  options for this call; the argument may contain `--` itself (only the first one separates)
  /<id> options                               lists the options of the skill with their defaults
"""
import re

KINDS = ("flag", "int", "float", "text")
TRUE, FALSE = ("true", "yes", "on", "1"), ("false", "no", "off", "0")


class TaskCommandError(ValueError):
    """a command that cannot run; the message is for the user, in plain words"""


class Option:
    def __init__(self, name, kind, default, text):
        if kind not in KINDS:
            raise ValueError("option %r: kind must be one of %s" % (name, ", ".join(KINDS)))
        self.name, self.kind, self.default, self.text = name, kind, default, text

    def convert(self, value):
        """`value` is None for a bare name"""
        try:
            if self.kind == "flag":
                if value is None or value.lower() in TRUE:
                    return True
                if value.lower() in FALSE:
                    return False
                raise ValueError
            if value is None:
                raise ValueError
            return {"int": int, "float": float, "text": str}[self.kind](value)
        except ValueError:
            raise TaskCommandError("The option %s needs %s, not %r." % (self.name, "yes or no" if self.kind == "flag" else "a value (%s)" % self.kind, value or ""))


class Task:
    def __init__(self, id, run, text, argument, example, options=(), aliases=(), needs=(), version="1"):
        """run(argument, on_delta, on_emotion, should_stop, **what it needs) -> the result text; `needs` names what the core hands over besides: "ask" (ask the user a question; a task that
        asks gives its result as the newest message), "options" (the options of this call), "monitor" (the status card: update(phase, budget, counts)),
        "files" (files(name, data) -> the stored name: puts a file into the files volume), "reports" (reports(question, report): keeps the finished report as a record)"""
        self.id, self.run, self.text, self.argument, self.example = id, run, text, argument, example
        self.options, self.aliases, self.needs, self.version = tuple(options), tuple(aliases), tuple(needs), version


class TaskRegistry:
    def __init__(self):
        self._tasks, self._names = {}, {}

    def register(self, task):
        for name in (task.id,) + task.aliases:
            if name in self._names:
                raise ValueError("The task id %r is already in use." % name)
        self._tasks[task.id] = task
        for name in (task.id,) + task.aliases:
            self._names[name] = task.id
        return task

    def ids(self):
        return list(self._tasks)

    def get(self, id):
        return self._tasks[self._names[id]]

    def commands(self):
        return [{"command": "/%s " % t.id, "description": "%s: /%s %s" % (t.text, t.id, t.argument), "confirm": False} for t in self._tasks.values()]

    def parse(self, text, defaults=None):
        """None if `text` is no task command; else {"task", "argument", "options", "help", "text"}; raises TaskCommandError for a command that cannot run"""
        names = "|".join(re.escape(n) for n in sorted(self._names, key=len, reverse=True))
        match = re.fullmatch(r"/(%s)(?:\s+(.*))?" % names, text.strip(), re.I | re.S) if names else None
        if not match:
            return None
        task = self._tasks[self._names[match.group(1).lower()]]
        rest = (match.group(2) or "").strip()
        options = {o.name: o.default for o in task.options}
        options.update({k: v for k, v in ((defaults or {}).get(task.id) or {}).items() if k in options})
        found = {"task": task.id, "argument": "", "options": options, "help": False, "text": ""}
        word = re.match(r"options(?:\s+(.*))?$", rest, re.I | re.S)
        if not word:
            if not rest:
                raise TaskCommandError("Write %s after /%s, for example: %s" % (task.argument, task.id, task.example))
            found["argument"] = rest
            return found
        if not task.options:
            raise TaskCommandError("/%s has no options." % task.id)
        given = (word.group(1) or "").strip()
        if not given:
            found.update(help=True, text=self.options_text(task))
            return found
        head, separator, argument = given.partition("--")
        if not separator or not argument.strip():
            raise TaskCommandError("Write -- and then %s after the options, for example: /%s options %s -- ..." % (task.argument, task.id, task.options[0].name))
        known = {o.name: o for o in task.options}
        for token in head.split():
            name, _, value = token.partition("=")
            if name not in known:
                raise TaskCommandError("/%s has no option %r. %s" % (task.id, name, self.options_text(task)))
            options[name] = known[name].convert(value if _ else None)
        found["argument"] = argument.strip()
        return found

    @staticmethod
    def options_text(task):
        return "Options of /%s: %s" % (task.id, "; ".join("%s (%s, default %s): %s" % (o.name, o.kind, o.default, o.text) for o in task.options))
