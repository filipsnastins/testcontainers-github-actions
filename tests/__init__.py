"""This file runs before any tests are run.
It sets dummy AWS credentials so that we don't accidentally mutate real infrastructure.

https://docs.getmoto.org/en/latest/docs/getting_started.html?highlight=muta#how-do-i-avoid-tests-from-mutating-my-real-infrastructure
"""
import os

os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
