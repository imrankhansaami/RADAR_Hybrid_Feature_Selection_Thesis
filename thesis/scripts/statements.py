"""Statements: data availability, use of AI tools, ethics."""
from lib import add_para, chapter_heading


def build(doc, st):
    chapter_heading(doc, 'Statements', page_break_before=True)
    add_para(doc,
             '**Data availability.** This study analyses the publicly released '
             'RADAR dataset [3]: Sysmon event telemetry collected from goodware '
             'and ransomware executions in a controlled laboratory environment. '
             'No new telemetry was collected for this thesis, and the ransomware '
             'samples were not executed by the authors. The engineered CSV '
             'variants used in the runs are derived from the published dataset; '
             'the scripts, configuration files and result files that produce '
             'every number in Chapter 4 accompany this report so that each '
             'result can be traced back to a run.')
    add_para(doc,
             '**Use of AI tools.** During the preparation of this work the '
             'authors used an AI-based assistant to help implement the '
             'experimental pipeline, prepare the figures and format the '
             'manuscript. The study design was fixed before the runs, all '
             'experiments were executed on the authors\u2019 own machine, and '
             'every reported number was verified against the stored run outputs. '
             'The authors reviewed and edited all content and take full '
             'responsibility for the thesis.')
    add_para(doc,
             '**Ethics statement.** The study uses a previously collected, '
             'publicly available dataset of host-level telemetry; no human '
             'participants, personal data or live malware were involved in this '
             'work. The dataset was collected by its original authors in a '
             'controlled laboratory environment and is used here under its '
             'published terms; all sources are credited in the reference list '
             'at the end of this report.')
