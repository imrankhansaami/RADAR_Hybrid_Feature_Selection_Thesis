"""Chapter 1: Introduction."""
import os
from lib import add_para, chapter_heading, add_figure, add_bullets, h2

FIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')


def build(doc, st):
    chapter_heading(doc, 'Chapter 1: Introduction')
    add_para(doc,
             'Ransomware is a class of malicious software that denies access to a '
             'victim\u2019s data, typically by encrypting files and demanding a payment '
             'for their release. Modern ransomware families act quickly: they delete '
             'local snapshots and backups, change file creation timestamps and delete '
             'archived copies of documents, so that restoring data without paying '
             'becomes hard. On the defence side, every one of these actions leaves '
             'traces in the Windows event log, and the System Monitor service (Sysmon) '
             'records them as structured events about process creation, file activity, '
             'registry changes and network connections.')
    add_para(doc,
             'A detector built on Sysmon events does not observe the malware directly; '
             'it observes features engineered from the events. Only some of these '
             'features separate malicious from benign activity, and different feature '
             'selection strategies keep different subsets of them. This thesis studies '
             'that selection step on the RADAR dataset [3], a recent collection of '
             'Sysmon events recorded from goodware and ransomware executions, and it '
             'compares two published selection ideas: a hybrid consensus voting '
             'selector [1] and a percentage-sweep selector driven by a combined '
             'chi-square, F-test and mutual information score [2]. Figure 1.1 shows the '
             'overall framework of the study.')
    add_figure(doc, os.path.join(FIGDIR, 'fig1_1_framework.png'),
               'Fig 1.1: Framework of the proposed study', width_cm=15.0)

    h2(doc, '1.1  Project Overview')
    add_para(doc,
             'This thesis builds and compares three feature selectors for event-level '
             'ransomware detection. FS-A re-implements the hybrid voting selector of '
             '[1]: mutual information, the ANOVA F-test, recursive feature elimination '
             'and Pearson correlation each score the training features, each method '
             'votes for the features that stand out with respect to its own score '
             'distribution, and a feature is kept when the voting ratio reaches a '
             'consensus threshold. FS-B implements the percentage sweep of [2]: '
             'features are scored with chi-square, the F-test and mutual information, '
             'the three scores are normalised and averaged into a single combined '
             'score, and the top ten, twenty, and so on up to one hundred percent of '
             'the ranked features are kept as candidate subsets. FS-C is proposed in '
             'this thesis: features are ranked by the votes of FS-A, ties are broken '
             'with the combined score of FS-B, and the same percentage sweep is '
             'applied, so that both selection ideas can be compared on subsets of '
             'identical sizes.')
    add_para(doc,
             'The three selectors are first assessed as selectors: how many features '
             'each one keeps, how strongly they agree with each other, and how stable '
             'the kept subsets are across cross-validation folds and random seeds. The '
             'selected subsets are then evaluated as feature sets for detection. Seven '
             'classical classifiers (logistic regression, k-nearest neighbours, naive '
             'Bayes, a decision tree, a random forest, XGBoost and AdaBoost) and an '
             'adversarial autoencoder graph neural network model (A2G-PTH, adapted from '
             '[2]) are trained on each subset, under a paper-faithful random split and '
             'under a leakage-aware group split in which no ransomware sample appears '
             'on both sides. The study reports detection quality on the rare '
             'ransomware class, the gap between the two splits, and the computational '
             'cost of every configuration.')

    h2(doc, '1.2  Motivation')
    add_para(doc,
             'Ransomware has developed into one of the most damaging cyber threats. In '
             'its 2025 threat reports, the security industry records continued growth '
             'in ransomware incidents, multi-million dollar payment demands and a '
             'strong shift towards double extortion, where data is stolen before it is '
             'encrypted [31], [32]. Detection research therefore studies behavioural '
             'telemetry, and Sysmon has become a standard source of such telemetry on '
             'Windows hosts.')
    add_para(doc,
             'Sysmon records thousands of events per execution, and the engineered '
             'features computed from them are partly redundant: an event action flag '
             'and its event category flag often describe the same activity, and several '
             'path statistics correlate with each other. Feeding everything to a '
             'classifier inflates training cost, hides which features carry the signal '
             'and can hurt detection when the classes are imbalanced, which is exactly '
             'the situation in ransomware detection, where malicious events are the '
             'minority. A compact, justified subset that preserves recall on the '
             'ransomware class is therefore more useful than the full feature set.')
    add_para(doc,
             'The two source papers define the two main strategies this thesis '
             'compares, but each was evaluated in a different domain: [1] votes over '
             'network-flow features from the LUFlow dataset [4], and [2] sweeps the '
             'retained percentage for one deep model on the ACI IoT dataset [5]. Their '
             'thresholds and sweep results are not reproducible from the papers '
             'themselves, and neither paper tests host-based ransomware events, subset '
             'stability across resamples, or evaluation protocols that control data '
             'leakage on block-structured data such as RADAR. These gaps motivate a '
             'verified re-implementation of both selectors on one common host-event '
             'dataset, a direct comparison between them, and a stability and '
             'leakage-aware assessment of the subsets they keep.')

    h2(doc, '1.3  Objectives')
    add_para(doc, 'The specific objectives of this study are:', space_after=4)
    add_bullets(doc, [
        'To re-implement the hybrid voting selector of [1] (FS-A) on RADAR, with '
        'every threshold recomputed from the RADAR training scores instead of reusing '
        'the values stated in the paper.',
        'To implement the percentage-sweep selector of [2] (FS-B) with its combined '
        'chi-square, F-test and mutual information score, computed for every feature.',
        'To propose and test a voting-ranked percentage sweep (FS-C) that ranks '
        'features by consensus votes and then applies the same percentage sweep.',
        'To assess the subsets kept by the three selectors in terms of subset size, '
        'agreement between the selectors, and stability across folds and seeds.',
        'To evaluate the subsets with the seven classical models of [1] and the '
        'A2G-PTH deep model of [2], under a paper-faithful split and a leakage-aware '
        'group split.',
        'To measure and report the computational cost (selection time, training time, '
        'prediction time and model size) of every configuration.',
    ])

    h2(doc, '1.4  Methodology')
    add_para(doc,
             'The methodology follows the working plan of this project. The primary '
             'data is the RADAR engineered event file with about ten percent ransomware '
             '(Imbalanced-10), with the harder Imbalanced-5 file and the Drift file as '
             'secondary experiments. Exact duplicate rows are removed before the split; '
             'class balancing, Min-Max scaling and all feature scores are computed on '
             'training data only. Three protocols are used: a stratified random split '
             '(P1, the paper-faithful baseline), a group split on the ransomware sample '
             'identifier so that no sample appears on both sides (P2, the main validity '
             'result), and a chronological split of the time-ordered Drift file '
             '(P3; the phase-boundary files are not part of the processed data, so '
             'the split is chronological rather than phase-labelled). '
             'The retained percentage of the sweep is chosen by cross-validation inside '
             'the training set, and every configuration is repeated over several random '
             'seeds with mean and standard deviation reported.')
    add_para(doc, 'The study answers the following research questions:', space_after=4)
    add_bullets(doc, [
        'RQ1: Does hybrid voting (FS-A) keep a much smaller subset with detection '
        'performance close to that of all features?',
        'RQ2: How does performance change as the retained percentage moves from ten '
        'to one hundred percent, and is there a stable minimum-size subset (FS-B)?',
        'RQ3: Does ranking by votes (FS-C) differ from ranking by the combined score '
        '(FS-B) in the subsets it keeps and in the performance it yields?',
        'RQ4: How stable are the selected subsets across folds, seeds and selectors?',
        'RQ5: Do subsets chosen with the classical models hold up for the A2G-PTH '
        'deep model?',
        'RQ6: How large is the gap between a random split and a leakage-aware split?',
        'RQ7: What do the selected subsets save in training time, prediction time and '
        'model size?',
    ])

    h2(doc, '1.5  Project Outcome')
    add_para(doc,
             'The expected outcomes of the study are: a verified re-implementation of '
             'the voting selector of [1] with a documented correction of its '
             'inconsistent thresholds; a side-by-side comparison of consensus voting '
             'and percentage-sweep selection on host-based ransomware events; the '
             'voting-ranked sweep (FS-C) that links the two papers\u2019 ideas; a '
             'stability and agreement analysis of the three selectors together with a '
             'leakage-aware evaluation of their subsets using classical and deep '
             'models; and a documented list of the inconsistencies found in the two '
             'source papers and how each one was resolved. All result tables in this '
             'report are produced by our own runs of the pipeline described in '
             'Chapter 4, and the code, configuration files and logs accompany this '
             'report.')
    add_para(doc,
             'The remainder of this report is organised as follows. Chapter 2 '
             'introduces the background: ransomware telemetry, feature selection '
             'concepts and scoring measures, the three selectors, the evaluation '
             'models and the metrics. Chapter 3 reviews the related literature and '
             'positions this study. Chapter 4 describes the implementation and the '
             'experimental design, and reports the results of the study. Chapter 5 '
             'concludes and discusses future work.')
