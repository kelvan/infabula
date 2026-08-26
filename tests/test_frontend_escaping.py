"""Guards the stored-XSS fix in the frontend.

Entry `meta` is arbitrary client JSON that gets interpolated into HTML
attributes in the edit modal. It escaped cleanly once; this makes sure
it keeps doing so. Runs the real `esc()` out of app.js under node, so
the test breaks if that function or its callers regress.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

APP_JS = Path(__file__).resolve().parent.parent / "static" / "app.js"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node not available"
)

PAYLOADS = [
    '" autofocus onfocus=alert(1) x="',
    "<script>alert(1)</script>",
    "' onmouseover='alert(1)",
    '"><img src=x onerror=alert(1)>',
]


def run_in_node(script: str) -> str:
    """Evaluate a snippet with app.js's helpers in scope.

    app.js runs top-level side effects (it expects a DOM), so only the
    function under test is lifted out rather than loading the whole file.
    """
    source = APP_JS.read_text()
    start = source.index("function esc(s)")
    end = source.index("\n", start)
    esc_fn = source[start:end]
    completed = subprocess.run(
        ["node", "-e", f"{esc_fn}\n{script}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


@pytest.mark.parametrize("payload", PAYLOADS)
def test_esc_neutralises_attribute_breakouts(payload):
    out = run_in_node(f"console.log(esc({json.dumps(payload)}))")
    for dangerous in ('"', "<", ">", "'"):
        assert dangerous not in out, f"{dangerous!r} survived escaping: {out}"


def test_esc_handles_non_strings():
    """meta values arrive as whatever JSON held — numbers, null, missing."""
    assert run_in_node("console.log(esc(null))") == ""
    assert run_in_node("console.log(esc(undefined))") == ""
    assert run_in_node("console.log(esc(120))") == "120"


def test_no_meta_value_reaches_an_attribute_unescaped():
    """The regression itself: `value="${m.amount}"` and friends.

    Checks every line that drops a `m.<field>` into an HTML attribute,
    rather than naming the three that were wrong once — a new one added
    later is caught the same way.
    """
    offenders = []
    for number, line in enumerate(APP_JS.read_text().splitlines(), start=1):
        if 'value="${' not in line or "m." not in line:
            continue
        for fragment in line.split('value="${')[1:]:
            expression = fragment.split("}")[0]
            if "m." in expression and "esc(" not in expression:
                offenders.append(f"{number}: {line.strip()}")
    joined = "\n".join(offenders)
    assert not offenders, f"meta reaches an attribute unescaped:\n{joined}"
