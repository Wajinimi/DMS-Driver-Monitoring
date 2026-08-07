"""Generate report figures from the authoritative notebook_run_artefacts metrics.

Every value plotted is read directly from *_metrics.json; nothing is simulated.
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

BASE = "/Users/dell/Library/CloudStorage/OneDrive-hull.ac.uk/MEETING"
ART = os.path.join(BASE, "notebook_run_artefacts")
OUT = os.path.join(BASE, "report_figures")
os.makedirs(OUT, exist_ok=True)

CLASSES = [
    "No Finding",
    "Infiltration",
    "Atelectasis",
    "Effusion",
    "Nodule",
    "Pneumothorax",
    "Mass",
]

# Class order verified against the classification_report string stored in
# notebook_run_artefacts/gan_resnet50_metrics.json (descending prevalence).

SELECTED = {
    "intensity_vgg19": "VGG19 + intensity augmentation",
    "baseline_resnet50": "ResNet50 + baseline (no augmentation)",
    "gan_cnn": "Custom CNN + conditional GAN augmentation",
}

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "savefig.dpi": 300,
        "figure.dpi": 300,
    }
)


def load(name):
    with open(os.path.join(ART, f"{name}_metrics.json")) as fh:
        return json.load(fh)


def curve_figure(metric, filename, ylabel):
    """metric is 'accuracy' or 'loss'; validation series is 'val_' + metric."""
    names = ["intensity_vgg19", "baseline_resnet50"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.05))
    panel = ["(a)", "(b)"]
    handles = None
    for ax, name, tag in zip(axes, names, panel):
        j = load(name)
        h = j["history"]
        tr = np.asarray(h[metric], dtype=float)
        va = np.asarray(h["val_" + metric], dtype=float)
        ep = np.arange(1, len(tr) + 1)
        ax.plot(ep, tr, marker="o", ms=3.5, lw=1.4, color="#1f4e79", label="Training")
        ax.plot(ep, va, marker="s", ms=3.5, lw=1.4, color="#c0392b", label="Validation")

        # Restored checkpoint = epoch of minimum validation loss (see Section 3.6).
        best = int(np.argmin(np.asarray(h["val_loss"], dtype=float))) + 1
        ax.axvline(best, color="0.35", ls="--", lw=1.0)
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo - 0.16 * (hi - lo), hi)
        ax.annotate(
            f"restored epoch {best}",
            xy=(best, ax.get_ylim()[0]),
            xytext=(3, 3),
            textcoords="offset points",
            va="bottom",
            ha="left",
            fontsize=7,
            color="0.25",
        )
        ax.set_xlabel("Epoch")
        ax.set_ylabel(ylabel)
        ax.set_xticks(ep)
        ax.set_title(f"{tag} {SELECTED[name]}")
        handles = ax.get_legend_handles_labels()
    fig.legend(
        *handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(OUT, filename), bbox_inches="tight")
    plt.close(fig)
    print("wrote", filename)


def cm_figure(name, filename):
    j = load(name)
    cm = np.asarray(j["confusion_matrix"], dtype=int)
    row = cm.sum(axis=1, keepdims=True)
    shade = cm / np.maximum(row, 1)
    fig, ax = plt.subplots(figsize=(5.1, 4.2))
    sns.heatmap(
        shade,
        annot=cm,
        fmt="d",
        cmap="Blues",
        vmin=0.0,
        vmax=1.0,
        cbar_kws={"label": "Proportion of true class"},
        linewidths=0.4,
        linecolor="white",
        annot_kws={"size": 6.6},
        xticklabels=CLASSES,
        yticklabels=CLASSES,
        ax=ax,
    )
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("True class")
    m = j["metrics"]
    ax.set_title(
        f"{SELECTED[name]}\nmacro-F1 = {m['f1_macro']:.3f}, accuracy = {m['accuracy']:.3f}",
        fontsize=9,
    )
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, filename), bbox_inches="tight")
    plt.close(fig)
    print("wrote", filename)


if __name__ == "__main__":
    curve_figure("accuracy", "fig2_accuracy_curves.png", "Accuracy")
    curve_figure("loss", "fig3_loss_curves.png", "Cross-entropy loss")
    cm_figure("intensity_vgg19", "fig4_cm_intensity_vgg19.png")
    cm_figure("baseline_resnet50", "fig5_cm_baseline_resnet50.png")
    cm_figure("gan_cnn", "fig6_cm_gan_cnn.png")
