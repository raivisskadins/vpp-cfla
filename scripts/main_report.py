# main_report.py
import pandas as pd
from pathlib import Path


def build_main_report_html(input_csv_path: Path) -> str:
    """
    Generate the main HTML report from a CSV file.
    :param input_csv_path: Path to the CSV report file.
    :return: HTML string for the main report.
    """
    df = pd.read_csv(input_csv_path, keep_default_na=False, encoding="utf-8")
    html = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <title>Main Report</title>",
        "  <style>",
        "    details.procurement {",
        "      margin-bottom: 1em;",
        "      border: 1px solid #888;",
        "      border-radius: 4px;",
        "      padding: 0.5em;",
        "    }",
        "    summary.procurement {",
        "      font-size: 1.2em;",
        "      font-weight: bold;",
        "      cursor: pointer;",
        "      outline: none;",
        "    }",
        "    details.question {",
        "      margin: 0.5em 0;",
        "      border: 1px dashed #aaa;",
        "      border-radius: 4px;",
        "      padding: 0.5em;",
        "    }",
        "    summary.question {",
        "      font-size: 1em;",
        "      font-weight: normal;",
        "      cursor: pointer;",
        "      outline: none;",
        "    }",
        "    .question-content p {",
        "      margin: 0.3em 0;",
        "    }",
        "  </style>",
        "</head>",
        "<body>"
    ]

    for procurement_id, group in df.groupby("Iepirkuma ID"):
        precision = (group["Atbilde"] == group["Sagaidāmā atbilde"]).mean()
        proc_summary = (
            f"Iepirkuma ID: {procurement_id} — "
            f"Precision: {precision*100:.2f}%"
        )

        html.append(f"<details class='procurement'>")
        html.append(f"  <summary class='procurement'>{proc_summary}</summary>")
        html.append("  <div class='questions'>")

        for _, row in group.iterrows():
            qnum          = row["Nr"]
            answer        = row["Atbilde"]
            expect        = row["Sagaidāmā atbilde"]
            justification = row["Pamatojums"]
            chunk         = row["Chunk"]
            prompt        = row["Prompt"]

            q_summary = f"{qnum}: Answer=\"{answer}\" vs Expected=\"{expect}\""
            html.append(f"    <details class='question'>")
            html.append(f"      <summary class='question'>{q_summary}</summary>")
            html.append("      <div class='question-content'>")
            html.append(f"        <p><strong>Pamatojums:</strong> {justification}</p>")
            html.append(f"        <p><strong>Chunk:</strong> {chunk}</p>")
            html.append(f"        <p><strong>Prompt:</strong> {prompt}</p>")
            html.append("      </div>")
            html.append("    </details>")

        html.append("  </div>")
        html.append("</details>")

    html.extend([
        "</body>",
        "</html>"
    ])
    return "\n".join(html)


def main():
    """
    When run as a script, generate the main report for a hard-coded subdirectory.
    """
    project_root       = Path(__file__).parent.parent
    # TODO: replace with argparse or environment variable if you need dynamic subdirs
    report_folder_name = "dev-test_07.07"

    input_csv = project_root / "reports" / report_folder_name / "report.csv"
    if not input_csv.is_file():
        raise FileNotFoundError(f"report.csv not found at {input_csv}")

    html_output = build_main_report_html(input_csv)
    output_path = project_root / "reports" / report_folder_name / "main_report.html"
    output_path.write_text(html_output, encoding="utf-8")
    print(f"HTML report saved to: {output_path}")


if __name__ == "__main__":
    main()
