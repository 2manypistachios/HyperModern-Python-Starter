# Standard
import contextlib
import os
import tempfile
from typing import Any, Generator

# Local
import nox
from nox.sessions import Session

# Definition
package = "hypermodern_python"
nox.options.sessions = "lint", "safety", "mypy", "tests"
locations = "src", "tests", "noxfile.py"


@contextlib.contextmanager
def temporary_filename(suffix: str = None) -> Generator[str, None, None]:
    """Context that introduces a temporary file.

    Creates a temporary file, yields its name, and upon context exit, deletes it.
    (In contrast, tempfile.NamedTemporaryFile() provides a 'file' object and
    deletes the file as soon as that file object is closed, so the temporary file
    cannot be safely re-opened by another library or process.)

    Args:
    suffix: desired filename extension (e.g. '.mp4').

    Yields:
    The name of the temporary file.
    """
    try:
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_name = f.name
        f.close()
        yield tmp_name
    finally:
        os.unlink(tmp_name)


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """ Use Poetry Export to access lock file to install correct packages.
    See https://cjolowicz.github.io/posts/hypermodern-python-03-linting/
    """
    with temporary_filename() as filename:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={filename}",
            external=True,
        )
        session.install(f"--constraint={filename}", *args, **kwargs)


@nox.session(python="3.8")  # Black Styling
def black(session: Session) -> None:
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session(python=["3.8"])  # LINTING SESSION
def lint(session: Session) -> None:
    args = session.posargs or locations
    install_with_constraints(
        session,
        "flake8",  # Basic Linting
        "flake8-annotations",  # Typing
        "flake8-bandit",  # Safety
        "flake8-black",  # Styling
        "flake8-bugbear",  # Opionated Design
        "flake8-import-order",  # Imports
    )
    session.run("flake8", *args)


@nox.session(python="3.8")  # Secure-Packages Analysis
def safety(session: Session) -> None:
    with temporary_filename() as filename:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={filename}",
            external=True,
        )
        install_with_constraints(session, "safety")
        session.run("safety", "check", f"--file={filename}", "--full-report")


@nox.session(python=["3.8"])  # Static File-Type Checking
def mypy(session: Session) -> None:
    args = session.posargs or locations
    install_with_constraints(session, "mypy")
    session.run("mypy", *args)


@nox.session(python=["3.8"])  # Run all tests
def tests(session: Session) -> None:
    args = session.posargs or ["--cov", "-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session, "coverage[toml]", "pytest", "pytest-cov", "pytest-mock"
    )
    session.run("pytest", *args)


@nox.session(python=["3.8"])  # Runtime Type Checking
def typeguard(session: Session) -> None:
    args = session.posargs or ["-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "pytest", "pytest-mock", "typeguard")
    session.run("pytest", f"--typeguard-packages={package}", *args)
