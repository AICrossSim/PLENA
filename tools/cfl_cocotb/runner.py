from os import path, getenv
import logging
from pathlib import Path
from copy import deepcopy
import re
import inspect
from typing import Any
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import time

import cocotb
from cocotb.runner import get_runner, get_results
# from mase_components.deps import MASE_HW_DEPS

logger = logging.getLogger("sim_runner")
logger.setLevel("INFO")


def _verilator_args(hierarchical, trace):
    return [
        # Verilator linter is overly strict.
        # Too many errors
        # These errors are in later versions of verilator
        "-Wno-GENUNNAMED",
        "-Wno-WIDTHEXPAND",
        "-Wno-WIDTHTRUNC",
        # Simulation Optimisation
        "-Wno-UNOPTFLAT",
        "-prof-c",
        "--assert",
        "--stats",
        # Hierarchical
        *(["--hierarchical"] if hierarchical else []),
        # Signal trace in dump.fst
        *(["--trace-fst", "--trace-structs"] if trace else []),
        "-O2",
        "-build-jobs",
        "8",
        "-Wno-fatal",
        "-Wno-lint",
        "-Wno-style",
    ]


def _single_test(
    i: int,  # id
    include_files: Path,
    extra_include_files: str,
    definitions_path: str,
    module: str,
    module_params: dict,
    module_path: Path,
    test_work_dir: Path,
    sim: str = "verilator",
    extra_build_args: list[str] = [],
    seed: int = None,
    trace: bool = False,
    skip_build: bool = False,
    hierarchical: bool = False,
):
    print("# ---------------------------------------")
    print(f"# Test {i}")
    print("# ---------------------------------------")
    print(f"# Parameters:")
    print(f"# - {'Test Index'}: {i}")
    for k, v in module_params.items():
        print(f"# - {k}: {v}")
    print("# ---------------------------------------")

    runner = get_runner(getenv("SIM", sim))

    if not skip_build:

        if sim == "verilator":
            tool_args = _verilator_args(hierarchical, trace)
            sources = [module_path]
            includes = [str(include_files) + "/rtl/"]
            if extra_include_files:
                for exclude in extra_include_files:
                    includes.append(exclude+ "/rtl/")
            if definitions_path:
                includes.append(definitions_path)
                    
        elif sim == "icarus":
            tool_args = []
            sources = [module_path]
            includes = [str(include_files) + "/rtl/"]
        else:
            raise ValueError(f"Unsupported simulator: {sim}")

        runner.build(
            verilog_sources=sources,
            includes=includes,
            hdl_toplevel=module,
            build_args=[
                *tool_args,
                *extra_build_args,
            ],
            # Do not use params in hierarchical verilation
            parameters=module_params if not hierarchical else {},
            build_dir=test_work_dir,
        )

    try:
        runner.test(
            hdl_toplevel=module,
            hdl_toplevel_lang="verilog",
            test_module=module + "_tb",
            seed=seed,
            results_xml="results.xml",
            build_dir=test_work_dir
        )
        num_tests, fail = get_results(test_work_dir.joinpath("results.xml"))
    except Exception as e:
        print(f"Error occured while running Verilator simulation: {e}")
        num_tests = fail = 1

    return {
        "num_tests": num_tests,
        "failed_tests": fail,
        "params": module_params,
    }


