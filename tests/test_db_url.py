"""Building the database URL, in particular injecting a password that
arrives separately (from a container secret) rather than inline."""

from db import with_password


def test_injects_password_for_a_bare_user():
    assert (
        with_password("postgresql://infabula@db.example/infabula", "s3cret")
        == "postgresql://infabula:s3cret@db.example/infabula"
    )


def test_keeps_the_port():
    assert (
        with_password("postgresql://infabula@db.example:5432/infabula", "s3cret")
        == "postgresql://infabula:s3cret@db.example:5432/infabula"
    )


def test_an_explicit_password_wins():
    """Never silently override one that's already there."""
    url = "postgresql://infabula:inline@db.example/infabula"
    assert with_password(url, "other") == url


def test_special_characters_are_escaped():
    """An unescaped @ or / would corrupt the URL's structure."""
    out = with_password("postgresql://infabula@db.example/infabula", "p@ss/w:rd")
    assert out == "postgresql://infabula:p%40ss%2Fw%3Ard@db.example/infabula"
    # And it still parses back to the original secret.
    from urllib.parse import unquote, urlsplit

    stored = urlsplit(out).password
    assert stored == "p%40ss%2Fw%3Ard"
    assert stored is not None and unquote(stored) == "p@ss/w:rd"


def test_sqlite_url_is_left_alone():
    """No host, so there's no userinfo to put a password into."""
    url = "sqlite:///data/infabula.db"
    assert with_password(url, "s3cret") == url
