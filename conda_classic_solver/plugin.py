# Copyright (C) 2022 Anaconda, Inc
# Copyright (C) 2023 conda
# SPDX-License-Identifier: BSD-3-Clause
"""
The hooks for the conda solver plugin system.
"""

from typing import Iterable

from conda.plugins import CondaSolver, hookimpl

from .solve import ClassicSolver


@hookimpl
def conda_solvers() -> Iterable[CondaSolver]:
    """
    The conda plugin hook implementation to load the solver into conda.
    """
    yield CondaSolver(
        name="classic",
        backend=ClassicSolver,
    )
