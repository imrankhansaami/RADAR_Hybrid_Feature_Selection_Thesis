"""Generate all thesis diagrams as PNGs (simple box style like the old thesis)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
os.makedirs(OUT, exist_ok=True)

GREEN = '#C6E0B4'
BLUE = '#BDD7EE'
YELLOW = '#FFE699'
ORANGE = '#F8CBAD'
GRAY = '#D9D9D9'
EDGE = '#404040'


def new_ax(w_in, h_in, xlim=(0, 100), ylim=(0, 100)):
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=200)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    return fig, ax


def box(ax, x, y, w, h, text, fc=GREEN, fontsize=9.5, bold=False, radius=1.6):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle=f'round,pad=0,rounding_size={radius}',
                       linewidth=0.9, edgecolor=EDGE, facecolor=fc)
    ax.add_patch(p)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold' if bold else 'normal', wrap=True)


def rbox(ax, x, y, w, h, text, fc=GREEN, fontsize=9.5, bold=False):
    p = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                       boxstyle='square,pad=0', linewidth=0.9,
                       edgecolor=EDGE, facecolor=fc)
    ax.add_patch(p)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold' if bold else 'normal')


def arrow(ax, x1, y1, x2, y2, text=None, fontsize=8.5, rad=0.0, color=EDGE):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=11,
                        linewidth=0.9, color=color,
                        connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(a)
    if text:
        ax.text((x1 + x2) / 2 + 2, (y1 + y2) / 2, text, fontsize=fontsize,
                ha='left', va='center')


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, facecolor='white')
    plt.close(fig)
    print('saved', path)


# ---------------------------------------------------------------- Fig 1.1
fig, ax = new_ax(6.4, 1.85)
xs = [1, 20.5, 40.5, 61.5, 81.5, 99]
labels = ['RADAR Sysmon\nEvent Dataset', 'Preprocessing\nand Split',
          'Feature Selection\nFS-A / FS-B / FS-C',
          'Detection Models\n7 Classical + A2G-PTH', 'Evaluation\nand Reporting']
colors = [BLUE, GRAY, GREEN, YELLOW, ORANGE]
w, h = 17.5, 11
centers = [10, 30.5, 50.5, 71.5, 91.5]
for cx, lb, fc in zip(centers, labels, colors):
    box(ax, cx, 55, w, 26, lb, fc=fc)
for a, b in zip(centers[:-1], centers[1:]):
    arrow(ax, a + w / 2 + 0.6, 55, b - w / 2 - 0.6, 55)
ax.text(50.5, 13, 'Feature selection is the core of the study; the models evaluate the selected subsets.',
        ha='center', va='center', fontsize=8.5, style='italic')
save(fig, 'fig1_1_framework.png')

# ---------------------------------------------------------------- Fig 2.1
fig, ax = new_ax(6.4, 3.6)
box(ax, 50, 92, 30, 11, 'Feature Selection\nMethods', fc=BLUE, bold=True)
cats = [(13, 'Filter\nMethods', GREEN), (38, 'Wrapper\nMethods', YELLOW),
        (63, 'Embedded\nMethods', ORANGE), (88, 'Hybrid (Voting /\nRanking) Methods', GREEN)]
for cx, lb, fc in cats:
    box(ax, cx, 68, 20, 15, lb, fc=fc)
    arrow(ax, 50, 86.5, cx, 68 + 7.5)
    # children
subs = {
    13: ['Mutual\nInformation', 'ANOVA\nF-test', 'Chi-square', 'Pearson\ncorrelation'],
    38: ['RFE with\nLogistic\nRegression'],
    63: ['LASSO'],
    88: ['FS-A: consensus\nvoting', 'FS-B: percentage\nsweep', 'FS-C: voting-\nranked sweep'],
}
for cx, lb, fc in cats:
    items = subs[cx]
    n = len(items)
    y0 = 40
    step = 16
    if n == 1:
        ys = [y0]
    elif n == 4:
        ys = [52, 38, 24, 10]
    else:
        ys = [48, 30, 12]
    for i, (item, yy) in enumerate(zip(items, ys)):
        box(ax, cx, yy, 21, 12.5, item, fc='white', fontsize=8.5)
        if i == 0:
            arrow(ax, cx, 68 - 7.5, cx, yy + 6.5)
save(fig, 'fig2_1_taxonomy.png')

# ---------------------------------------------------------------- Fig 2.2
fig, ax = new_ax(6.0, 4.3)
box(ax, 50, 93, 60, 10, 'Training feature matrix (d features, label y)', fc=BLUE)
box(ax, 50, 75, 76, 10.5,
    'Score every feature with four methods:\nMutual Information, ANOVA F-test, RFE (Logistic Regression), Pearson |r|', fc=GREEN)
box(ax, 50, 57, 76, 10.5,
    'Each method casts one vote for a feature\nwhen its score exceeds the mean of that method\u2019s own scores\n(RFE: a vote when the feature survives; a retained feature gets rank 1)', fc=GREEN, fontsize=8.5)
box(ax, 50, 39, 62, 9.5, 'Voting ratio = votes / 4;\nkeep features with ratio \u2265 \u03b8  (\u03b8 = 0.5)', fc=YELLOW)
box(ax, 20, 18, 34, 9.5, 'Yes: selected subset (FS-A)', fc='white')
box(ax, 76, 18, 40, 9.5, 'No feature reaches \u03b8:\nkeep all features (fallback)', fc='white')
arrow(ax, 50, 88, 50, 80.5)
arrow(ax, 50, 69.5, 50, 62.5)
arrow(ax, 50, 51.5, 50, 44)
arrow(ax, 37, 34.5, 22, 23.5, text='Yes')
arrow(ax, 63, 34.5, 74, 23.5, text='No')
save(fig, 'fig2_2_voting.png')

# ---------------------------------------------------------------- Fig 2.3
fig, ax = new_ax(6.0, 4.3)
box(ax, 50, 93, 70, 10, 'Score every feature: \u03c7\u00b2, ANOVA F-test and Mutual Information\n(\u03c7\u00b2 computed on Min-Max scaled data)', fc=GREEN)
box(ax, 50, 74, 70, 9.5, 'Min-Max normalise each score to [0, 1];\ncombined score S\u1d62 = average of the three normalised scores', fc=GREEN)
box(ax, 50, 55, 78, 11, 'Rank features by S\u1d62 (FS-B)\nor by total votes with S\u1d62 as tie-breaker (FS-C)', fc=BLUE)
box(ax, 50, 37, 70, 10, 'Sweep p = 10 %, 20 %, \u2026, 100 %:\nkeep the top d \u00d7 p features (rounded down)', fc=YELLOW)
box(ax, 50, 19, 70, 10, 'Validate every subset (cross-validation inside the training set);\nselect the smallest subset within one standard error of the best', fc='white')
for y1, y2 in [(88, 78.8), (69, 60.5), (49.5, 42), (32, 24)]:
    arrow(ax, 50, y1, 50, y2)
save(fig, 'fig2_3_sweep.png')

# ---------------------------------------------------------------- Fig 2.4
fig, ax = new_ax(6.4, 4.8)
# encoder column
box(ax, 30, 95, 34, 8, 'Input x: k selected features', fc=BLUE, bold=True)
box(ax, 30, 82.5, 40, 9, 'Dense 512, ReLU\nDropout 0.3, BatchNorm', fc=GREEN, fontsize=8.5)
box(ax, 30, 70.5, 40, 9, 'Dense 256, ReLU\nDropout 0.3', fc=GREEN, fontsize=8.5)
box(ax, 30, 58.5, 40, 9, 'Dense 128, ReLU\nDropout 0.2', fc=GREEN, fontsize=8.5)
box(ax, 30, 46, 44, 9, 'Attention: \u03b1 = softmax(tanh(W\u00b7h + b))\nh\u2090\u209c\u209c = h \u00b7 \u03b1  (128 units)', fc=YELLOW, fontsize=8.5)
box(ax, 30, 33, 30, 8.5, 'Latent z = ReLU(W\u00b7h\u2090\u209c\u209c + b)\n(64 units)', fc=ORANGE, fontsize=8.5)
# decoder below
box(ax, 30, 17, 42, 12, 'Decoder: Dense 128 \u2192 256 \u2192 512,\nsigmoid output of size k; MSE loss\n(reconstruction error = anomaly score)', fc=GRAY, fontsize=8.5)
# discriminator right
box(ax, 79, 76, 38, 12, 'Discriminator:\nDense 256 \u2192 128 \u2192 64 \u2192 1,\nsigmoid; BCE loss', fc=YELLOW, fontsize=8.5)
box(ax, 79, 60, 30, 9, 'Real: encoder latents\nFake: N(0, I\u2086\u2084) samples', fc='white', fontsize=8.5)
box(ax, 79, 40, 40, 12, 'Graph: edge when cosine\nsimilarity of latents > 0.7\n(sparse adjacency)', fc=BLUE, fontsize=8.5)
box(ax, 79, 20, 40, 14, 'GNN classifier:\nDense 128, 128 (dropout 0.3),\nhead 64 (dropout 0.2),\nsoftmax over K = 2 classes', fc=GREEN, fontsize=8.5)
arrow(ax, 30, 91, 30, 87)
arrow(ax, 30, 78, 30, 75)
arrow(ax, 30, 66, 30, 63)
arrow(ax, 30, 54, 30, 50.5)
arrow(ax, 30, 41.5, 30, 37.5)
arrow(ax, 30, 28.5, 30, 23)
arrow(ax, 44, 34.5, 64, 58, rad=-0.22, text='z', fontsize=8.5)
arrow(ax, 44, 31, 59, 38, rad=0.18, text='latents', fontsize=8.5)
arrow(ax, 79, 70, 79, 64.5)
arrow(ax, 79, 34, 79, 27)
save(fig, 'fig2_4_a2gpth.png')

# ---------------------------------------------------------------- Fig 4.1
fig, ax = new_ax(6.4, 4.6)
box(ax, 50, 95, 46, 8, 'RADAR engineered events\n(audit, \u00b1\u221e \u2192 NaN, deduplicate)', fc=BLUE)
box(ax, 50, 81, 54, 8, 'Split: P1 random / P2 grouped by sample / P3 chronological', fc=GRAY)
box(ax, 26, 62, 44, 9.5, 'Training set only (train):\nbalancing \u2192 Min-Max fit \u2192 feature scores on train', fc=GREEN, fontsize=8.5)
box(ax, 76, 62, 42, 9.5, 'Test set (kept at natural prevalence):\napply train Min-Max statistics', fc=YELLOW, fontsize=8.5)
box(ax, 26, 45, 46, 11.5, 'Build subsets on train only:\nFS-A (voting), FS-B (sweep), FS-C (voting-ranked sweep);\nchoose p by cross-validation, never on test', fc=GREEN, fontsize=8.5)
box(ax, 26, 26.5, 46, 10.5, 'Train and tune: 7 classical classifiers +\nA2G-PTH (validation inside train)', fc=GREEN, fontsize=8.5)
box(ax, 76, 26.5, 42, 14, 'Evaluate once on the untouched test set:\naccuracy, precision, recall, F1, ROC-AUC,\nPR-AUC, F2, specificity, FPR, FNR,\nconfusion matrix, time, model size', fc=YELLOW, fontsize=8.5)
arrow(ax, 50, 91, 50, 85)
arrow(ax, 34, 77, 28, 67)
arrow(ax, 66, 77, 74, 67)
arrow(ax, 26, 57.2, 26, 51)
arrow(ax, 26, 39.2, 26, 32)
arrow(ax, 48, 26.5, 55, 26.5)
ax.text(50, 8, 'Selection leakage control: every score, threshold and subset is computed on training data only.',
        ha='center', va='center', fontsize=8.5, style='italic')
save(fig, 'fig4_1_pipeline.png')

print('all figures done')
