"""Export the MSc report docx to markdown so the text copy stays in sync."""

import os

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

BASE = "/Users/dell/Library/CloudStorage/OneDrive-hull.ac.uk/MEETING"
DOCX = os.path.join(BASE, "MSc_Research_Project_Report_GAN_CXR.docx")
OUT = os.path.join(BASE, "MSc_Research_Project_Report_GAN_CXR.md")

FIGURE_IMAGES = [
    "Experiment_Workflow_Diagram.png",
    "report_figures/fig2_accuracy_curves.png",
    "report_figures/fig3_loss_curves.png",
    "report_figures/fig4_cm_intensity_vgg19.png",
    "report_figures/fig5_cm_baseline_resnet50.png",
    "report_figures/fig6_cm_gan_cnn.png",
]


def iter_block_items(doc):
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[1]
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def main():
    doc = Document(DOCX)
    lines = []
    image_index = 0
    for block in iter_block_items(doc):
        if isinstance(block, Table):
            rows = [[c.text.strip() for c in r.cells] for r in block.rows]
            lines.append("| " + " | ".join(rows[0]) + " |")
            lines.append("|" + "---|" * len(rows[0]))
            for row in rows[1:]:
                lines.append("| " + " | ".join(row) + " |")
            lines.append("")
            continue

        text = block.text.strip()
        if "blip" in block._p.xml and not text:
            path = FIGURE_IMAGES[image_index]
            image_index += 1
            lines.append(f"![Figure {image_index}]({path})")
            lines.append("")
            continue
        if not text:
            continue

        style = block.style.name
        bold = bool(block.runs) and block.runs[0].bold
        italic = bool(block.runs) and block.runs[0].italic
        if style == "Title":
            lines.append(f"# {text}")
        elif style == "Heading 1":
            lines.append(f"## {text}")
        elif text.startswith("Keywords:"):
            lines.append(f"**{text}**")
        elif bold:
            lines.append(f"### {text}")
        elif italic:
            lines.append(f"*{text}*")
        else:
            lines.append(text)
        lines.append("")

    with open(OUT, "w") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    print("wrote", OUT, f"({image_index} figures)")


if __name__ == "__main__":
    main()
