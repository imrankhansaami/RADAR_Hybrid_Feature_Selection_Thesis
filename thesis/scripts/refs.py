"""References list."""
import re
from docx.shared import Pt, Cm
from lib import add_para, chapter_heading, set_run

REFS = [
    'A. Goni, R. J. Momtahina and R. R. Chowdhury, "A Hybrid Voting-Based Feature Selection Approach for Identifying Intrusions in IoT Networks," in Proc. IEEE WIECON-ECE, Cox\u2019s Bazar, Bangladesh, Dec. 2025.',
    'A. Goni, R. J. Momtahina and R. R. Chowdhury, "A2G-PTH: An Adversarial Autoencoder Graph Neural Network for Proactive Threat Hunting in IoT," in Proc. 28th International Conference on Computer and Information Technology (ICCIT), Cox\u2019s Bazar, Bangladesh, Dec. 2025.',
    'J. Ispahany, O. B. Deho, M. R. Islam, M. A. Khan and M. Z. Islam, "RADAR: a realistic dataset for advancing ransomware detection," Cybersecurity, vol. 8, 2025, doi: 10.1186/s42400-025-00435-9; dataset doi: 10.5281/zenodo.14542547.',
    'R. Mills, "LUFlow Network Intrusion Detection Data Set," Kaggle dataset.',
    '"ACI IoT Network Traffic Dataset 2023," IEEE DataPort, 2023.',
    'A. Goni, M. U. F. Jahangir and R. R. Chowdhury, "Optimized Intrusion Detection in IoT Networks Using Machine Learning for Enhanced Security," in Proc. 27th ICCIT, 2024, doi: 10.1109/ICCIT64611.2024.11022016.',
    'N. Verma, N. Kumar, K. Singh, A. Aljohani, A. Sinha and S. A. Hussain, "A novel univariate feature selection with ANOVA F-test-based machine learning model for Intrusion Detection Framework of Robotics system," Applied Artificial Intelligence, vol. 39, no. 1, 2025.',
    'H. Alazzam, A. Sharieh and K. E. Sabri, "A feature selection algorithm for intrusion detection system based on Pigeon Inspired Optimizer," Expert Systems with Applications, vol. 148, 2020.',
    'T. Altaf, X. Wang, W. Ni, G. Yu, R. P. Liu and R. Braun, "A new concatenated Multigraph Neural Network for IoT intrusion detection," Internet of Things, vol. 22, 2023.',
    'J. Ghadermazi, S. Hore, A. Shah and N. D. Bastian, "GTAE-IDS: Graph Transformer-Based Autoencoder Framework for Real-Time Network Intrusion Detection," IEEE Transactions on Information Forensics and Security, vol. 20, pp. 4026\u20134041, 2025.',
    'I. Guyon and A. Elisseeff, "An Introduction to Variable and Feature Selection," Journal of Machine Learning Research, vol. 3, pp. 1157\u20131182, 2003.',
    'I. Guyon, J. Weston, S. Barnhill and V. Vapnik, "Gene Selection for Cancer Classification using Support Vector Machines," Machine Learning, vol. 46, pp. 389\u2013422, 2002.',
    'C. E. Shannon, "A Mathematical Theory of Communication," Bell System Technical Journal, vol. 27, pp. 379\u2013423, 1948.',
    'R. A. Fisher, "The use of multiple measurements in taxonomic problems," Annals of Eugenics, vol. 7, pp. 179\u2013188, 1936.',
    'K. Pearson, "Mathematical Contributions to the Theory of Evolution. III. Regression, Heredity, and Panmixia," Philosophical Transactions of the Royal Society A, vol. 187, pp. 253\u2013318, 1896.',
    'J. L. Rodgers and W. A. Nicewander, "Thirteen Ways to Look at the Correlation Coefficient," The American Statistician, vol. 42, no. 1, pp. 59\u201366, 1988.',
    'A. L. Blum and P. Langley, "Selection of relevant features and examples in machine learning," Artificial Intelligence, vol. 97, pp. 245\u2013271, 1997.',
    'Y. Freund and R. E. Schapire, "A Decision-Theoretic Generalization of On-Line Learning and an Application to Boosting," Journal of Computer and System Sciences, vol. 55, no. 1, pp. 119\u2013139, 1997.',
    'L. Breiman, J. Friedman, R. Olshen and C. Stone, Classification and Regression Trees, Chapman and Hall, 1984.',
    'E. Fix and J. L. Hodges, "Discriminatory Analysis: Nonparametric Discrimination; Consistency Properties," USAF School of Aviation Medicine, Report 4, 1951.',
    'G. H. John and P. Langley, "Estimating Continuous Distributions in Bayesian Classifiers," in Proc. Conference on Uncertainty in Artificial Intelligence (UAI), 1995.',
    'D. R. Cox, "The Regression Analysis of Binary Sequences," Journal of the Royal Statistical Society B, vol. 20, no. 2, pp. 215\u2013242, 1958.',
    'T. Fawcett, "An introduction to ROC analysis," Pattern Recognition Letters, vol. 27, no. 8, pp. 861\u2013874, 2006.',
    'T. Saito and M. Rehmsmeier, "The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets," PLoS ONE, vol. 10, no. 3, 2015.',
    'N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, "SMOTE: Synthetic Minority Over-sampling Technique," Journal of Artificial Intelligence Research, vol. 16, pp. 321\u2013357, 2002.',
    'H. He and E. A. Garcia, "Learning from Imbalanced Data," IEEE Transactions on Knowledge and Data Engineering, vol. 21, no. 9, pp. 1263\u20131284, 2009.',
    'S. Kaufman, S. Rosset and C. Perlich, "Leakage in Data Mining: Formulation, Detection, and Avoidance," ACM Transactions on Knowledge Discovery from Data, vol. 6, no. 4, 2012.',
    'G. Widmer and M. Kubat, "Learning in the Presence of Concept Drift and Hidden Contexts," Machine Learning, vol. 23, pp. 69\u2013101, 1996.',
    'Microsoft, "Sysmon v15," Sysinternals documentation, 2023.',
    'MITRE, "ATT&CK Enterprise Matrix: Ransomware," 2025.',
    'Sophos, "The State of Ransomware 2025," Sophos report, 2025.',
    'Chainalysis, "The 2025 Crypto Crime Report," Chainalysis report, 2025.',
    'I. Goodfellow, Y. Bengio and A. Courville, Deep Learning, MIT Press, 2016.',
    'I. J. Goodfellow, J. Pouget-Abadie, M. Mirza, B. Xu, D. Warde-Farley, S. Ozair, A. Courville and Y. Bengio, "Generative Adversarial Nets," in Proc. NeurIPS, 2014.',
    'A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser and I. Polosukhin, "Attention Is All You Need," in Proc. NeurIPS, 2017.',
    'T. N. Kipf and M. Welling, "Semi-Supervised Classification with Graph Convolutional Networks," in Proc. ICLR, 2017.',
    'P. Velickovic, G. Cucurull, A. Casanova, A. Romero, P. Lio and Y. Bengio, "Graph Attention Networks," in Proc. ICLR, 2018.',
    'S. Ioffe and C. Szegedy, "Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift," in Proc. ICML, 2015.',
    'N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. Salakhutdinov, "Dropout: A Simple Way to Prevent Neural Networks from Overfitting," Journal of Machine Learning Research, vol. 15, pp. 1929\u20131958, 2014.',
    'X. Glorot and Y. Bengio, "Understanding the difficulty of training deep feedforward neural networks," in Proc. AISTATS, 2010.',
    'M. Sokolova and G. Lapalme, "A systematic analysis of performance measures for classification tasks," Information Processing and Management, vol. 45, no. 4, pp. 427\u2013437, 2009.',
    'Y. LeCun, Y. Bengio and G. Hinton, "Deep learning," Nature, vol. 521, pp. 436\u2013444, 2015.',
    'R. Kohavi and G. H. John, "Wrappers for feature subset selection," Artificial Intelligence, vol. 97, no. 1\u20132, pp. 273\u2013324, 1997.',
    'L. Yu and H. Liu, "Efficient Feature Selection via Analysis of Relevance and Redundancy," Journal of Machine Learning Research, vol. 5, pp. 1205\u20131224, 2004.',
    'R. Tibshirani, "Regression Shrinkage and Selection via the Lasso," Journal of the Royal Statistical Society B, vol. 58, no. 1, pp. 267\u2013288, 1996.',
    'H. Peng, F. Long and C. Ding, "Feature Selection Based on Mutual Information: Criteria of Max-Dependency, Max-Relevance, and Min-Redundancy," IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 27, no. 8, pp. 1226\u20131238, 2005.',
    'L. I. Kuncheva, "A Stability Index for Feature Selection," in Proc. IASTED International Conference on Artificial Intelligence and Applications, 2007.',
    'A. Kalousis, J. Prados and M. Hilario, "Stability of feature selection algorithms: a study on high-dimensional spaces," Knowledge and Information Systems, vol. 12, pp. 95\u2013116, 2007.',
]


def build(doc, st):
    chapter_heading(doc, 'References', page_break_before=True)
    for i, ref in enumerate(REFS, start=1):
        p = add_para(doc, '[' + str(i) + '] ' + ref, space_after=4)
        pf = p.paragraph_format
        pf.left_indent = Cm(1.0)
        pf.first_line_indent = Cm(-1.0)
