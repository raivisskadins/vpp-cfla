import re
import html
import pandas as pd
from pathlib import Path
from .utilities import get_questions_without_q0

HTML_STYLE = """
<style>
    table.procurement-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
    }
    table.procurement-table th,
    table.procurement-table td {
        border: 1px solid #ccc;
        padding: 8px 10px;
        text-align: center;
    }
    table.procurement-table th {
        background-color: #f4f4f4;
    }
    tr.expandable {
        cursor: pointer;
        background-color: #fefefe;
    }
    tr.expandable:hover {
        background-color: #f0f0f0;
    }
    tr.details-row {
        display: none;
        background-color: #fcfcfc;
    }
    .question {
        margin: 0.5em 0;
        border: 1px dashed #aaa;
        border-radius: 4px;
        padding: 0.5em;
    }
    .question summary {
        font-size: 1em;
        font-weight: normal;
        cursor: pointer;
        outline: none;
    }
    .question-content p {
        margin: 0.3em 0;
    }
    .mismatch {
        background-color: #ffe6e6;
        border-left: 4px solid #ff4d4d;
        padding: 0.5em;
        border-radius: 4px;
    }
    td.toggle-cell {
        width: 30px;
        font-weight: bold;
        font-size: 1.2em;
        cursor: pointer;
        user-select: none;
    }
    tr.expandable .toggle-icon::before {
        content: "▶";
        transition: transform 0.2s;
        display: inline-block;
    }
    tr.expandable.expanded .toggle-icon::before {
        content: "▼";
    }
    tr.total-row {
        font-weight: bold;
        background-color: #e8f0ff;
    }

    /* --- New styles for readable prompts --- */
    pre.prompt-block {
        white-space: pre-wrap;      /* preserve newlines + wrap long lines */
        word-break: break-word;
        padding: 10px 12px;
        line-height: 1.45;
        font-size: 0.92rem;
        margin: 0.4rem 0 0.8rem 0;
    }
</style>
"""

TOGGLE_SCRIPT = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('tr.expandable').forEach(row => {
        row.addEventListener('click', () => {
            const detailsRow = row.nextElementSibling;
            const isVisible = detailsRow.style.display === 'table-row';
            detailsRow.style.display = isVisible ? 'none' : 'table-row';
            row.classList.toggle('expanded', !isVisible);
        });
    });
});
</script>
"""

# ---------- Helpers to safely render multiline text ----------

def render_multiline_as_pre(text: str) -> str:
    if text is None:
        text = ""
    escaped = html.escape(str(text))  # turns <context> into &lt;context&gt;
    return f"<pre class='prompt-block'>{escaped}</pre>"

# ---------- HTML building ----------

def create_question_details(row) -> str:
    qnum = row["Nr"]
    answer = row["Atbilde"]
    expect = row["Sagaidāmā atbilde"]
    justification = row["Pamatojums"]
    prompt = row["Uzvedne"]

    mismatch_class = "mismatch" if answer != expect else ""
    prompt_html = render_multiline_as_pre(prompt)            # literal text with preserved newlines

    return f"""
    <details class='question {mismatch_class}'>
        <summary>{qnum}: Answer="{answer}" vs Expected="{expect}"</summary>
        <div class='question-content'>
            <p><strong>Pamatojums:</strong></p>
            <div style="text-align: left;">{justification}</div>
            <p><strong>Uzvedne:</strong></p>
            <div style="text-align: left;">{prompt_html}</div>
        </div>
    </details>
    """

def build_main_report_html(input_csv_path: Path, question_dictionary: dict) -> str:
    df = pd.read_csv(input_csv_path, keep_default_na=False, encoding="utf-8")
    questions_wout_0q = get_questions_without_q0(question_dictionary)

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <title>Main Report</title>",
        HTML_STYLE,
        TOGGLE_SCRIPT,
        "</head>",
        "<body>",
        "<table class='procurement-table'>",
        "<thead>",
        "  <tr>",
        "    <th></th>",
        "    <th>Iepirkuma ID</th>",
        "    <th>Precizitāte</th>",
        "    <th>Precizitāte bez kontekstā nav informācijas</th>",
        "    <th>Kopējā iespējamā precizitāte</th>",
        "  </tr>",
        "</thead>",
        "<tbody>"
    ]

    total_correct = 0
    total_answered_correct = 0
    total_possible_correct = 0
    total_question_count = 0
    total_answered = 0
    total_possible = 0

    for procurement_id, group in df.groupby("Iepirkuma ID"):
        is_correct = group["Atbilde"] == group["Sagaidāmā atbilde"]
        question_count = len(group)

        excluded_answers = ["X", "kontekstā nav informācijas"]
        answered_mask = ~group["Atbilde"].isin(excluded_answers)
        is_answered_correct = is_correct & answered_mask

        na_mask = (group["Sagaidāmā atbilde"] == "n/a") & (group["Nr"].isin(questions_wout_0q))
        max_possible_mask = answered_mask & ~na_mask
        is_possible_correct = is_correct & max_possible_mask

        precision = (is_correct.sum() / question_count) if question_count > 0 else 0.0
        answered_sum = int(answered_mask.sum())
        max_possible_sum = int(max_possible_mask.sum())

        precision_answered = (is_answered_correct.sum() / answered_sum) if answered_sum > 0 else 0.0
        max_possible_precision = (is_possible_correct.sum() / max_possible_sum) if max_possible_sum > 0 else 0.0

        total_correct += int(is_correct.sum())
        total_answered_correct += int(is_answered_correct.sum())
        total_possible_correct += int(is_possible_correct.sum())

        total_question_count += question_count
        total_answered += answered_sum
        total_possible += max_possible_sum

        safe_proc_id = html.escape(str(procurement_id))

        html_parts.append(f"""
        <tr class="expandable">
            <td class="toggle-cell"><span class="toggle-icon"></span></td>
            <td>{safe_proc_id}</td>
            <td>{precision * 100:.2f}%</td>
            <td>{precision_answered * 100:.2f}%</td>
            <td>{max_possible_precision * 100:.2f}%</td>
        </tr>
        """)

        questions_html = "\n".join([create_question_details(row) for _, row in group.iterrows()])
        html_parts.append(f"""
        <tr class="details-row">
            <td colspan="5">
                {questions_html}
            </td>
        </tr>
        """)

    # Final totals
    total_precision = (total_correct / total_question_count) if total_question_count > 0 else 0.0
    total_answered_precision = (total_answered_correct / total_answered) if total_answered > 0 else 0.0
    total_max_possible_precision = (total_possible_correct / total_possible) if total_possible > 0 else 0.0

    html_parts.append(f"""
    <tr class="total-row">
        <td></td>
        <td><strong>Kopējā precizitāte</strong></td>
        <td>{total_precision * 100:.2f}%</td>
        <td>{total_answered_precision * 100:.2f}%</td>
        <td>{total_max_possible_precision * 100:.2f}%</td>
    </tr>
    """)

    html_parts.extend([
        "</tbody>",
        "</table>",
        "</body>",
        "</html>"
    ])

    return "\n".join(html_parts)
