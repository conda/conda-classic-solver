# Copyright (C) 2012 Anaconda, Inc
# Copyright (C) 2023 conda
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest
from conda.base.constants import UpdateModifier
from conda.base.context import context, reset_context
from conda.common.serialize import json
from conda.core.index import Index, ReducedIndex
from conda.core.prefix_data import PrefixData
from conda.exceptions import PackagesNotFoundError
from conda.models.match_spec import MatchSpec
from conda.models.records import PackageRecord
from conda.testing.solver_helpers import SimpleEnvironment

from conda_classic_solver.solve import ClassicSolver


@pytest.fixture
def solver_env(tmp_path, tmp_pkgs_dir, reset_conda_context, monkeypatch):
    monkeypatch.setenv("CONDA_SOLVER", "pycosat")
    reset_context(search_path=())
    return SimpleEnvironment(tmp_path, ClassicSolver, subdirs=("noarch",))


@pytest.mark.skipif(
    not hasattr(context, "exclude_newer_policy"),
    reason="conda does not support exclude-newer policies",
)
@pytest.mark.parametrize("policy", ["global", "channel", "package"])
def test_exclude_newer_selects_older_package(
    solver_env, tmp_path, policy, http_test_server
):
    solver_env = SimpleEnvironment(
        http_test_server.directory, ClassicSolver, subdirs=("noarch",)
    )
    solver_env.repo_packages = [
        PackageRecord(
            name="sample",
            version=version,
            build="0",
            build_number=0,
            subdir="noarch",
            timestamp=timestamp,
            depends=[],
        )
        for version, timestamp in (("1.0", 1704067200000), ("2.0", 1706745600000))
    ]
    solver_env.solver(add=(), remove=())
    channel = http_test_server.get_url("channels/test")
    cutoff = "2024-01-15"
    settings = {
        "global": {"exclude_newer": cutoff},
        "channel": {
            "channel_settings": [
                {
                    "channel": channel,
                    "exclude_newer": cutoff,
                }
            ]
        },
        "package": {"exclude_newer_package": {"sample": cutoff}},
    }
    condarc = tmp_path / "condarc"
    condarc.write_text(json.dumps(settings[policy]))
    reset_context(search_path=(str(condarc),))

    solver = ClassicSolver(
        prefix=tmp_path / "prefix",
        channels=(channel,),
        subdirs=("noarch",),
        specs_to_add=("sample",),
    )
    reset_context(search_path=())
    solution = solver.solve_final_state()

    assert [(record.name, record.version) for record in solution] == [("sample", "1.0")]


@pytest.mark.parametrize("index_prefix", [None, "target", "other"])
@pytest.mark.parametrize("realized", [False, True])
def test_solve_with_provided_index(
    solver_env, tmp_path, mocker, index_prefix, realized
):
    records = {
        name: PackageRecord(
            name=name,
            version="1.0",
            build="0",
            build_number=0,
            subdir="noarch",
            channel=(tmp_path / "channels" / "test").as_uri(),
            depends=depends,
        )
        for name, depends in (
            ("installed-app", ["dependency"]),
            ("dependency", ["leaf"]),
            ("leaf", []),
            ("requested", []),
            ("unrelated", []),
        )
    }
    solver_env.repo_packages = list(records.values())
    solver_env.installed_packages = [
        records[name] for name in ("installed-app", "dependency", "leaf")
    ]
    solver = solver_env.solver(add=("requested",), remove=())
    source_prefix = (
        PrefixData(solver.prefix if index_prefix == "target" else tmp_path / "other")
        if index_prefix is not None
        else None
    )
    provided_index = Index(
        channels=solver.channels,
        prepend=False,
        subdirs=("noarch",),
        use_cache=False,
        use_system=True,
        prefix=source_prefix,
    )
    if realized:
        provided_index.data
    elif index_prefix != "other":
        mocker.patch.object(
            Index, "_realize", side_effect=AssertionError("Eager index")
        )
    solver._index = provided_index

    solution = solver.solve_final_state()

    assert {record.name for record in solution} == {
        "installed-app",
        "dependency",
        "leaf",
        "requested",
    }
    assert provided_index.prefix_data is source_prefix
    assert ("_data" in provided_index.__dict__) is (realized or index_prefix == "other")


def test_prepare_reduces_provided_index_for_each_spec_set(tmp_path, mocker):
    solver = ClassicSolver(prefix=tmp_path, channels=())
    provided_index = Index(prepend=False)
    reduced_indexes = [mocker.Mock(spec=ReducedIndex), mocker.Mock(spec=ReducedIndex)]
    reduce_index = mocker.patch.object(
        Index, "get_reduced_index", autospec=True, side_effect=reduced_indexes
    )
    mocker.patch("conda_classic_solver.solve.Resolve")
    mocker.patch.object(Index, "_realize", side_effect=AssertionError("Eager index"))
    solver._index = provided_index

    for name, reduced_index in zip(("first", "second"), reduced_indexes):
        prepared_index, _ = solver._prepare({MatchSpec(name)})
        assert prepared_index is reduced_index

    assert "_data" not in provided_index.__dict__
    assert provided_index.prefix_data is None
    assert reduce_index.call_count == 2
    for call in reduce_index.call_args_list:
        assert call.args[0].prefix_data.prefix_path == tmp_path


def test_missing_pinned_version_reports_channels(solver_env, monkeypatch):
    solver_env.repo_packages = [
        PackageRecord(
            name=name,
            version="1.0",
            build="0",
            build_number=0,
            subdir="noarch",
            depends=depends,
        )
        for name, depends in (("app", ["dependency >=1"]), ("dependency", []))
    ]
    solver = solver_env.solver(add=("app",), remove=())
    channels = tuple(channel.url() for channel in solver.channels)
    monkeypatch.setenv("CONDA_CHANNELS", ",".join(channels))
    monkeypatch.setenv("CONDA_PINNED_PACKAGES", "dependency=99")
    reset_context(search_path=())

    with pytest.raises(PackagesNotFoundError) as exc:
        solver.solve_final_state(update_modifier=UpdateModifier.FREEZE_INSTALLED)

    assert tuple(map(str, exc.value.packages)) == ("dependency=99",)
    assert exc.value.channel_urls == channels
