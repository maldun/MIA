"""
The gate before a task (REQ-WFM-035): a model that is new and does not run on this machine is asked about once whether it is paid; a paid model gives a warning and the option `slice` as its
default (a task whose skill has that option); the class is changed only by the user's command `/model paid <name>` or `/model local <name>`. The chat core calls make_prepare()'s function before
every task and make_model_command()'s function for `/model`; it knows nothing else about models or money.
"""


def make_prepare(classes, model, host, note):
    """model() and host() say which model answers and where it runs; note(text) puts a note in the chat"""
    def prepare(task, options, ask):
        name, where = model(), host()
        paid = classes.class_of(name, where) == "paid"
        if classes.needs_question(name, where):
            reply = (ask("Is the model %s a paid (commercial) model? Answer yes or no. I ask only once for each model; "
                         "/model paid <name> or /model local <name> changes it later." % name) or "").strip().lower()
            if reply.startswith("n"):
                classes.set(name, "local")
            else:
                paid = True
                if reply.startswith("y"):
                    classes.set(name, "paid")                      # no answer is not stored: the next task asks again
        options = dict(options)
        if paid:
            note("Warning: %s is a paid model. A long task can cost money, so I work in slices and ask at each limit." % name)
            if any(o.name == "slice" for o in task.options):
                options["slice"] = True
        return options
    return prepare


def make_model_command(classes, model, host):
    def command(argument):
        words = argument.split()
        if not words:
            name = model()
            return "The model %s is treated as %s (%s)." % (name, classes.class_of(name, host()) or "unknown", "/model paid <name> or /model local <name> changes it")
        if len(words) != 2 or words[0] not in ("paid", "local"):
            raise ValueError("Use /model paid <name> or /model local <name>.")
        classes.set(words[1], words[0])
        return "The model %s is now treated as %s." % (words[1], words[0])
    return command
