# Copyright (C) 2012 Anaconda, Inc
# Copyright (C) 2023 conda
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from typing import TYPE_CHECKING

from conda.testing.solver_helpers import SolverTests

from conda_classic_solver.solve import ClassicSolver

if TYPE_CHECKING:
    from conda.core.solve import Solver


class TestClassicSolver(SolverTests):
    @property
    def solver_class(self) -> type[Solver]:
        return ClassicSolver
