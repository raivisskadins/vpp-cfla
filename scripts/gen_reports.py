import pandas as pd

def generate_precision_report_html(table_html: str, total_precision: float) -> str:
    report_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Precision Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        th {{ background-color: #f4f4f4; cursor: pointer; position: relative; }}

        /* Default neutral sort indicator */
        th::after {{
            content: " ▲▼";
            font-size: 0.8em;
            color: #999;
            margin-left: 4px;
        }}

        /* Sorted ascending */
        th.asc::after {{
            content: " ▲";
            color: black;
        }}

        /* Sorted descending */
        th.desc::after {{
            content: " ▼";
            color: black;
        }}
    </style>
</head>
<body>
    <h1>Total model precision: {total_precision}</h1>
    <h1>Model Precision per Question</h1>
    {table_html}
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

def generate_precision_report(input_csv: str) -> str:
    if not input_csv.exists():
        raise FileNotFoundError(f"Cannot find CSV at {input_csv}")

    df = pd.read_csv(input_csv)

    # Normalize strings for consistent comparison
    df['Atbilde'] = df['Atbilde'].astype(str).str.strip().str.lower()
    df['Sagaidāmā atbilde'] = df['Sagaidāmā atbilde'].astype(str).str.strip().str.lower()

    # Exclude rows that have no expected answer
    valid_mask = df['Sagaidāmā atbilde'] != "?"

    # Compare answers
    df['correct'] = (df['Atbilde'] == df['Sagaidāmā atbilde']) & valid_mask

    # Preserve original order
    original_order = df['Nr'].drop_duplicates().tolist()

    table_data = (
        df[valid_mask]
        .groupby('Nr')
        .agg(
            total_asked=('correct', 'size'),
            n_correct=('correct', 'sum')
        )
        .assign(precision=lambda d: round(d['n_correct'] / d['total_asked'], 2))
        .reindex(original_order)
        .reset_index()
    )

    total_asked = table_data['total_asked'].sum()
    total_correct = table_data['n_correct'].sum()
    total_precision = round(total_correct / total_asked, 2)

    table_html = table_data.to_html(index=False, classes="sortable")
    precison_report_html = generate_precision_report_html(table_html, total_precision)

    return precison_report_html