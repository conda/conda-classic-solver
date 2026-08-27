# Copyright (C) 2012 Anaconda, Inc
# Copyright (C) 2023 conda
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

from conda_classic_solver import plugin
from conda_classic_solver.plugin import conda_solvers

if TYPE_CHECKING:
    from pytest import Monkeypatch


def test_plugin_yields_pycosat():
    solvers = list(conda_solvers())
    names = [s.name for s in solvers]
    assert "pycosat" in names


def test_plugin_has_classic_true(monkeypatch: Monkeypatch):
    monkeypatch.setattr(plugin, "conda_version", "26.7.1")
    assert plugin._conda_has_classic()
    names = [s.name for s in conda_solvers()]
    assert "classic" not in names


def test_plugin_has_classic_false(monkeypatch: Monkeypatch):
    monkeypatch.setattr(plugin, "conda_version", "26.7.2.dev66")
    assert not plugin._conda_has_classic()
    names = [s.name for s in conda_solvers()]
    assert "classic" in names
