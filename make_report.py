import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from evaluate import build_views, evaluate_rows
from guard import decide, parse_view


PROJECT_DIR = Path(__file__).resolve().parent
FULL_CLEAN = PROJECT_DIR / "results_clean_all.csv"
FULL_PHONE = PROJECT_DIR / "results_phone_all.csv"
PILOT = PROJECT_DIR / "results" / "day8_clean_pilot_results.csv"
REQUIRED_FULL_COLUMNS = (
    "view_v25_itn",
    "view_v25_literal",
    "view_v30",
    "expected_len",
    "kind",
    "truth",
)
OUTPUT_REPORT = PROJECT_DIR / "RESULTS_AUTO.md"
OUTPUT_CHART = PROJECT_DIR / "results_chart.png"
OUTPUT_DEMO_IDS = PROJECT_DIR / "demo_ids.txt"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no CSV header")
        return list(reader), set(reader.fieldnames)


def require_full_columns(path, columns):
    missing = [column for column in REQUIRED_FULL_COLUMNS if column not in columns]
    if missing:
        raise ValueError(
            f"{path} is missing required full-result columns: {', '.join(missing)}"
        )


def adapt_full_rows(rows, condition):
    adapted = []
    for row in rows:
        normalized = dict(row)
        normalized["condition"] = condition
        # Map actual full-result fields to the existing evaluator's view order.
        normalized["view_verbatim"] = row.get("view_v25_itn", "")
        normalized["view_itn"] = row.get("view_v25_literal", "")
        normalized["view_v3_0"] = row.get("view_v30", "")
        adapted.append(normalized)
    return adapted


def evaluate_condition(rows, label):
    evaluation = evaluate_rows(rows)
    details = []
    for index, row in enumerate(rows, start=1):
        truth = (row.get("truth") or "").strip()
        views = build_views(row)
        if not truth or not views:
            continue
        kind = row["kind"]
        truth_value = truth if kind == "digits" else int(truth)
        first_value, _ = parse_view(kind, next(iter(views.values())))
        expected_len = int(row["expected_len"]) if row.get("expected_len") else None
        guard = decide(kind, views, expected_len=expected_len)
        details.append(
            {
                "id": row.get("id") or f"row {index}",
                "language": row.get("language") or "?",
                "condition": label,
                "truth": truth_value,
                "first_value": first_value,
                "guard_value": guard["value"],
                "decision": guard["decision"],
                "first_wrong": first_value != truth_value,
                "guard_wrong": guard["value"] != truth_value,
                "guard_reasons": ", ".join(guard["reasons"]) or "none",
            }
        )
    return {"label": label, "rows": rows, "evaluation": evaluation, "details": details}


def load_inputs(clean_path, phone_path, pilot_path):
    clean_exists = clean_path.is_file()
    phone_exists = phone_path.is_file()
    if clean_exists and phone_exists:
        clean_rows, clean_columns = read_csv(clean_path)
        phone_rows, phone_columns = read_csv(phone_path)
        require_full_columns(clean_path, clean_columns)
        require_full_columns(phone_path, phone_columns)
        return "full", [
            evaluate_condition(adapt_full_rows(clean_rows, "clean"), "clean"),
            evaluate_condition(adapt_full_rows(phone_rows, "phone"), "phone"),
        ], []

    missing = []
    if not clean_exists:
        missing.append(clean_path.name)
    if not phone_exists:
        missing.append(phone_path.name)
    if not pilot_path.is_file():
        raise FileNotFoundError(
            "Full inputs are incomplete and the clean pilot file is also missing: "
            + ", ".join(missing + [pilot_path.name])
        )
    pilot_rows, _ = read_csv(pilot_path)
    return "pilot", [evaluate_condition(pilot_rows, "clean pilot")], missing


def select_pilot_demos(result):
    categories = {}
    for detail in result["details"]:
        if detail["first_wrong"] and detail["decision"] == "CONFIRM":
            categories.setdefault("Prisma wrong and Guard asks", detail["id"])
        if detail["decision"] == "ACCEPT" and not detail["guard_wrong"]:
            categories.setdefault("Accepted value matches dataset label", detail["id"])
        if detail["decision"] == "ACCEPT" and detail["guard_wrong"]:
            categories.setdefault("Silent error", detail["id"])
        if detail["language"] == "kn":
            categories.setdefault("Kannada", detail["id"])
    return categories


