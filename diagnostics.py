from ear import check_microphone
from mouth import check_voice_output
from provider import validate_provider_config


def run_startup_checks() -> list[tuple[bool, str]]:
    return [
        validate_provider_config(),
        check_microphone(),
        check_voice_output(),
    ]


def format_startup_report(checks: list[tuple[bool, str]]) -> str:
    lines = ["Voss startup diagnostics:"]
    for ok, message in checks:
        status = "OK" if ok else "FAIL"
        lines.append(f"[{status}] {message}")
    return "\n".join(lines)


def all_checks_passed(checks: list[tuple[bool, str]]) -> bool:
    return all(ok for ok, _ in checks)
