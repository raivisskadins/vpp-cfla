import pandas as pd

def generate_precision_report_html(
    table_html: str,
    total_precision: float,
    total_precision_answered: float,
    total_precision_answered_wo_na: float,
    extra_data
) -> str:
    conf_matrix_html = extra_data["conf_matrix"].to_html(border=1, classes="conf-matrix")

    extra_info_html = f"""
    <h2>Additional Model Evaluation Data</h2>
    <h3>Confusion Matrix</h3>
    {conf_matrix_html}
    <p><strong>Total questions answered:</strong> {extra_data['total_q']}</p>
    <p><strong>Confident answers:</strong> {extra_data['confident_answers']}</p>
    <p><strong>Unanswerable questions (n/a without q0):</strong> {extra_data['unanswerable_count']}</p>
    <p><strong>Total 'jā' answers:</strong> {extra_data['total_yes']}</p>
    <p><strong>Total 'nē' answers:</strong> {extra_data['total_no']}</p>
    <p><strong>Total 'n/a' answers:</strong> {extra_data['total_na']}</p>
    <p><strong>'jā' answer accuracy:</strong> {round(extra_data['yes_accuracy'], 2)}%</p>
    <p><strong>'nē' answer accuracy:</strong> {round(extra_data['no_accuracy'], 2)}%</p>
    <p><strong>'n/a' answer accuracy:</strong> {round(extra_data['na_accuracy'], 2)}%</p>
    """

    report_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Precision Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        th {{ background-color: #f4f4f4; position: relative; }}
        table.sortable th {{ cursor: pointer; }}

        .conf-matrix {{ width: auto; margin-top: 20px; }}

        /* Default neutral sort indicator */
        table.sortable th::after {{
            content: " ▲▼";
            font-size: 0.8em;
            color: #999;
            margin-left: 4px;
        }}

        /* Sorted ascending */
        table.sortable th.asc::after {{
            content: " ▲";
            color: black;
        }}

        /* Sorted descending */
        table.sortable th.desc::after {{
            content: " ▼";
            color: black;
        }}
    </style>
</head>
<body>
    <h1>Total model precision: {total_precision}</h1>
    <h1>Total model precision for answered questions only: {total_precision_answered}</h1>
    <h1>Total model precision for answered questions only and without unobtainable n/a: {total_precision_answered_wo_na}</h1>
    <h1>Model Precision per Question</h1>
    <div class="report-table">
        {table_html}
    </div>
    {extra_info_html}
    <script>
    document.addEventListener('DOMContentLoaded', () => {{
        document.querySelectorAll('table.sortable th').forEach(headerCell => {{
            headerCell.addEventListener('click', () => {{
                const tableElement = headerCell.closest('table');
                const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
                const isAscending = headerCell.classList.contains('asc');
                const directionModifier = isAscending ? -1 : 1;
                const rows = Array.from(tableElement.querySelectorAll('tbody tr'));

                rows.sort((a, b) => {{
                    const aText = a.children[headerIndex].innerText.trim();
                    const bText = b.children[headerIndex].innerText.trim();

                    const aNum = parseFloat(aText);
                    const bNum = parseFloat(bText);

                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return (aNum - bNum) * directionModifier;
                    }}
                    return aText.localeCompare(bText) * directionModifier;
                }});

                while (tableElement.tBodies[0].firstChild) {{
                    tableElement.tBodies[0].removeChild(tableElement.tBodies[0].firstChild);
                }}

                tableElement.tBodies[0].append(...rows);
                tableElement.querySelectorAll('th').forEach(th => th.classList.remove('asc', 'desc'));
                headerCell.classList.toggle('asc', !isAscending);
                headerCell.classList.toggle('desc', isAscending);
            }});
        }});
    }});
    </script>
</body>
</html>"""
    return report_html



def generate_precision_report(input_csv: str, questions_without_q0, extra_data) -> str:
    if not input_csv.exists():
        raise FileNotFoundError(f"Cannot find CSV at {input_csv}")

    df = pd.read_csv(input_csv, keep_default_na=False)

    # Normalize strings for consistent comparison
    df['Atbilde'] = df['Atbilde'].astype(str).str.strip().str.lower()
    df['Sagaidāmā atbilde'] = df['Sagaidāmā atbilde'].astype(str).str.strip().str.lower()

    # Exclude rows that have no expected answer
    valid_mask = df['Sagaidāmā atbilde'] != "?"

    # Also exclude rows with questions that were not answered
    df['answered'] = df['Atbilde'].isin(['jā', 'nē', 'n/a'])

    # Only keep questions that are answered and where expected answer is not n/a without q0
    df['answered_wo_na'] = df['Atbilde'].isin(['jā', 'nē', 'n/a']) & ( ~((df['Nr'].isin(questions_without_q0)) & (df['Sagaidāmā atbilde'] == 'n/a')))

    # Compare answers
    df['correct'] = (df['Atbilde'] == df['Sagaidāmā atbilde']) & valid_mask



    # Preserve original order
    original_order = df['Nr'].drop_duplicates().tolist()

    table_data = (
        df[valid_mask]
        .groupby('Nr')
        .agg(
            total_asked=('correct', 'size'),
            total_answered=('answered', 'sum'),
            total_answered_wo_na=('answered_wo_na', 'sum'),
            n_correct=('correct', 'sum')
        )
        .assign(precision=lambda d: round(d['n_correct'] / d['total_asked'], 2))
        .assign(precision_answered = lambda d: round(d['n_correct'] / d['total_answered'].clip(lower=1), 2))
        .assign(precision_answered_wo_na = lambda d: round(d['n_correct'] / d['total_answered_wo_na'].clip(lower=1), 2))
        .reindex(original_order)
        .reset_index()
    )

    total_asked = table_data['total_asked'].sum()
    total_answered = table_data['total_answered'].sum()
    total_answered_wo_na = table_data['total_answered_wo_na'].sum()
    total_correct = table_data['n_correct'].sum()
    total_precision = round(total_correct / total_asked, 2)
    total_precision_answered = round(total_correct / total_answered, 2)
    total_precision_answered_wo_na = round(total_correct / total_answered_wo_na, 2)


    table_html = table_data.to_html(index=False, classes="sortable")
    precison_report_html = generate_precision_report_html(table_html, total_precision, total_precision_answered, total_precision_answered_wo_na, extra_data)

    return precison_report_html