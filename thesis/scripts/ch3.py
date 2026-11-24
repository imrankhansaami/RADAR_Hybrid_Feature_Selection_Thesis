"""Chapter 3: Review of the Literature."""
import os
from lib import add_para, chapter_heading, h2, add_table

FIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')


def build(doc, st):
    chapter_heading(doc, 'Chapter 3: Review of the Literature', page_break_before=True)
    add_para(doc,
             'This chapter reviews the research this thesis builds upon. Section 3.1 '
             'states the scope of the review and how the material was selected. '
             'Section 3.2 discusses machine learning for ransomware and intrusion '
             'detection, feature selection for security telemetry, ensemble and '
             'hybrid selection, graph and autoencoder models, and the two reference '
             'papers in detail. Section 3.3 summarises the gaps that motivate this '
             'study.')

    h2(doc, '3.1  Preliminaries')
    add_para(doc,
             'The review covers three lines of work: (i) machine learning for '
             'ransomware detection on host telemetry, (ii) feature selection and '
             'ensemble selection for intrusion and malware detection, and (iii) deep '
             'models that use autoencoders and graphs for anomaly and intrusion '
             'detection. Within these lines, the two reference papers [1] and [2] and '
             'the RADAR dataset [3] are treated as primary sources, and the studies '
             'cited by the two papers are used as secondary sources. The criteria for '
             'including a study were: a published description of the feature '
             'selection procedure or of the detection model; an evaluation on a '
             'publicly extractable dataset; and relevance to at least one of the '
             'three lines above. Work that reports only detection accuracy without a '
             'selection step or without host-event telemetry is mentioned briefly for '
             'context.')

    h2(doc, '3.2  Literature Review')
    add_para(doc,
             '**Machine learning for ransomware detection.** Machine learning '
             'approaches to ransomware detection use either static file properties or '
             'dynamic behaviour. Behaviour-based detection monitors system calls, '
             'file operations, registry changes and network traffic during execution, '
             'which survives packing and obfuscation and fits the way modern '
             'ransomware acts. Host telemetry studies show that classic supervised '
             'models trained on carefully engineered event features remain strong '
             'baselines: random forests, gradient-boosted trees and simple linear '
             'models reach competitive recall on ransomware events once the features '
             'capture process, path and file behaviour rather than raw byte patterns '
             '[3], [6]. The difficulty that re-appears across these studies is class '
             'imbalance and the repetitive structure of event logs: benign activity '
             'dominates, many events repeat, and the interesting class is rare. The '
             'learning-theory literature on imbalanced data therefore shapes the '
             'design choices of such detectors [25], [26].')
    add_para(doc,
             '**Feature selection for security telemetry.** Filter methods are '
             'attractive in security because they are cheap and model-independent: '
             'ANOVA F-test based univariate selection has been used to build compact '
             'intrusion detectors on robotics-network data [7], and mutual '
             'information, correlation and chi-square scores are standard ingredients '
             'of security pipelines [1], [2]. Wrapper methods search harder: '
             'Pigeon-Inspired Optimisation has been applied to choose feature subsets '
             'for intrusion detection [8], and genetic algorithms combined with '
             'random forests have been used on IoT traffic [6]. The cost of wrappers '
             'grows quickly with the number of features, and their selected subsets '
             'depend strongly on the classifier used in the search loop, which '
             'motivates hybrid schemes that combine several cheap filters with a '
             'cheap wrapper into one vote.')
    add_para(doc,
             '**Ensemble and hybrid selection.** Combining several selectors by '
             'voting or rank aggregation reduces the risk that a single criterion '
             'picks redundant or noisy features. Minimum-redundancy '
             'maximum-relevance ranking [46] and stability-index analyses [47], [48] '
             'formalise two requirements that hybrid selectors should meet: the '
             'selected features should add information beyond each other, and the '
             'subset should not change drastically when the training sample changes. '
             'The voting selector of [1] belongs to this family, but it was evaluated '
             'only on network-flow features and with single-split evaluation, so its '
             'behaviour on host events, its stability and its agreement with simpler '
             'rankings are open questions that this thesis addresses directly.')
    add_para(doc,
             '**Autoencoders and graph models for detection.** Autoencoders learn a '
             'compressed representation of normal behaviour and flag rows with large '
             'reconstruction error as anomalous [33]. Adversarial training of the '
             'autoencoder through a discriminator constrains the latent space to a '
             'prior distribution and improves the usefulness of the representation '
             'for downstream tasks [34]. Graph neural networks add relational '
             'structure: a multigraph neural network over IoT traffic improved '
             'intrusion detection by modelling relations between traffic entities '
             '[9], and the graph transformer autoencoder GTAE-IDS reports real-time '
             'intrusion detection above 98 % accuracy with attention over graph '
             'nodes, claiming a stronger detection rate on rare attacks than '
             'sequence models [10]. The A2G-PTH model of [2] combines both ideas, an '
             'adversarially trained autoencoder and a cosine-similarity graph with a '
             'GNN classifier, and it is the deep evaluator used in this thesis.')
    add_para(doc,
             '**The two reference papers.** The hybrid voting paper [1] studies '
             'feature selection on the LUFlow network intrusion dataset [4] '
             '(approximately 959,884 flow records, 16 candidate features, classes '
             'balanced by random undersampling). Mutual information, the ANOVA '
             'F-test, recursive feature elimination with logistic regression, and '
             'Pearson correlation each score the features; each method votes for the '
             'features above its own mean score; features reaching a voting ratio of '
             '0.5 are kept. Seven classical classifiers then evaluate the kept '
             'subset, and the random forest reports the highest accuracy (0.9989) '
             'while removing about half of the features. The paper documents the '
             'promise of consensus voting but leaves three issues open: the reported '
             'feature counts differ between the abstract, the data section and the '
             'score table (15, 16 and 11); the printed thresholds (for example 0.2939 '
             'for both MI and the F-test) are inconsistent with the paper\u2019s own '
             'score table and its votes cannot be reproduced from it; and the '
             'evaluation is a single random split on one honeypot network, with no '
             'stability analysis and no leakage-aware protocol.')
    add_para(doc,
             'The A2G-PTH paper [2] studies the complementary strategy on the ACI '
             'IoT 2023 dataset [5]. Features are scored by chi-square, F-test and '
             'mutual information; the normalised scores are averaged into one '
             'combined score; and the top d \u00d7 p features are kept for a '
             'percentage p from 10 % to 100 %. An adversarial autoencoder with an '
             'attention block feeds a cosine-similarity graph and a GNN classifier, '
             'and bidirectional resampling balances the training classes. The paper '
             'reports its strongest result at the 10 % setting (F1 99.84 %), with '
             'every other retained percentage far lower (about 64\u201382 % '
             'accuracy, Table I of [2]); the paper offers no explanation for this '
             'pattern, and it does not state how the retained percentage was chosen, '
             'how features are assigned between the categorical chi-square and the '
             'numeric F-test, or how the graph adjacency enters the classifier '
             'equations, which do not reference the adjacency matrix. The evaluation '
             'is again a single split without stability analysis, and the smallest '
             'attack class contains a handful of samples.')
    add_para(doc,
             '**Host-based ransomware data.** The RADAR dataset [3] addresses the '
             'scarcity of realistic ransomware telemetry: it was collected on a '
             'controlled Windows 11 laboratory, records Sysmon events from benign '
             'software and from a large set of ransomware samples, and ships both raw '
             'logs and engineered event-level feature files, including the '
             'imbalanced and drift variants used in this thesis. Because RADAR rows '
             'arrive in blocks (a ransomware sample contributes many consecutive '
             'events with the same family and process), naive random splits can put '
             'events of the same sample on both sides of the evaluation, a standard '
             'leakage risk that the machine-learning literature warns about [27] and '
             'that this thesis controls with a group split.')
    add_table(
        doc,
        header_rows=[['Aspect', '[1] Hybrid voting', '[2] A2G-PTH', 'This thesis']],
        body_rows=[
            ['Data', 'LUFlow network flows (16 features)', 'ACI IoT 2023 traffic (83 features stated)',
             'RADAR Sysmon events (21 features)'],
            ['Task', 'Binary intrusion', 'Multi-class intrusion (K = 11)',
             'Binary ransomware (Goodware = 0 / Ransomware = 1)'],
            ['Scoring measures', 'MI, ANOVA F-test, RFE (LR), Pearson', 'Chi-square, F-test, MI, normalised and averaged',
             'Both: FS-A votes; FS-B and FS-C use the combined score'],
            ['Combination', 'Votes; ratio \u2265 0.5', 'Rank by combined score; top d \u00d7 p',
             'FS-A voting, FS-B sweep, FS-C vote-ranked sweep'],
            ['Evaluation models', '7 classical classifiers', 'Adversarial AE + GNN (baselines RNN, CNN, LSTM)',
             '7 classical classifiers + A2G-PTH (both graph variants)'],
            ['Reported result', 'RF accuracy 0.9989 with about half the features', 'F1 99.84 % at 10 % of features only',
             'To be produced by our own runs (Chapter 4)'],
            ['Split / stability', 'Single random split; not reported', 'Single split; not reported',
             'P1/P2/P3 protocols; folds and seeds; stability measured'],
            ['Leakage control', 'Not reported', 'Not reported',
             'Selection, scaling and balancing on training data only'],
        ],
        col_widths_cm=[2.6, 4.4, 4.5, 4.5],
        caption='Table 1: The two reference papers and the scope of this thesis',
        align_body='Left'
    )

    h2(doc, '3.3  Summary')
    add_para(doc,
             'The literature shows that (i) classical machine learning on engineered '
             'host features is a relevant baseline for ransomware detection, (ii) '
             'filter, wrapper and hybrid selection each have known strengths on '
             'security telemetry, and (iii) adversarial autoencoders and graph models '
             'are promising but demanding evaluators. The two reference papers define '
             'the two selection strategies compared in this thesis, yet both were '
             'evaluated in other domains, with a single split, without stability '
             'analysis, and with several unstated or inconsistent details (the '
             'thresholds and feature counts of [1]; the choice of the 10 % percentage, '
             'the chi-square assignment and the role of the graph adjacency in [2]). '
             'No published study compares consensus voting with a percentage sweep on '
             'host-based ransomware events under leakage-aware protocols. The '
             'remainder of this thesis closes that gap: Chapter 4 presents the verified '
             're-implementation of both selectors and the proposed voting-ranked '
             'sweep on RADAR, evaluates the subsets with the seven classical models '
             'and A2G-PTH, and reports agreement, stability and cost.')
