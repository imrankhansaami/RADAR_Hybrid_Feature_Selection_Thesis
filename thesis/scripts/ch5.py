"""Chapter 5: Conclusion and future work."""
from lib import add_para, chapter_heading, h2


def build(doc, st):
    chapter_heading(doc, 'Chapter 5: Conclusion', page_break_before=True)
    add_para(doc,
             'This thesis studied feature selection for ransomware detection on '
             'Sysmon host events. It is a feature-selection study first: the '
             'classification models are used to evaluate the subsets that the '
             'selectors keep, not to compete for the highest accuracy on a benchmark. '
             'The study took two published ideas from the reference papers \u2014 the '
             'consensus voting of [1] and the percentage sweep with a combined score '
             'of [2] \u2014 re-implemented both on the RADAR dataset [3] with every '
             'threshold recomputed from RADAR training scores, and linked them in the '
             'proposed voting-ranked sweep (FS-C), which ranks features by consensus '
             'votes and then applies the percentage sweep of the combined score.')
    add_para(doc,
             'The contribution of the work is practical and documented. First, the '
             'voting selector is turned from a set of printed constants that cannot '
             'be reproduced from the source paper into a verified procedure whose '
             'vote table is a result of this study. Second, the two selection '
             'strategies, voting and the percentage sweep, are compared on the same '
             'host-event data with identical subset sizes, so the comparison is '
             'controlled by construction. Third, the subsets are assessed not only '
             'by detection quality with the seven classical models of [1] and the '
             'A2G-PTH deep model of [2], but also by agreement and stability across '
             'folds and seeds, and under a leakage-aware group split in which no '
             'ransomware sample appears on both sides of the evaluation. Fourth, the '
             'reproducibility issues found in the two source papers are collected and '
             'resolved one by one in Section 4.1, so that the differences between '
             'this study and the sources are explicit.')
    add_para(doc,
             'The results of the runs are reported in the tables of Section 4.2 and '
             'answer the research questions of Section 1.4: the size and detection '
             'quality of the voting subset (RQ1), the shape of the sweep curve and '
             'the smallest subset within one standard error of the best validation '
             'score (RQ2), the difference between the vote-based and score-based '
             'rankings (RQ3), the stability of the kept subsets (RQ4), the transfer '
             'of the subsets to the deep adversarial graph model (RQ5), the gap '
             'between the random and leakage-aware splits (RQ6), and the cost saved '
             'by the selected subsets (RQ7).')
    add_para(doc,
             'Several limitations qualify these results. The study covers one dataset '
             'family collected on one laboratory setup (Windows 11, Sysmon), so '
             'generalisation to other environments is not claimed. The engineered '
             'features describe single events and their local context, not event '
             'sequences, so the temporal order of a ransomware execution is outside '
             'the model; the Drift variant partially exposes time through its phases '
             'and is evaluated as a separate experiment, but its phase-boundary '
             'files are not part of the processed data, so the drift check uses a '
             'chronological split. A sizeable share of rows '
             'belongs to feature vectors that carry both labels, which bounds the '
             'accuracy that any model can reach and is reported with every result. '
             'The deep evaluator is faithful to the configuration of [2] in its '
             'architecture, but epochs, optimiser and learning rate are not reported '
             'in the source paper and were therefore chosen on validation data and '
             'documented; the compact variant is marked as such wherever it is '
             'reported. Finally, the comparisons against the published numbers of '
             '[1] and [2] are made with the caveats documented in Section 4.1, '
             'because both papers evaluate in other domains with single splits.')

    h2(doc, '5.1  Future Work')
    add_para(doc,
             'The findings of this study suggest several directions for future work:')
    from lib import add_bullets
    add_bullets(doc, [
        'Temporal modelling: replacing the per-event rows with short event windows '
        'or sequences (for example process trees or time-ordered Sysmon traces) and '
        're-running the selection study on window-level features.',
        'Dynamic graph selection: learning the similarity threshold of the A2G-PTH '
        'graph (0.7 in [2]) instead of fixing it, and rebuilding the graph over time '
        'so that drift in the event population is reflected in the neighbourhoods.',
        'Continual and drift-aware learning: evaluating the selected subsets under '
        'the phase structure of the Drift file with rolling retraining, and measuring '
        'how often the kept subset must be refreshed.',
        'Additional feature spaces: extending the comparison to the FastText feature '
        'family shipped with RADAR, and to window-level aggregates over the raw '
        'Sysmon fields, since the engineered set is only one possible view of the '
        'telemetry.',
        'Family-level analysis: using the sample and family labels to run the '
        'multiclass variant on the Drift file, which would show whether the selected '
        'features separate specific ransomware families as well as the binary '
        'ransomware-vs-goodware split.',
        'Broader evidence: repeating the protocols on other host-telemetry datasets '
        'and other operating systems, and adding deep baselines (sequence models) '
        'once a justified sequence definition exists, as discussed in Section 4.1.',
        'Deployment-oriented work: compressing the deep evaluator for on-device use, '
        'calibrating alert thresholds on validation data, and studying the '
        'alert-fatigue trade-offs of the recall-oriented metrics (F2, FPR, FNR) '
        'reported in this thesis.',
    ])