def veri_runner(
    module=None,
    group=None,
    additional_include_paths=None,
    definitions_path=None,
    module_param_list: list[dict[str, Any]] = [dict()],
    sim: str = "verilator",
    extra_build_args: list[str] = [],
    seed: int = None,
    jobs: int = 1,
    trace: bool = False,
    skip_build: bool = False,
    hierarchical: bool = False,
    template: bool = False,
):
    start_time = time()

    if group == None or module == None:
        # Autodetect
        # Get file which called this function
        # Should be of form components/<group>/test/<module>_tb.py
        test_filepath = inspect.stack()[1].filename
        # TODO - Need to rewrite this 
        matches = re.search(
            r"src/([\w/]+)/test/(\w+)_tb\.py", test_filepath
        )
        assert (
            matches != None
        ), "Did not find file that matches <module>_tb.py in the test folder!"
        group, module = matches.groups()

    # Group path is components/<group>
    test_filepath = inspect.stack()[1].filename
    group_path = Path(test_filepath).parent.parent
    # Components path is components
    module_path = group_path.joinpath("rtl").joinpath(f"{module}.sv")

    if template:
        template_path = group_path.joinpath("rtl").joinpath(f"{module}.sv.template")
        assert path.exists(template_path), f"{template_path} does not exist."
    else:
        # Try to find RTL file:
        # components/<group>/rtl/<module>.py
        assert path.exists(module_path), f"{module_path} does not exist."


    total_tests = 0
    total_fail = 0
    passed_cfgs = []
    failed_cfgs = []

    # Single threaded run
    if jobs == 1:
        for i, module_params in enumerate(module_param_list):
            test_work_dir = group_path.joinpath(f"test/build/{module}/test_{i}")
            results = _single_test(
                i=i,
                include_files=group_path,
                extra_include_files=additional_include_paths,
                definitions_path=definitions_path,
                module=module,
                module_params=module_params,
                module_path=module_path,
                test_work_dir=test_work_dir,
                sim=sim,
                extra_build_args=extra_build_args,
                seed=seed,
                trace=trace,
                skip_build=skip_build,
                hierarchical=hierarchical,
            )
            total_tests += results["num_tests"]
            total_fail += results["failed_tests"]
            if results["failed_tests"]:
                failed_cfgs.append((i, module_params))
            else:
                passed_cfgs.append((i, module_params))

    # Multi threaded run
    else:
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            # TODO: add timeout
            future_to_job_meta = {}
            for i, module_params in enumerate(module_param_list):
                test_work_dir = group_path.joinpath(f"test/build/{module}/test_{i}")
                future = executor.submit(
                    _single_test,
                    i=i,
                    include_files=group_path,
                    module=module,
                    module_params=module_params,
                    module_path=module_path,
                    test_work_dir=test_work_dir,
                    sim=sim,
                    extra_build_args=extra_build_args,
                    seed=seed,
                    trace=trace,
                    skip_build=skip_build,
                    hierarchical=hierarchical,
                )
                future_to_job_meta[future] = {
                    "id": i,
                    "params": deepcopy(module_params),
                }

            # Wait for futures to complete
            for future in as_completed(future_to_job_meta):
                meta = future_to_job_meta[future]
                id = meta["id"]
                params = meta["params"]
                try:
                    result = future.result()
                except Exception as exc:
                    print("Test %r generated an exception: %s" % (id, exc))
                else:
                    print("Test %r is done. Result: %s" % (id, result))
                    total_tests += result["num_tests"]
                    total_fail += result["failed_tests"]
                    if result["failed_tests"]:
                        failed_cfgs.append((id, params))
                    else:
                        passed_cfgs.append((id, params))

    print("# ---------------------------------------")
    print("# Test Results")
    print("# ---------------------------------------")
    print("# - Time elapsed: %.2f seconds" % (time() - start_time))
    print("# - Jobs: %d" % (jobs))
    print("# - Passed: %d" % (total_tests - total_fail))
    print("# - Failed: %d" % (total_fail))
    print("# - Total : %d" % (total_tests))
    print("# ---------------------------------------")

    if len(passed_cfgs):
        passed_cfgs = sorted(passed_cfgs, key=lambda t: t[0])
        print(f"# Passed Configs")
        print("# ---------------------------------------")
        for i, params in passed_cfgs:
            print(f"# - test_{i}: {params}")
        print("# ---------------------------------------")

    if len(failed_cfgs):
        failed_cfgs = sorted(failed_cfgs, key=lambda t: t[0])
        print(f"# Failed Configs")
        print("# ---------------------------------------")
        for i, params in failed_cfgs:
            print(f"# - test_{i}: {params}")
        print("# ---------------------------------------")

    return total_fail
