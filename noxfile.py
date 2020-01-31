"""Nox sessions."""
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
locations = "src", "tests", "noxfile.py", "docs/conf.py"


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
        generator: The name of the temporary file.
    """
    try:
        f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_name = f.name
        f.close()
        yield tmp_name
    finally:
        os.unlink(tmp_name)


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """Install Packages constrained by Poetry's lock file.

    See https://cjolowicz.github.io/posts/hypermodern-python-03-linting/

    Args:
        session: Session from Nox
        *args: Args
        **kwargs: Kwards
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


@nox.session(python="3.8")
def black(session: Session) -> None:
    """Run black code formatter."""
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session(python=["3.8"])
def lint(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or locations
    install_with_constraints(
        session,
        "flake8",  # Basic Linting
        "flake8-annotations",  # Typing
        "flake8-bandit",  # Safety
        "flake8-black",  # Styling
        "flake8-bugbear",  # Opionated Design
        "flake8-docstrings",  # Documentation Linting
        "flake8-import-order",  # Imports
        "darglint",  # Check documentation code
    )
    session.run("flake8", *args)


@nox.session(python="3.8")  # Secure-Packages Analysis
def safety(session: Session) -> None:
    """Scan dependancies for insecure packages."""
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
    """Type-check using mypy."""
    args = session.posargs or locations
    install_with_constraints(session, "mypy")
    session.run("mypy", *args)


@nox.session(python=["3.8"])  # Run all tests
def tests(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["--cov", "-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session, "coverage[toml]", "pytest", "pytest-cov", "pytest-mock"
    )
    session.run("pytest", *args)


@nox.session(python=["3.8"])
def typeguard(session: Session) -> None:
    """Runtime type checking using the Typeguard."""
    args = session.posargs or ["-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "pytest", "pytest-mock", "typeguard")
    session.run("pytest", f"--typeguard-packages={package}", *args)


@nox.session(python=["3.8"])
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "xdoctest")
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(python="3.8")
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "sphinx", "sphinx-autodoc-typehints")
    session.run("sphinx-build", "docs", "docs/_build")
