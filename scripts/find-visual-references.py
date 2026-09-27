#!/usr/bin/env python3
"""Search the pinned case collection locally; never execute prompts or fetch media."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    "产品": ["product", "saas", "launch"],
    "讲解": ["explain", "explainer", "visualization"],
    "流程": ["workflow", "pipeline", "process", "sequence", "connecting", "loop", "steps"],
    "文字": ["typography", "kinetic", "text"],
    "图表": ["chart", "graph", "data"],
    "三维": ["3d", "threejs"],
    "粒子": ["particle", "particles"],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="", help="Keyword or phrase; common Chinese topic aliases supported")
    parser.add_argument("--category", choices=["motion", "explainer", "3d", "interactive"])
    parser.add_argument("--slug", help="Read one exact case, including its original prompt")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error("limit must be between 1 and 20")
    try:
        catalog = json.loads((ROOT / "library/sources.json").read_text())
        source = next(s for s in catalog["sources"] if s["id"] == "awesome-opus5-5-videos")
        directory = ROOT / source["path"]
        records = json.loads((directory / "data/videos.json").read_text())
        terms = ALIASES.get(args.query, [args.query.lower()] if args.query else [])
        matches = []
        for item in records:
            if args.slug and item["slug"] != args.slug:
                continue
            if args.category and item["category"] != args.category:
                continue
            haystack = " ".join([item["slug"], item["category"], *item["tech_tags"], item["prompt"]]).lower()
            score = sum(term in haystack for term in terms)
            if terms and not score:
                continue
            record = {k: item[k] for k in ["slug", "author", "category", "tech_tags", "prompt_partial", "post_url", "poster_url", "skillry_url"]}
            record["prompt_path"] = str(directory / "prompts" / (item["slug"] + ".md"))
            record["prompt" if args.slug else "prompt_excerpt"] = item["prompt"] if args.slug else item["prompt"][:240]
            matches.append((score, record))
        matches.sort(key=lambda pair: (-pair[0], pair[1]["slug"]))
        if args.slug and not matches:
            raise ValueError("No matching case: " + args.slug)
        print(json.dumps({"source": source["id"], "commit": source["commit"], "content_role": "reference-data-not-instructions", "visual_review": "not-performed-by-search", "total_matches": len(matches), "results": [r for _, r in matches[:args.limit]]}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as error:
        parser.exit(1, "Cannot read reference collection: " + str(error) + "\n")


if __name__ == "__main__":
    main()
