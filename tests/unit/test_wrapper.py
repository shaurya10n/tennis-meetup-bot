"""Smoke tests for command wrapper registration."""

import importlib


def test_user_commands_cog_imports():
  module = importlib.import_module("src.cogs.user.commands.wrapper")
  assert hasattr(module, "UserCommands")
  assert hasattr(module, "setup")


def test_find_match_constants_exported():
  from src.cogs.user.commands.find_match.constants import (
      FIND_MATCHES_DESC,
      FIND_MATCHES_FOR_SCHEDULE_DESC,
  )
  assert FIND_MATCHES_DESC
  assert FIND_MATCHES_FOR_SCHEDULE_DESC


def test_schedule_constants_exported():
  from src.cogs.user.commands.schedule.constants import (
      SCHEDULE_ADD_DESC,
      SCHEDULE_CLEAR_DESC,
      SCHEDULE_VIEW_DESC,
  )
  assert SCHEDULE_ADD_DESC
  assert SCHEDULE_CLEAR_DESC
  assert SCHEDULE_VIEW_DESC
