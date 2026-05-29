#!/usr/bin/env python3
"""
Unit tests for run-only organize state.

These replace the former ``test_archimedius_core`` suite: source/destination,
templates, and operation mode now live in :mod:`settings` and flow into
:mod:`organize_plan`, leaving only the run flags here.
"""

from run_state import RunState


def test_new_run_state_is_idle():
    state = RunState()

    assert state.is_running is False
    assert state.stop_requested is False
    assert state.files_processed == 0


def test_begin_resets_flags_for_a_new_run():
    state = RunState(is_running=False, stop_requested=True, files_processed=7)

    state.begin()

    assert state.is_running is True
    assert state.stop_requested is False
    assert state.files_processed == 0


def test_stop_sets_stop_requested_flag():
    state = RunState()
    state.begin()

    state.stop()

    assert state.stop_requested is True
    # stop() only requests a stop; the run loop owns clearing is_running.
    assert state.is_running is True
