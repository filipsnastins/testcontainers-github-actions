# noqa: INP001
from subprocess import check_call


def hooks() -> None:
    check_call(["pre-commit", "run", "--all-files"])


def format() -> None:
    check_call(["black", "."])
    check_call(["isort", "."])
    check_call(
        [
            "autoflake",
            "--in-place",
            "--recursive",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--ignore-init-module-imports",
            ".",
        ]
    )


def lint() -> None:
    check_call(["flake8", "."])
    check_call(["mypy", "src", "tests"])


def test() -> None:
    check_call(["pytest"])


def test_cov_term() -> None:
    check_call(["pytest", "--cov=src", "--cov-branch", "--cov-report=term-missing"])


def test_cov_html() -> None:
    check_call(["pytest", "--cov=src", "--cov-branch", "--cov-report=html:build/htmlcov"])


def test_ci() -> None:
    check_call(
        [
            "pytest",
            "-v",
            "--cov=src",
            "--cov-branch",
            "--cov-report=xml:build/coverage.xml",
            "--cov-report=html:build/htmlcov",
            "--junitxml=build/tests.xml",
        ]
    )