def render_report(mode, results, missing_full):
    lines = [
        "# SankhyaGuard — Automatically Generated Results",
        "",
    ]
    if mode == "pilot":
        lines += [
            "> **PILOT ONLY:** This report uses saved clean-pilot data. It is not the full 72-clip experiment.",
            "",
            "## Data scope",
            "",
            f"- Source: `results/day8_clean_pilot_results.csv` ({results[0]['evaluation']['input_rows']} rows).",
            f"- Complete pairs evaluated: {results[0]['evaluation']['evaluated_rows']}.",
            f"- Skipped rows: {results[0]['evaluation']['skipped_rows']}.",
            f"- Missing full-result inputs: {', '.join(f'`{name}`' for name in missing_full)}.",
            "- No phone, SNR 5, or SNR 10 model results are included.",
            "- Dataset labels were not independently checked against each recording during this report generation.",
            "",
        ]
    else:
        lines += [
            "> This report uses the full clean and phone CSV inputs. It does not include pilot rows.",
            "",
            "## Data scope",
            "",
        ]
        for result in results:
            evaluation = result["evaluation"]
            lines.append(
                f"- `{result['label']}`: {evaluation['input_rows']} input rows, "
                f"{evaluation['evaluated_rows']} evaluated, {evaluation['skipped_rows']} skipped."
            )
        lines += [
            "- The SNR 5 and SNR 10 conditions are not included in these two inputs.",
            "",
        ]

    lines += [
        "## Evaluation definitions",
        "",
        "Counts below use the existing `evaluate.py` and Guard logic. A is the first view; G is the Guard. "
        "A caught error means the Guard requested confirmation on a row where A was wrong; it is not a correction.",
        "",
        "## Metrics",
        "",
        "| Dataset | Input | Evaluated | Skipped | Skip reasons | A wrong | G silent wrong | G asks | Caught | Needless |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        report = result["evaluation"]
        stats = report["stats"].get("ALL", {})
        skip_text = ", ".join(
            f"{reason}: {count}"
            for reason, count in sorted(report["skip_reasons"].items())
        ) or "none"
        lines.append(
            f"| {result['label']} | {report['input_rows']} | {report['evaluated_rows']} "
            f"| {report['skipped_rows']} | {skip_text} | {stats.get('A_errors', 0)} "
            f"| {stats.get('G_silent_errors', 0)} | {stats.get('G_confirms', 0)} "
            f"| {stats.get('G_caught', 0)} | {stats.get('G_unneeded', 0)} |"
        )
    lines += [
        "",
        "### Evaluated rows by language",
        "",
        "| Dataset | Language | Evaluated | A wrong | G silent wrong | G asks | Caught | Needless |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        language_stats = result["evaluation"]["stats"]
        for language in sorted(key for key in language_stats if key != "ALL"):
            stats = language_stats[language]
            lines.append(
                f"| {result['label']} | {language} | {stats['n']} "
                f"| {stats['A_errors']} | {stats['G_silent_errors']} "
                f"| {stats['G_confirms']} | {stats['G_caught']} | {stats['G_unneeded']} |"
            )
    lines += [
        "",
        "The evaluator excludes rows without a truth value or usable transcript views. Its metric denominators are the evaluated rows, except caught errors, which are counted among first-view errors.",
        "",
        "## Row details",
        "",
        "| Dataset | ID | Language | Truth label | First-view parsed | Guard decision | Guard parsed | Outcome |",
        "|---|---|---|---:|---:|---|---:|---|",
    ]
    for result in results:
        for detail in result["details"]:
            if detail["decision"] == "CONFIRM":
                outcome = f"confirmation ({detail['guard_reasons']})"
            elif detail["guard_wrong"]:
                outcome = "silent error against dataset label"
            else:
                outcome = "accepted value matches dataset label"
            lines.append(
                f"| {result['label']} | `{detail['id']}` | {detail['language']} "
                f"| {detail['truth']} | {detail['first_value']} | {detail['decision']} "
                f"| {detail['guard_value']} | {outcome} |"
            )
    skipped_rows = [
        (result["label"], reason, clip_id)
        for result in results
        for reason, clip_ids in result["evaluation"]["skipped_ids"].items()
        for clip_id in clip_ids
    ]
    if skipped_rows:
        lines += [
            "",
            "## Incomplete or skipped rows",
            "",
            "| Dataset | ID | Skip reason |",
            "|---|---|---|",
        ]
        lines.extend(
            f"| {label} | `{clip_id}` | {reason} |"
            for label, reason, clip_id in skipped_rows
        )
    lines += [
        "",
        "## Demo clip availability",
        "",
    ]
    if mode == "pilot":
        categories = select_pilot_demos(results[0])
        for category in (
            "Prisma wrong and Guard asks",
            "Accepted value matches dataset label",
            "Silent error",
            "Phone quality",
            "Kannada",
        ):
            if category == "Phone quality":
                lines.append(
                    "- **Phone quality: unavailable.** No phone-condition model results are present."
                )
            elif category in categories:
                lines.append(f"- **{category}:** `{categories[category]}`")
            else:
                lines.append(f"- **{category}: unavailable in the evaluated pilot.**")
        lines += [
            "",
            "The generated `demo_ids.txt` contains only supported pilot IDs, one per line. A selected clip may represent more than one category. Matching a written label is not independent proof that the audio itself is correct.",
        ]
    else:
        lines += [
            "- The original `analyse.py` and its “Every row to study” output are unavailable, so the original analysis-based five-clip selection is not verified by this script.",
            "- No pilot examples are mixed into this full-results report.",
        ]
    lines += [
        "",
        "## Limitations",
        "",
        "- Agreement between model views does not prove a number is correct.",
        "- These counts describe only the supplied result files and the current parser/Guard.",
        "- Missing responses are skipped, not treated as successful results.",
    ]
    return "\n".join(lines) + "\n"


def create_chart(results, output_path):
    labels = []
    counts = []
    annotations = []
    for result in results:
        stats = result["evaluation"]["stats"].get("ALL", {})
        denominator = result["evaluation"]["evaluated_rows"]
        for label, key in (
            ("A wrong", "A_errors"),
            ("G silent wrong", "G_silent_errors"),
            ("G asks", "G_confirms"),
            ("Needless confirmations", "G_unneeded"),
        ):
            labels.append(f"{result['label']}: {label}")
            counts.append(stats.get(key, 0))
            annotations.append(f"{stats.get(key, 0)} / {denominator}")
        labels.append(f"{result['label']}: errors caught")
        counts.append(stats.get("G_caught", 0))
        annotations.append(
            f"{stats.get('G_caught', 0)} / {stats.get('A_errors', 0)} A errors"
        )

    height = max(4.5, len(labels) * 0.48 + 1.6)
    figure, axis = plt.subplots(figsize=(10, height))
    y_positions = list(range(len(labels)))
    bars = axis.barh(y_positions, counts, color="#5470C6")
    axis.set_yticks(y_positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Count (denominator shown at right)")
    title = (
        "SankhyaGuard - Clean pilot only"
        if results[0]["label"] == "clean pilot"
        else "SankhyaGuard - Full clean and phone results"
    )
    if results[0]["label"] == "clean pilot":
        title += f" ({results[0]['evaluation']['evaluated_rows']} complete pairs)"
    axis.set_title(title, pad=14)
    maximum = max(counts, default=0)
    axis.set_xlim(0, max(1.0, maximum * 1.3 + 0.4))
    for bar, annotation in zip(bars, annotations):
        axis.text(
            max(bar.get_width(), 0) + 0.04,
            bar.get_y() + bar.get_height() / 2,
            annotation,
            va="center",
        )
    figure.subplots_adjust(left=0.36, right=0.97, top=0.91, bottom=0.24)
    if results[0]["label"] == "clean pilot":
        figure.text(
            0.02,
            0.12,
            "Pilot counts only; categories may overlap. Dataset labels were not independently verified against audio.",
            fontsize=8,
        )
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def create_demo_ids(result, output_path):
    categories = select_pilot_demos(result)
    ordered_categories = (
        "Prisma wrong and Guard asks",
        "Accepted value matches dataset label",
        "Silent error",
        "Kannada",
    )
    ids = []
    for category in ordered_categories:
        clip_id = categories.get(category)
        if clip_id and clip_id not in ids:
            ids.append(clip_id)
    if not ids:
        raise ValueError("No supported pilot demo clips are available")
    output_path.write_text("\n".join(ids) + "\n", encoding="utf-8")
    return ids


def generate(
    report_path,
    chart_path,
    demo_ids_path,
    clean_path,
    phone_path,
    pilot_path,
    overwrite=False,
):
    targets = [report_path, chart_path, demo_ids_path]
    existing = [path for path in targets if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Refusing to overwrite existing output(s): "
            + ", ".join(str(path) for path in existing)
        )
    mode, results, missing_full = load_inputs(clean_path, phone_path, pilot_path)
    report_path.write_text(
        render_report(mode, results, missing_full), encoding="utf-8"
    )
    create_chart(results, chart_path)
    demo_ids = []
    if mode == "pilot":
        demo_ids = create_demo_ids(results[0], demo_ids_path)
    else:
        demo_ids_path.write_text(
            "# Not generated: analyse.py and its 'Every row to study' output are unavailable.\n",
            encoding="utf-8",
        )
    return mode, results, missing_full, demo_ids


def main():
    parser = argparse.ArgumentParser(
        description="Generate results from full clean/phone CSVs, or clearly labeled pilot data when full inputs are unavailable."
    )
    parser.add_argument("--clean", type=Path, default=FULL_CLEAN)
    parser.add_argument("--phone", type=Path, default=FULL_PHONE)
    parser.add_argument("--pilot", type=Path, default=PILOT)
    parser.add_argument("--report", type=Path, default=OUTPUT_REPORT)
    parser.add_argument("--chart", type=Path, default=OUTPUT_CHART)
    parser.add_argument("--demo-ids", type=Path, default=OUTPUT_DEMO_IDS)
    parser.add_argument(
        "--overwrite-generated",
        action="store_true",
        help="allow replacing only the report, chart, and demo-ID output files",
    )
    args = parser.parse_args()
    try:
        mode, results, missing_full, demo_ids = generate(
            args.report,
            args.chart,
            args.demo_ids,
            args.clean,
            args.phone,
            args.pilot,
            args.overwrite_generated,
        )
    except (FileNotFoundError, FileExistsError, ValueError, csv.Error) as error:
        parser.error(str(error))
    print(f"Generated {mode}-mode report: {args.report}")
    print(f"Generated chart: {args.chart}")
    if missing_full:
        print("Full experiment inputs missing: " + ", ".join(missing_full))
    if demo_ids:
        print("Pilot demo IDs: " + ", ".join(demo_ids))
    else:
        print("Analysis-based demo selection unavailable; no demo IDs were invented.")


if __name__ == "__main__":
    main()
