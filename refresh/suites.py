"""The full suite set the monthly refresh runs before it may publish.

The same set the October packets ran by hand (03 RESEARCH/oct-2026/scripts/
q2_run_suites.sh, AUDIT_2026-10 section B), held here so the scheduled task
does not depend on a file outside the repository. A suite added to the site
must be added here too, or the refresh publishes past it; tests/test_refresh.py
fails when a test file in tests/ is in neither this list nor SKIP.

test_generators.py is not here: it is the last step of the ordering rule,
which monthly.py runs before the suites.
"""
import os

FIXED = [
    "python beauty/test_beauty.py", "python beauty/break_log.py", "python beauty/break_model.py",
    "python beauty/break_topics.py", "python climate-cost/test_lca.py", "node climate-cost/test_scene.js",
    "python continents/test_continents.py", "python continents/break_b1.py", "python continents/break_gates.py",
    "node continents/test_app.js", "python longevity-quotient/test_fit_strategy.py",
    "python longevity-quotient/test_merge.py", "python longevity-quotient/test_lq.py", "node longevity-quotient/test_perf.js", "node skyline/test_app.js", "python skyline/test_skylines.py",
    "python tests/test_units.py", "python tests/test_no_address.py", "python tests/test_lf.py",
    "python tests/test_markup.py", "python tests/test_retro.py",
    "node tests/verify_hero_systems.js", "python tests/test_fit_ticks.py", "node tests/fig_served_widths.js",
    "python tests/test_fig_floor.py", "node tests/test_invariants.js", "node tests/test_layout.js",
    "node tests/test_nav_states.js", "node tests/test_chrome.js", "node tests/test_contrast.js",
    "node tests/test_scroll_jank.js",
]
# run when present: page suites and parity checks that arrive with their pages
OPTIONAL = [
    "python meter/test_meter.py", "python tests/test_parity_meter.py",
    "python takeaway/test_takeaway.py", "python lostgas/test_lostgas.py", "python storage/test_storage.py", "python heat/test_heat.py",
    "node tests/test_kit.js", "python tests/test_refresh.py",
]
# test files in tests/ that are not suites in their own right
SKIP = {"three-stub.js", "parity_engine.js", "probe_scene.js", "test_atlas_interaction.js",
        "test_parity.py", "test_payload.py", "test_demand_response.py", "test_generators.py",
        "test_parity_lauf.py"}


def commands(root):
    out = list(FIXED)
    for c in OPTIONAL:
        if os.path.exists(os.path.join(root, c.split()[1])):
            out.append(c)
    return out
