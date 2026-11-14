"""
Build outputs/payload.json for aiweb.html from sources.py.

Every value on the page comes from sources.FIG (as published) or is derived here from those values (ratios and
growth rates), so the page never types a number. The payload is written with sorted keys and fixed float
formatting so a rebuild gives the same bytes (test_aiweb.py checks this).

Run:  python build_aiweb.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")


def main():
    bad = [k for k, v in S.FIG.items() if v[3] not in S.REFS]
    if bad:
        raise SystemExit(f"figures naming an unknown source: {bad}")
    fig = {k: {"value": v[0], "unit": v[1], "period": v[2], "source": v[3]} for k, v in S.FIG.items()}
    val = {k: v[0] for k, v in S.FIG.items()}
    derived = {
        # Alphabet's year-on-year search revenue growth, from the two quarters it reports
        "goog_growth": round(100 * (val["goog_rev"] / val["goog_rev_prev"] - 1), 1),
        # how many times as many visits google.com had as chatgpt.com
        "g_c_ratio": round(val["g_visits"] / val["c_visits"], 1),
        # how many times more often people clicked a result without an AI summary
        "pew_ratio": round(val["pew_click_no"] / val["pew_click_ai"], 2),
        # what is published vs what Google shows
        "pub_shown_ratio": round(val["graphite_articles"] / val["graphite_serp"], 2),
        # machine share of requests from Cloudflare's human share, to check against Imperva's
        "cf_machine_html": 100 - val["cf_human_html"],
        # growth in tracked AI content-farm sites
        "ng_ratio": round(val["ng_2026"] / val["ng_2023"], 1),
        # OpenAI and Anthropic crawl ratios against Google's
        "openai_vs_google": round(val["crawl_openai"] / val["crawl_google"]),
        "anthropic_vs_google": round(val["crawl_anthropic"] / val["crawl_google"]),
    }
    payload = {"fig": fig, "derived": derived, "refs": S.REFS,
               "scenarios": S.SCENARIOS, "today": S.TODAY, "strip": S.STRIP, "scorecard": S.SCORECARD,
               "as_of": "2026-11-14"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(f"  payload: {len(fig)} figures, {len(derived)} derived, {len(S.REFS)} sources -> outputs/payload.json")


if __name__ == "__main__":
    main()
