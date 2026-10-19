"""Single source of truth for the prompt. Training, prediction, baselines and Phase B all import this."""

SYSTEM_PROMPT = ("You are a log parser. Replace every variable in the log message "
                 "with <*>. Output only the template.")


def user_prompt(system, content):
    return f"System: {system}\nLog: {content}"


def prompt_messages(system, content):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt(system, content)},
    ]


def to_example(system, content, template):
    return {"messages": prompt_messages(system, content) + [{"role": "assistant", "content": template}]}