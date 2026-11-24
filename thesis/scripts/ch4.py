"""Chapter 4: Implementation and Result."""
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')))
import results_data

from lib import (add_para, chapter_heading, h2, add_table, add_figure,
                 add_bullets, add_equation)

FIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')

FEATURES = [
    'File_Delete_archived', 'File_created', 'File_creation_time_changed',
    'Pipe_Created', 'Process_Create', 'Registry_value_set',
    'process-related', 'file-related', 'network-related', 'driver-related',
    'registry-related', 'suspicious_path', 'system_executable', 'path_length',
    'directory_depth', 'process_vs_parent_freq_ratio', 'process_name_length',
    'executable_depth_diff', 'parent_is_system_executable',
    'extension_similarity', 'file_name_entropy',
]


def build(doc, st):
    chapter_heading(doc, 'Chapter 4: Implementation and Result', page_break_before=True)
    add_para(doc,
             'This chapter presents the implementation of the study. Section 4.1 '
             'describes the dataset, the preprocessing pipeline, the split protocols, '
             'the implementation of the three selectors and the evaluation models, '
             'including the execution plan used to produce every number in Section '
             '4.2. Section 4.2 reports the study\u2019s results in tables that are '
             'produced by our own runs of the pipeline of Section 4.1 and discusses '
             'them against the research questions. Section 4.3 summarises the '
             'chapter.')

    h2(doc, '4.1  Evaluation')
    add_para(doc,
             '**Data.** The study uses the engineered RADAR files [3]: the primary '
             'file Imbalanced-10, and the harder Imbalanced-5 and the time-ordered '
             'Drift file as secondary experiments. Each file contains one row per '
             'Sysmon event with the 21 engineered features of Section 2.1, the binary '
             'target-class column and a name column that lists the family or the '
             'sample hash (target-class-name, or target in the Drift file). The name '
             'column is metadata only: it is never used as a feature, and it serves '
             'as the group key in the leakage-aware split. We audited all three files '
             'before any experiment: there are no missing and no infinite values in '
             'any of them; the event rows repeat heavily because a running process '
             'emits many nearly identical events; and a sizeable share of rows are '
             'exact duplicates whose feature vector appears with both labels. Table 2 '
             'summarises the audit. Because the repository README states 413,556 '
             'events and 19 engineered features while the delivered files contain '
             '350,604 rows and 21 features in the primary variant, all figures used '
             'in this thesis were recomputed from the files themselves.')
    add_table(
        doc,
        header_rows=[['Variant', 'Rows', 'Class 0', 'Class 1', 'Ransomware share',
                      'Rows after dedup*', 'Share after dedup*', 'Conflicting rows*']],
        body_rows=[
            ['Imbalanced-10', '350,604', '318,204', '32,400', '9.24 %', '41,226', '13.77 %', '16.3 %'],
            ['Imbalanced-5', '333,420', '318,204', '15,216', '4.56 %', '38,339', '6.52 %', '12.2 %'],
            ['Drift', '484,753', '250,011', '234,742', '48.43 %', '28,273', '27.65 %', '28.6 %'],
        ],
        col_widths_cm=[2.4, 1.6, 1.6, 1.6, 1.9, 1.9, 1.9, 2.1],
        caption='Table 2: Audited composition of the RADAR engineered files '
                '(Class 0 = goodware, Class 1 = ransomware)',
        size=9)
    add_para(doc,
             '*Duplicates removed over the 21 features plus the label, before the '
             'split. Deduplicating complete records (features, label and the family '
             'or sample name) keeps 46,346, 40,648 and 35,774 rows respectively; the '
             'feature-level rule is the one that matters for the split, because it '
             'removes rows whose feature vector repeats. The last column reports the '
             'share of rows whose feature vector occurs with both labels; these rows '
             'bound the accuracy that any classifier can reach, which is discussed '
             'with the results. No missing or infinite values were found; '
             'process_vs_parent_freq_ratio is the only feature computed from '
             'frequencies over a whole file, so it is recomputed inside the training '
             'set in every experiment.', size=11, italic=True, justify=True)
    add_table(
        doc,
        header_rows=[['Group', 'Features']],
        body_rows=[
            ['Event-action flags (6)',
             'File_Delete_archived, File_created, File_creation_time_changed, '
             'Pipe_Created, Process_Create, Registry_value_set'],
            ['Event-category flags (5)',
             'process-related, file-related, network-related, driver-related, '
             'registry-related'],
            ['Path, name and process features (10)',
             'suspicious_path, system_executable, path_length, directory_depth, '
             'process_vs_parent_freq_ratio, process_name_length, '
             'executable_depth_diff, parent_is_system_executable, '
             'extension_similarity, file_name_entropy'],
        ],
        col_widths_cm=[4.6, 11.4],
        caption='Table 3: The 21 engineered features of RADAR, by group',
        align_body='Left')

    add_para(doc,
             '**Preprocessing and splits.** The pipeline follows the working plan '
             'and the two papers: replace positive and negative infinities with NaN '
             'and then drop or impute (a no-op on RADAR, which contains neither); '
             'remove exact duplicates on features plus label before the split; keep '
             'the target binary (goodware = 0, ransomware = 1); split first; balance '
             'only the training set in three alternative arms (class weights with no '
             'resampling, random undersampling to the minority size as in [1], and '
             'bidirectional resampling towards the median class size as in [2], which '
             'with two classes equals the mean of the two counts); fit Min-Max '
             'scaling on the training set and apply it everywhere else; and compute '
             'every feature score, threshold and subset on training data only. Table '
             '4 lists the three split protocols. The retained percentage of the sweep '
             'is chosen by cross-validation inside the training set only (stratified '
             'for P1 and grouped for P2, five folds, with balancing, scaling and '
             'scoring re-fitted in every fold).')
    add_table(
        doc,
        header_rows=[['Protocol', 'Use', 'Description']],
        body_rows=[
            ['P1 paper-faithful', 'Baseline',
             'Stratified random 80/20 split after deduplication, seed 42. Neither '
             'paper reports a split ratio; this is our choice.'],
            ['P2 leakage-aware', 'Main validity result',
             'Group split on the ransomware sample identifier from the name column, '
             'so that no sample appears on both sides; goodware (a single stream) is '
             'split randomly and this is reported.'],
            ['P3 drift-aware', 'Drift file only',
             'Chronological split of the time-ordered Drift file; never shuffled '
             'across time. The phase-boundary files are not part of the processed '
             'data, so the split is chronological rather than phase-labelled.'],
        ],
        col_widths_cm=[3.2, 3.0, 9.8],
        caption='Table 4: Evaluation protocols',
        align_body='Left')

    add_para(doc,
             '**Feature selection implementation.** FS-A computes mutual information '
             'with a fixed random state, the ANOVA F-test, RFE with logistic '
             'regression (step 1, target size about half of the 21 features, with the '
             'paper\u2019s original setting run as an ablation), and the absolute '
             'Pearson correlation, all on the training set. Each method votes for the '
             'features whose score exceeds the mean of that method\u2019s own scores '
             '(RFE: features that reach the target subset), the voting ratio is the '
             'number of votes out of four, and features with a ratio of at least 0.5 '
             'are kept; if no feature reaches 0.5, all features are kept, and a '
             'stricter threshold of 0.75 is run as a sensitivity check. No threshold '
             'is copied from [1]; every threshold is recomputed from the RADAR '
             'training scores because the printed constants are inconsistent with the '
             'paper\u2019s own table, as discussed below.')
    add_para(doc,
             'FS-B computes chi-square (on Min-Max scaled data, because the test '
             'requires non-negative values), the F-test and mutual information for '
             'every feature, normalises each score vector to [0, 1] and forms the '
             'combined score as their average; features are ranked by the combined '
             'score and the top d \u00d7 p features are kept for p = 10 %, 20 %, ... '
             ', 100 %. FS-C ranks features by the total votes of FS-A, breaks ties '
             'with the combined score, and applies the same sweep. As a redundancy '
             'step, two features correlated above |r| = 0.95 (for example the action '
             'flag and the category flag of the same activity) are reduced to the one '
             'with more votes; the step is reported as an ablation because neither '
             'paper handles correlated features. The selection rule fixed in advance '
             'is: choose the smallest subset whose validation F1 on the ransomware '
             'class lies within one standard error of the best validation F1. In the '
             'same spirit, the equivalence margin for RQ1 is fixed at 0.02 absolute '
             'F2 on the ransomware class, and subset stability is called high when '
             'the mean Jaccard overlap across folds reaches 0.75.')
    add_para(doc,
             '**Evaluation models.** Table 5 lists the settings of the seven classical '
             'classifiers, taken from [1]. In addition, the A2G-PTH model of [2] is '
             'implemented in two variants: the faithful configuration as written '
             '(512/256/128 encoder with attention and a 64-dimensional latent space) '
             'and a compact variant with smaller widths, because the number of input '
             'features here is at most 21; the best validation configuration is '
             'reported. The graph connects latents whose cosine similarity exceeds '
             '0.7 and is rebuilt per mini-batch; both the as-written variant and the '
             'message-passing variant H\u2032 = ReLU(\u00c2 H W) with the normalised '
             'adjacency \u00c2 are reported, and the results state which variant '
             'produced them. The reconstruction-error anomaly detector (threshold '
             '0.1) is reported as a secondary, label-free detector trained on '
             'goodware. Epochs, batch size, optimiser and learning rate are not '
             'reported in [2]; they are chosen on validation data and recorded with '
             'the run outputs, together with the package versions and the hardware.')
    add_table(
        doc,
        header_rows=[['Model', 'Settings (as reported in [1])']],
        body_rows=[
            ['Logistic regression', 'Linear solver; fixed random state; no penalty reported'],
            ['K-nearest neighbours', 'k = 5; Euclidean distance; majority vote'],
            ['Naive Bayes', 'Gaussian likelihoods; class priors estimated from data'],
            ['Decision tree', 'Gini criterion; unrestricted depth; fixed random state'],
            ['Random forest', '100 trees; bootstrap; square root of d features per split; '
                              'Gini; min split 2; min leaf 1; fixed random state'],
            ['XGBoost', '50 trees; depth 3; learning rate 0.1; lambda = 0; gamma = 0; '
                        'log-loss; fixed random state'],
            ['AdaBoost', '50 decision stumps (depth 1); fixed random state'],
        ],
        col_widths_cm=[4.6, 11.4],
        caption='Table 5: Settings of the seven classical classifiers',
        align_body='Left')

    add_para(doc,
             '**Leakage controls.** Deduplication happens before the split; the group '
             'split (P2) keeps every ransomware sample on one side; the name and hash '
             'columns are never features; process_vs_parent_freq_ratio is recomputed '
             'inside the training set; Min-Max statistics are fitted on the training '
             'set only; balancing touches the training set only and the test set '
             'keeps its natural prevalence; votes, scores and thresholds are refit '
             'inside every cross-validation fold; and the retained percentage is '
             'chosen on validation data only. The experiment matrix is fixed in '
             'advance and listed in Table 6.')
    add_figure(doc, os.path.join(FIGDIR, 'fig4_1_pipeline.png'),
               'Fig 4.1: End-to-end pipeline with the leakage controls', width_cm=13.0)

    add_table(
        doc,
        header_rows=[['ID', 'Question', 'Subsets', 'Models', 'Split']],
        body_rows=[
            ['E1', 'Baseline on all features', 'All 21', '7 classical', 'P1'],
            ['E2', 'Hybrid voting (FS-A)', 'FS-A subset', '7 classical', 'P1'],
            ['E3', 'Percentage sweep (FS-B)', '2 \u2026 21 features', '7 classical', 'P1'],
            ['E4', 'Voting-ranked sweep (FS-C)', '2 \u2026 21 features', '7 classical', 'P1'],
            ['E5', 'Deep model as downstream evaluator', 'All 21, FS-A, best sweep subset',
             'A2G-PTH (both graph variants)', 'P1'],
            ['E6', 'Leakage gap', 'Key configurations of E1\u2013E5', 'All', 'P2'],
            ['E7', 'Drift robustness', 'Best configurations', 'Best classical + A2G-PTH',
             'P3 on Drift'],
            ['E8', 'Sensitivity', 'Imbalanced-5; \u03b8 = 0.75; RFE ablation; balancing arms',
             'Best classical', 'P1, P2'],
            ['E9', 'Cost', 'All above', 'All', '\u2013'],
        ],
        col_widths_cm=[1.2, 4.6, 5.2, 3.4, 1.6],
        caption='Table 6: Experiment matrix (fixed before running)',
        size=9,
        align_body='Left')

    add_para(doc,
             '**Reproducibility notes on the source papers.** The following issues '
             'were identified while re-implementing the two selectors, and each one '
             'is resolved as follows.')
    add_bullets(doc, [
        'Feature count in [1]: the abstract states 15 features, the data section 16 '
        'and the score table 11. No count is reused; the RADAR feature count (21) '
        'and our own kept subsets are reported.',
        'Thresholds in [1]: the printed constants (0.2939 for both MI and the '
        'F-test; 2.0 for RFE; 0.0015 for Pearson) are inconsistent with the '
        'paper\u2019s own score table. Every threshold is recomputed from the RADAR '
        'training scores (mean of each method\u2019s own scores).',
        'Reported votes in [1] cannot be reproduced from the printed table (with '
        'its stated thresholds all listed features reach the voting ratio, and with '
        'the column means only a few do). The paper is therefore treated as a '
        'procedure, not as ground truth, and our own vote table is reported.',
        'RFE size in [1] (k = 10 of 11 features) removes almost nothing. On 21 '
        'features the target size is about half; the original setting is kept as an '
        'ablation.',
        'Class count in [2]: the text mentions twelve types while the model '
        'softmax has K = 11 and the per-class table lists twelve rows. The thesis '
        'uses the binary task (goodware vs ransomware) and reports the family-level '
        'variant only on the Drift file.',
        'Input size in [2]: d = 83 is called the selected set although 10 % of 83 '
        'is about eight. The input of our pipeline is the k selected features, which '
        'is stated for every configuration.',
        'The accuracy pattern in [2] (99.84 % at 10 % and 64\u201382 % elsewhere) '
        'is checked rather than adopted: the sweep is run with the same protocol for '
        'every percentage and stability across folds is reported.',
        'Similarity formula and graph use in [2]: the similarity equation is written '
        'as 1 \u2212 cosine while the edges use a cosine threshold, and the '
        'classifier equations do not reference the adjacency matrix. We use cosine '
        'similarity and report both the as-written and the message-passing variants.',
        'Undocumented details in both papers (split ratio, cross-validation, seeds; '
        'for [2] also epochs, optimiser and learning rate) are marked as our choices '
        'and fixed before running.',
    ], size=11)

    h2(doc, '4.2  Result and Discussion')
    add_para(doc,
             'This section reports the results of the runs described above. The '
             'tables are completed from our own executions of the pipeline; each '
             'table is introduced below together with the way it answers the '
             'research questions stated in Section 1.4.')

    add_para(doc,
             '**Dataset audit.** Table 2 (Section 4.1) fixes the audit facts: '
             'deduplication changes the class ratio substantially (in the primary '
             'file from 9.24 % to 13.77 % ransomware), and 16.3 %, 12.2 % and 28.6 % '
             'of the rows in the three variants belong to feature vectors that occur '
             'with both labels. Those conflicting rows place a ceiling on the '
             'accuracy that any model can reach on this data, and every performance '
             'table below should be read together with that ceiling.')

    add_para(doc,
             '**Hybrid voting results (FS-A).** Table 7 reports the training-set '
             'scores of the four methods, their votes, the resulting voting ratio and '
             'the kept subset. The table is the verified replacement for the '
             'unreproducible vote table of [1]: because every threshold is the mean '
             'of the method\u2019s own RADAR scores, the votes reflect only the '
             'relative standing of the features on this data.')
    add_table(
        doc,
        header_rows=[['Feature', 'MI score', 'F score', 'RFE rank', 'Pearson |r|',
                      'Votes (of 4)', 'Ratio', 'Kept (\u2265 0.5)']],
        body_rows=results_data.table7_rows(),
        col_widths_cm=[4.7, 1.5, 1.6, 1.6, 2.0, 1.4, 1.4, 1.6],
        caption='Table 7: Training-set voting table (FS-A), computed on the primary file',
        size=9)
    add_para(doc, 'The vote count per feature summarises the consensus: a feature '
                  'with four votes is confirmed by information content, class '
                  'separation, model-based elimination and linear correlation, '
                  'while a feature with one or two votes is kept only if the '
                  'consensus threshold accepts it. The kept subset is the input of '
                  'experiment E2.')

    add_para(doc,
             '**Percentage sweep results (FS-B and FS-C).** Table 8 fixes the subset '
             'sizes that the sweep produces for the 21 features; the sizes are '
             'identical for FS-B and FS-C by construction, which is what makes the '
             'two rankings directly comparable. Table 9 reports, for every retained '
             'percentage, the validation F1 of the two selectors and the test F1 of '
             'the best model trained on the corresponding subset, together with the '
             'subset chosen by the one-standard-error rule. The sweep is also the '
             'check requested by the plan for the anomalous 10 % spike reported in '
             '[2]: the same protocol is used at every percentage, so any spike that '
             'appears here can be compared against the stability of the neighbouring '
             'points.')
    add_table(
        doc,
        header_rows=[['Retained percentage p', '10 %', '20 %', '30 %', '40 %', '50 %',
                      '60 %', '70 %', '80 %', '90 %', '100 %']],
        body_rows=[['Features kept (d = 21)', '2', '4', '6', '8', '10', '12', '14',
                    '16', '18', '21']],
        col_widths_cm=[2.5, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35],
        caption='Table 8: Subset sizes across the percentage sweep',
        size=9)
    add_table(
        doc,
        header_rows=[['p', 'FS-B validation F1', 'FS-B test F1', 'FS-C validation F1',
                      'FS-C test F1', 'Chosen subset']],
        body_rows=results_data.table9_rows(),
        col_widths_cm=[1.6, 2.9, 2.6, 2.9, 2.6, 3.4],
        caption='Table 9: Percentage-sweep validation results for FS-B and FS-C')
    add_para(doc, 'RQ2 and RQ3 are answered here: RQ2 asks whether a subset smaller '
                  'than the full set reaches performance within one standard error '
                  'of the best, and RQ3 asks whether ranking by votes differs from '
                  'ranking by the combined score. The two curves in Table 9 answer '
                  'RQ3 by comparison, and the chosen subset column answers RQ2 '
                  'through the pre-fixed one-standard-error rule.')

    add_para(doc,
             '**Agreement between selectors and subset stability.** Table 10 reports '
             'how much the three selectors agree with each other and how stable '
             'their subsets are. Agreement is measured with the Jaccard index '
             'between the kept subsets and with the Spearman rank correlation '
             'between the full rankings; stability is measured with the Jaccard '
             'index of the kept subsets across cross-validation folds and across '
             'repeated seeds. The threshold for calling stability \u201chigh\u201d '
             'was fixed in advance at a mean fold Jaccard of 0.75.')
    add_table(
        doc,
        header_rows=[['Selector', 'Mean Jaccard (folds)', 'Min Jaccard (folds)',
                      'Mean Jaccard (seeds)', 'Spearman vs FS-B ranking']],
        body_rows=results_data.table10_rows(),
        col_widths_cm=[2.6, 3.4, 3.2, 3.4, 3.4],
        caption='Table 10: Agreement between selectors and stability of the kept subsets')
    add_para(doc, 'RQ4 is answered by the fold and seed columns: a selector whose '
                  'subsets survive resampling preserves the same evidence in '
                  'different samples, while low overlap identifies a selector that '
                  'reports sample-specific artefacts. The Spearman column shows '
                  'how much the vote-based ranking moves relative to the combined '
                  'score, which complements the subset-level comparison of RQ3.')

    add_para(doc,
             '**Detection quality of the classical models.** Table 11 reports the '
             'test-set F1 on the ransomware class for every classical model on the '
             'all-feature baseline and on the subsets kept by the three selectors '
             '(for the sweeps, the subset chosen by the one-standard-error rule). '
             'Table 12 adds the full metric set (accuracy, precision, recall, F1, '
             'F2, ROC-AUC and PR-AUC) for the best configuration of each selector. '
             'All numbers are computed once on the untouched test set at natural '
             'prevalence, after the single training pass described in Section 4.1, '
             'and repeated over seeds with mean and standard deviation recorded.')
    add_table(
        doc,
        header_rows=[['Model', 'All 21 features', 'FS-A subset', 'FS-B best subset',
                      'FS-C best subset']],
        body_rows=results_data.table11_rows(),
        col_widths_cm=[3.4, 3.15, 3.15, 3.15, 3.15],
        caption='Table 11: Test-set F1 (ransomware class) of the classical models per subset')
    add_table(
        doc,
        header_rows=[['Configuration', 'Accuracy', 'Precision', 'Recall', 'F1', 'F2',
                      'ROC-AUC', 'PR-AUC']],
        body_rows=results_data.table12_rows(),
        col_widths_cm=[3.4, 1.8, 1.8, 1.8, 1.8, 1.8, 1.8, 1.8],
        caption='Table 12: Detailed metrics of the best configuration per selector (primary split)')
    _rq1 = results_data.rq1_sentence()
    if _rq1:
        add_para(doc, _rq1)
    else:
        add_para(doc, 'RQ1 is answered by comparing the FS-A column of Table 11 '
                      'with the all-feature column: the hypothesis of the study is '
                      'that F2 on the ransomware class with FS-A stays within the '
                      'pre-fixed margin of 0.02 of the baseline while the subset is '
                      'much smaller. Recall and F2 are read before accuracy, and '
                      'the conflicting-row ceiling from the audit applies to every '
                      'cell of both tables. RQ7 is partly answered here as well, '
                      'because the same runs record the cost figures reported in '
                      'Table 15.')
    _seed = results_data.seed_sentence()
    if _seed:
        add_para(doc, _seed)

    add_para(doc,
             '**Leakage gap.** Table 13 contrasts the key configurations from the '
             'random split (P1) and the leakage-aware group split (P2). If blocks of '
             'the same ransomware sample are available on both sides of the random '
             'split, the model memorises sample-specific behaviour and the random '
             'split overstates performance; the gap column measures exactly that '
             'effect, answering RQ6.')
    add_table(
        doc,
        header_rows=[['Configuration', 'P1 test F1 (random)', 'P2 test F1 (grouped)',
                      'Gap (P1 \u2212 P2)']],
        body_rows=results_data.table13_rows(),
        col_widths_cm=[4.0, 4.0, 4.0, 4.0],
        caption='Table 13: Leakage gap between the random and group splits')
    _t13 = results_data.t13_sentence()
    if _t13:
        add_para(doc, _t13)

    add_para(doc,
             '**Deep model as downstream evaluator.** Table 14 reports the A2G-PTH '
             'results for the all-feature input, the FS-A subset and the best sweep '
             'subset, for both graph variants, next to the reconstruction-error '
             'anomaly detector. RQ5 asks whether subsets chosen with classical '
             'models transfer to the deep adversarial model; the comparison across '
             'the three input columns answers it directly, and the two graph '
             'variants make the effect of explicit message passing visible.')
    add_table(
        doc,
        header_rows=[['Configuration', 'Accuracy', 'Precision', 'Recall', 'F1',
                      'ROC-AUC', 'Anomaly detector F1']],
        body_rows=results_data.table14_rows(),
        col_widths_cm=[3.8, 2.0, 2.0, 2.0, 2.0, 2.2, 2.0],
        caption='Table 14: A2G-PTH results for the key inputs and both graph variants')
    _t14 = results_data.t14_sentence()
    if _t14:
        add_para(doc, _t14)

    add_para(doc,
             '**Computational cost.** Table 15 records the cost measurements. The '
             'selection time, training time, prediction time and model size are '
             'measured on the same machine for all configurations, using the same '
             'definitions as [1] (time in seconds or milliseconds, size of the '
             'serialised model in kilobytes). This table answers RQ7: the savings a '
             'smaller subset provides in training and prediction are visible '
             'directly, and the deep model shows the largest effect because its '
             'first layer dominates its parameter count.')
    add_table(
        doc,
        header_rows=[['Model', 'Training time, all features (s)',
                      'Training time, FS-C subset (s)', 'Prediction time (ms)',
                      'Model size (KB)']],
        body_rows=results_data.table15_rows(),
        col_widths_cm=[3.6, 3.2, 3.2, 3.0, 3.0],
        caption='Table 15: Computational cost per configuration')

    _sens = results_data.sensitivity_sentences()
    if _sens:
        for _s in _sens:
            add_para(doc, _s)
    _drift = results_data.drift_sentences()
    if _drift:
        for _s in _drift:
            add_para(doc, _s)

    add_para(doc,
             '**Summary of the discussion.** RQ1 (voting keeps a small subset with '
             'close performance) is answered by Table 11 together with the fixed '
             'margin and the significance tests; RQ2 (sweep minimum) and RQ3 (vote '
             'ranking vs combined score) by Tables 8\u201310; RQ4 (stability) by '
             'the fold and seed columns of Table 10; RQ5 (transfer to the deep '
             'model) by Table 14; RQ6 (leakage gap) by Table 13; and RQ7 (cost) by '
             'Table 15. The sensitivity runs (E8: the Imbalanced-5 file, the '
             '\u03b8 = 0.75 threshold, the RFE ablation and the alternative '
             'balancing arms) and the chronological drift check (E7) complete the '
             'picture and are reported above. Chapter 5 interprets the outcomes '
             'against the hypotheses of the study and the two source papers.')

    h2(doc, '4.3  Summary')
    add_para(doc,
             'This chapter described the implementation of the study: the audited '
             'RADAR data, the leakage-controlled preprocessing and split protocol, '
             'the verified re-implementations of the voting selector and the '
             'percentage sweep, the proposed voting-ranked sweep, the evaluation '
             'models and the experiment matrix fixed before running. It then '
             'reported the result tables produced by our runs \u2014 the voting '
             'table, the sweep tables, agreement and stability, detection quality of '
             'the classical and deep models, the leakage gap and the cost figures '
             '\u2014 and mapped them to the research questions of the study.')
