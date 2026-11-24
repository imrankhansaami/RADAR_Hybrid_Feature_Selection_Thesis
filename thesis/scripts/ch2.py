"""Chapter 2: Background."""
import os
from lib import add_para, chapter_heading, add_figure, add_bullets, h2, add_equation

FIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')


def build(doc, st):
    chapter_heading(doc, 'Chapter 2: Background', page_break_before=True)
    add_para(doc,
             'This chapter introduces the concepts behind the study: ransomware '
             'behaviour and the Sysmon telemetry that exposes it (Section 2.1), the '
             'categories of feature selection methods and why selection matters for '
             'this dataset (Section 2.2), the statistical measures used to score '
             'features (Section 2.3), the two published selection strategies and the '
             'voting-ranked sweep proposed in this thesis (Sections 2.4 and 2.5), the '
             'classical classifiers and the deep adversarial graph model used to '
             'evaluate the selected subsets (Sections 2.6 and 2.7), and the metrics '
             'used to measure detection quality and cost (Section 2.8).')

    h2(doc, '2.1  Ransomware and Sysmon Event Telemetry')
    add_para(doc,
             'Ransomware is malicious software that obstructs access to a victim\u2019s '
             'data with the aim of extorting a payment. A typical modern execution '
             'proceeds in phases: the sample is executed from a suspicious location, '
             'for example a user folder or a temporary directory; it creates or '
             'modifies files at a high rate while it prepares the encryption; it '
             'deletes local shadow copies, backups and archived documents; it changes '
             'file creation timestamps so that encrypted files blend in; it may '
             'install persistence through the registry; and it finally leaves ransom '
             'notes. Each of these actions produces operating-system level events.')
    add_para(doc,
             'Sysmon (System Monitor) is a Windows service that records such events '
             'in a structured form. For every relevant activity it logs an event '
             'code, the acting process and its parent process, the file, pipe, '
             'registry key or network endpoint involved, and metadata such as file '
             'hashes and signatures. Security research increasingly treats Sysmon '
             'logs as the primary telemetry for host-based detection, because the '
             'logged activity describes behaviour rather than static file content and '
             'is therefore more robust against packing and obfuscation [29], [30].')
    add_para(doc,
             'The RADAR dataset [3] provides Sysmon events collected in a controlled '
             'laboratory environment on Windows 11: several hundred thousand events '
             'triggered by ordinary software (goodware) and by the execution of many '
             'ransomware samples. In the engineered files used by this thesis, each '
             'row is a single Sysmon event described by 21 engineered features: six '
             'event-action flags (file deleted and archived, file created, file '
             'creation time changed, pipe created, process created, registry value '
             'set), five event-category flags (process-, file-, network-, driver- and '
             'registry-related), and ten path, name and process features such as the '
             'path length, the directory depth, the executable depth difference, the '
             'file name entropy and the ratio of the process frequency to the parent '
             'process frequency. The binary label marks whether the event comes from '
             'a ransomware execution. The dataset is provided in three variants: '
             'Imbalanced-10 (about 9.2 % ransomware events), Imbalanced-5 (about '
             '4.6 %) and Drift (about 48 %, where ransomware families are introduced '
             'gradually over time [28]). Section 4.1 gives the exact composition and the '
             'audit we performed on these files.')

    h2(doc, '2.2  Feature Selection: Concepts and Categories')
    add_para(doc,
             'Feature selection is the process of choosing, from the available '
             'measurements, the subset that carries most of the useful information '
             'about the target while discarding redundant and irrelevant variables '
             '[11]. The goal is threefold: a smaller input reduces training and '
             'inference cost, a selected subset is easier to justify to an analyst, '
             'and removing noisy variables can improve detection quality, especially '
             'when the interesting class is rare and the number of available rows is '
             'large but repetitive [26].')
    add_para(doc,
             'Feature selection methods are usually grouped into four families '
             '(Figure 2.1). Filter methods score each feature with a statistical '
             'criterion independently of any classifier: mutual information, the '
             'ANOVA F-test, the chi-square test and correlation coefficients belong '
             'to this family [11], [7]. Wrapper methods search subsets using the '
             'performance of a model as the criterion, recursive feature elimination '
             'being the standard example [12], [17], [43]. Embedded methods perform '
             'selection as '
             'part of model training, for example through the L1 penalty of LASSO '
             '[45]. Hybrid and ensemble methods combine several selection criteria or '
             'several selectors, either by voting, by rank aggregation [44], or by '
             'applying one selector on top of another; this family is the subject of '
             'this thesis, since both reference papers belong to it [1], [2].')
    add_para(doc,
             'Two practical properties of a selector matter beyond the score it '
             'computes. The first is stability: a selector whose kept subset changes '
             'completely when the sample changes is difficult to interpret, so '
             'subset overlap (for example the Jaccard index) is measured across '
             'resampled training sets [47], [48]. The second is leakage control: '
             'every score, threshold and subset must be computed on training data '
             'only, because a selector that has seen the test rows leaks information '
             'into the evaluation and inflates the measured performance [27]. Both '
             'properties are evaluated in this study (Section 4.4).')
    add_figure(doc, os.path.join(FIGDIR, 'fig2_1_taxonomy.png'),
               'Fig 2.1: Categories of feature selection methods', width_cm=14.0)

    h2(doc, '2.3  Statistical Measures for Feature Ranking')
    add_para(doc,
             'The selectors in this thesis score features with measures from '
             'information theory and classical statistics. This section defines the '
             'measures; all of them are computed on the training set only.')
    add_para(doc,
             '**Mutual information (MI)** measures any statistical dependence, '
             'linear or non-linear, between a feature X and the target Y [13]. For '
             'discrete variables it is defined as:', space_after=2)
    add_equation(doc,
                 'I(X; Y) = \u03a3\u2093 \u03a3\u1d67 p(x, y) log( p(x, y) / ( p(x) \u00b7 p(y) ) )',
                 st.next_eq())
    add_para(doc,
             'where p(x, y) is the joint probability and p(x), p(y) are the marginal '
             'probabilities estimated from the training data. Continuous features are '
             'discretised for this estimation. A large MI means the feature and the '
             'target are strongly dependent; [1] computes MI with a fixed random '
             'state for reproducibility.')
    add_para(doc,
             '**ANOVA F-test** compares the between-class variance of a feature with '
             'its within-class variance [14]:', space_after=2)
    add_equation(doc,
                 'F = ( SS_between / (K \u2212 1) ) / ( SS_within / (N \u2212 K) )',
                 st.next_eq())
    add_para(doc,
             'where SS_between and SS_within are the between-class and within-class '
             'sums of squares, K is the number of classes and N the number of '
             'training rows. For a binary task, K = 2. A large F indicates that the '
             'class means of the feature are well separated relative to the spread '
             'inside the classes [7].')
    add_para(doc,
             '**Recursive feature elimination (RFE)** is a wrapper method. It fits a '
             'model, ranks the features by the magnitude of their coefficients or '
             'importance, removes the weakest feature, and repeats the procedure '
             'until a target number of features remains [12]. With logistic '
             'regression as the underlying model, the feature removed at each step '
             'is:', space_after=2)
    add_equation(doc,
                 'j* = argmin\u1d62 | w\u1d62 | ,   X \u2190 X \\ { j* }',
                 st.next_eq())
    add_para(doc,
             'The rank of a feature is the step at which it survives; the last '
             'standing feature is the most important, and a feature that reaches the '
             'target subset receives rank one.')
    add_para(doc,
             '**Pearson correlation** [15] measures the strength of the linear '
             'relationship between a feature and the target:', space_after=2)
    add_equation(doc,
                 'r = \u03a3 (x\u1d62 \u2212 x\u0304)(y\u1d62 \u2212 \u0233) / \u221a[ \u03a3 (x\u1d62 \u2212 x\u0304)\u00b2 \u00b7 \u03a3 (y\u1d62 \u2212 \u0233)\u00b2 ]',
                 st.next_eq())
    add_para(doc,
             'For a binary target, the standard Pearson coefficient coincides with '
             'the point-biserial correlation. Its absolute value is used for '
             'ranking, so strong negative relations count as important [16].')
    add_para(doc,
             '**Chi-square test** (\u03c7\u00b2) measures the dependence between a '
             'non-negative feature and the target by comparing observed and expected '
             'frequencies. Because it requires non-negative values, it is computed on '
             'Min-Max scaled features in this study. The reference papers use these '
             'measures as follows: [1] votes with MI, the F-test, RFE and Pearson '
             'correlation, while [2] averages the \u03c7\u00b2, F-test and MI scores '
             'into a single ranking score. Both approaches are re-implemented in '
             'Chapter 4.')

    h2(doc, '2.4  Hybrid Consensus Voting (FS-A)')
    add_para(doc,
             'The hybrid voting selector of [1] combines four different views of '
             'feature importance: information content (MI), separation between the '
             'classes (F-test), predictive relevance under a linear model (RFE) and '
             'linear association with the target (Pearson correlation). Each of the '
             'four methods casts one vote. A method votes for every feature whose '
             'score exceeds the mean of that method\u2019s own scores, so that each '
             'method keeps a comparable share of the candidates regardless of the '
             'scale of its scores. For RFE, a vote is given to the features that '
             'survive elimination and reach rank one.')
    add_para(doc,
             'For each feature j, the voting ratio is the number of votes divided by '
             'the number of methods M, and the feature is kept when the ratio reaches '
             'the consensus threshold \u03b8:', space_after=2)
    add_equation(doc,
                 'ratio\u2c7c = ( 1 / M ) \u00b7 \u03a3\u2098 1[ method m votes for feature j ] ,   keep j if ratio\u2c7c \u2265 \u03b8',
                 st.next_eq())
    add_para(doc,
             'With M = 4 methods, \u03b8 = 0.5 means that a feature is kept when at '
             'least two methods vote for it. If no feature reaches the threshold, '
             'the selector falls back to keeping all features. Two adaptations are '
             'needed on RADAR. First, every threshold is recomputed from the RADAR '
             'training scores: the fixed constants printed in [1] are not consistent '
             'with the paper\u2019s own score table, as documented in Section 4.1, so '
             'they are treated as a procedure rather than as reference values. '
             'Second, the RFE target size is set so that elimination removes a '
             'meaningful number of features; the setting used by [1] removes almost '
             'nothing on a small feature set, and this study records the vote count '
             'and voting ratio of every feature in a reproducible table. Figure 2.2 '
             'shows the workflow.')
    add_figure(doc, os.path.join(FIGDIR, 'fig2_2_voting.png'),
               'Fig 2.2: Workflow of the hybrid consensus voting selector (FS-A)',
               width_cm=13.5)

    h2(doc, '2.5  Percentage-Sweep Selection: FS-B and FS-C')
    add_para(doc,
             'The second selection strategy comes from [2]. Features are scored with '
             'three measures (chi-square, F-test and mutual information), each score '
             'vector is Min-Max normalised across features so that the three '
             'measures become comparable, and a combined score is formed as the '
             'average of the three normalised scores:', space_after=2)
    add_equation(doc,
                 'S\u1d62 = ( 1 / 3 ) \u00b7 ( \u03c7\u00b2\u2032\u1d62 + F\u2032\u1d62 + MI\u2032\u1d62 ) ,   s\u2032 = ( s \u2212 min s ) / ( max s \u2212 min s )',
                 st.next_eq())
    add_para(doc,
             'Features are ranked by S\u1d62, and the top d \u00d7 p features are kept '
             'for a retained percentage p that sweeps ten, twenty, ... , one hundred '
             'percent of the feature count d. The sweep produces not a single subset '
             'but a family of candidate subsets of increasing size, and the retained '
             'percentage is chosen on validation data, never on the test set. [2] '
             'does not state how its ten percent were chosen; if that choice was made '
             'on test results it amounts to selection bias, which this thesis avoids '
             'by fixing the rule in advance: the smallest subset whose validation F1 '
             'on the ransomware class lies within one standard error of the best '
             'validation F1 is selected. [2] also does not explain how features are '
             'assigned to the chi-square versus the F-test; this study computes all '
             'three scores for every feature and documents the decision.')
    add_para(doc,
             'The voting-ranked sweep, FS-C, is proposed in this thesis to link the '
             'two papers\u2019 ideas. Features are first ranked by their total votes '
             'from FS-A; features with equal votes are ordered by the combined score '
             'S\u1d62 from FS-B. The ordered list is then swept exactly as in FS-B. '
             'Because FS-C and FS-B keep subsets of identical sizes for every p, the '
             'sweep curves of the two rankings can be compared directly, and the '
             'comparison shows whether consensus voting carries information beyond '
             'the combined statistical score. Figure 2.3 shows both workflows; '
             'Section 4.2 reports the sweep results as a table.')
    add_figure(doc, os.path.join(FIGDIR, 'fig2_3_sweep.png'),
               'Fig 2.3: Workflow of the percentage sweep (FS-B) and the voting-ranked sweep (FS-C)',
               width_cm=13.5)

    h2(doc, '2.6  Classical Machine Learning Classifiers')
    add_para(doc,
             'The seven classical classifiers of [1] evaluate the selected subsets '
             'and they represent very different decision mechanisms: a linear model, '
             'two instance- and distribution-based models, and four tree-based '
             'ensembles. The settings below follow the configuration reported in [1] '
             'and are listed again with the preprocessing in Section 4.1.')
    add_para(doc,
             '**Logistic regression (LR)** models the class probability with a '
             'sigmoid over a linear combination of the features and fits the '
             'coefficients by maximum likelihood [22] (the linear solver is used, with a '
             'fixed random state). It is the most transparent of the seven models: '
             'each coefficient corresponds to one feature.')
    add_para(doc,
             '**K-nearest neighbours (KNN)** classifies a row by majority vote among '
             'its k = 5 nearest training rows under Euclidean distance [20]. The distance '
             'metric requires scaled features, which is one reason the whole pipeline '
             'uses Min-Max scaling.')
    add_para(doc,
             '**Gaussian naive Bayes (NB)** models each feature within each class as '
             'a normal distribution and combines the likelihoods with the class '
             'priors under an independence assumption [21]. The assumption is weak for '
             'correlated binary flags, which is one of the reasons its behaviour on '
             'the subsets is worth observing.')
    add_para(doc,
             '**Decision tree (DT)** splits the data greedily by the impurity '
             'criterion (Gini index [19], with unrestricted depth and a fixed random '
             'state). A single tree is easy to read but high variance; in [1] the '
             'text mentions information gain while the definition follows Gini, a '
             'small inconsistency that this study resolves in favour of Gini.')
    add_para(doc,
             '**Random forest (RF)** averages 100 decorrelated trees, each grown '
             'with bootstrap sampling and a random subset of features at every split '
             '(square root of d in [1], meaning d = 7 there); it reduces the variance '
             'of a single tree while remaining non-parametric [16].')
    add_para(doc,
             '**XGBoost** builds boosted trees in sequence, each new tree fitting the '
             'residuals of the previous ensemble under a regularised objective. The '
             'configuration of [1] uses 50 trees, depth 3, learning rate 0.1, '
             'log-loss and no explicit regularisation.')
    add_para(doc,
             '**AdaBoost** reweights training rows after every round and combines 50 '
             'decision stumps with weighted votes [18]. Because the weights of '
             'misclassified rows grow, the method is sensitive to noisy labels, and '
             'the duplicate and conflicting rows described in Section 4.1 are '
             'expected to challenge it most.')

    h2(doc, '2.7  The A2G-PTH Adversarial Graph Model')
    add_para(doc,
             'The deep evaluator of this study is A2G-PTH from [2], an adversarial '
             'autoencoder with a graph neural network classifier, a combination of '
             'deep representation learning [42] and learning over graphs [36]. It has '
             'three components that interact during training: an autoencoder, a '
             'discriminator, and a graph-based classifier (Figure 2.4).')
    add_para(doc,
             'The **autoencoder** compresses the selected feature vector x into a '
             'latent representation z and reconstructs the input from it. The '
             'encoder consists of dense layers with ReLU activations, dropout for '
             'regularisation [39] and batch normalisation [38] for stable training; an '
             'attention block then reweights the units of the last hidden layer [35] '
             'before the latent code is formed. The decoder mirrors the encoder and '
             'ends in a sigmoid layer, and it is trained with the mean squared '
             'reconstruction error [33]. The reconstruction error of a row doubles '
             'as an anomaly score, so the model can also flag unusual events without '
             'using any labels.')
    add_para(doc,
             'The **discriminator** is the adversarial part. It receives encoder '
             'latents as real examples and random vectors drawn from a normal prior '
             'as fake examples, and it is trained with binary cross-entropy to tell '
             'them apart [34]. Alternately, the encoder is trained to fool the '
             'discriminator, which pushes the latent codes towards the prior '
             'distribution and prevents the autoencoder from memorising the training '
             'rows. This construction follows the adversarial autoencoder of [2]; the '
             'weights are initialised with the Xavier-uniform scheme [40], and the '
             'latent dimension is tuned on validation data.')
    add_para(doc,
             'The **classifier** operates on a graph built over the latents: two '
             'latent vectors are connected when their cosine similarity exceeds 0.7, '
             'and the graph is passed through two dense graph layers and a softmax '
             'head [36], [37]. The graph lets the classifier use the neighbourhood '
             'structure of an event, so events that look similar in latent space '
             'receive consistent labels \u2014 the property [2] exploits for '
             'proactive threat hunting. The adjacency matrix is stored sparsely, and '
             'the graph is built per mini-batch in this study, because a dense matrix '
             'over the whole training set is not practical at RADAR\u2019s scale. '
             'The paper\u2019s equations apply the weight matrix to the node '
             'representation only; therefore this study reports both the faithful '
             'variant and a message-passing variant in which the neighbourhood '
             'aggregation H\u2032 = ReLU(\u00c2 H W) with a normalised adjacency '
             '\u00c2 is applied explicitly, and it states which result belongs to '
             'which variant.')
    add_figure(doc, os.path.join(FIGDIR, 'fig2_4_a2gpth.png'),
               'Fig 2.4: Architecture of the A2G-PTH model (adapted from [2])',
               width_cm=13.0)

    h2(doc, '2.8  Evaluation Metrics')
    add_para(doc,
             'Because only a minority of the events are ransomware, accuracy alone '
             'is misleading: a detector that labels every event as goodware is 91 % '
             'accurate on the primary file while catching nothing. The study '
             'therefore reports precision, recall, F1 and ROC-AUC, always computed '
             'for the ransomware class (class 1). Precision is the share of flagged '
             'events that are truly ransomware, recall the share of ransomware '
             'events that are flagged, and F1 their harmonic mean [41]. ROC-AUC '
             'summarises the ranking quality over all thresholds [23], and the '
             'precision-recall AUC is added because it is the more informative '
             'summary under heavy imbalance [24].')
    add_para(doc,
             'Two recall-oriented additions are reported as well. F2 weights recall '
             'twice as much as precision and is closer to how a detection console '
             'trades missed attacks against false alerts, and the false positive and '
             'false negative rates make the two error kinds directly comparable '
             '(FPR drives alert fatigue, FNR describes missed attacks). Every '
             'configuration is repeated over several random seeds and reported as '
             'mean \u00b1 standard deviation, since both reference papers report '
             'single-seed results. Alongside detection quality, the study records '
             'the computational cost of each configuration: feature selection time, '
             'training time, prediction time and model size, using the same '
             'definitions as [1].')
