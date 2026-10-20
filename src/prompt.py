"""Single source of truth for the prompt. Training, prediction, baselines and Phase B all import this."""

SYSTEM_PROMPT = ("You are a log parser. Replace every variable in the log message "
                 "with <*>. Output only the template.")


def user_prompt(system, content, system_line=True):
    return f"System: {system}\nLog: {content}" if system_line else f"Log: {content}"


def prompt_messages(system, content, examples=(), system_line=True):
    """`examples` are (system, content, template) triples inserted as earlier chat turns (few-shot)."""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for s, c, t in examples:
        msgs += [{"role": "user", "content": user_prompt(s, c, system_line)}, {"role": "assistant", "content": t}]
    return msgs + [{"role": "user", "content": user_prompt(system, content, system_line)}]


def to_example(system, content, template):
    return {"messages": prompt_messages(system, content) + [{"role": "assistant", "content": template}]}