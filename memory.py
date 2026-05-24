from pathlib import Path


conversation_history = []


def add_to_history(role: str, content: str):
    conversation_history.append({"role": role, "content": content})


def get_history():
    return conversation_history


def update_living_context(new_information: str):
    living_context_path = Path(__file__).with_name("living_context.txt")
    with living_context_path.open("a", encoding="utf-8") as file:
        file.write(f"\n{new_information.strip()}\n")


def clear_history():
    conversation_history.clear()
