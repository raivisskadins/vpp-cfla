# pip install --upgrade gradio
import gradio as gr
import time


def evaluate_procurement(procurement_file, agreement_file):
    yield f"Iepirkums tiek vērtēts failiem:\n{procurement_file}\n{agreement_file}"

    # TODO call the assesment script
    time.sleep(3)

    yield "REZULTĀTI: ..."


# Create Gradio UI
with gr.Blocks(title="Iepirkumi") as form:
    gr.Markdown("## Iepirkumu dokumentācijas vērtēšana")

    with gr.Row():
        procurement_file = gr.Textbox(label="Iepirkumu fails (.docx vai .pdf)")
        agreement_file = gr.Textbox(
            label="Līguma projekta fails (ja tas ir atsevišķā failā)  (.docx vai .pdf)"
        )

    submit = gr.Button("Vērtēt iepirkumu")
    output = gr.Textbox(label="Rezultāti")

    submit.click(
        fn=evaluate_procurement,
        inputs=[procurement_file, agreement_file],
        outputs=output,
    )

form.launch()
