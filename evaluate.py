###############################################################################
#
#   Copyright 2019 Secretaría de Estado para el Avance Digital (SEAD)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
#                      PharmaCoNER Evaluation Script
#
# This script is distributed as apart of the Pharmacological Substances,
# Compounds and proteins and Named Entity Recognition (PharmaCoNER) task.
# It is slightly based on the evaluation script from the i2b2 2014
# Cardiac Risk and Personal Health-care Information (PHI) tasks. It is
# intended to be used via command line:
#
# $> python evaluate.py [ner|indexing] GOLD SYSTEM
#
# It produces Precision, Recall and F1 (P/R/F1) measures for both subtracks.
#
# SYSTEM and GOLD may be individual files or also directories in which case
# all files in SYSTEM will be compared to files the GOLD directory based on
# their file names.
#
# Basic Examples:
#
# $> python evaluate.py ner gold/01.ann system/run1/01.ann
#
# Evaluate the single system output file '01.ann' against the gold standard
# file '01.ann' for the NER subtrack. Input files in BRAT format.
#
# $> python evaluate.py indexing gold/01.tsv system/run1/01.tsv
#
# Evaluate the single system output file '01.tsv' against the gold standard
# file '01.tsv' for the Concept Indexing subtrack. Input files in TSV format.
#
# $> python evaluate.py indexing gold/ system/run1/
#
# Evaluate the set of system outputs in the folder system/run1 against the
# set of gold standard annotations in gold/ using the Concept Indexing
# subtrack. Input files in TSV format.
#
# $> python evaluate.py ner gold/ system/run1/ system/run2/ system/run3/
#
# Evaluate the set of system outputs in the folder system/run1, system/run2
# and in the folder system/run3 against the set of gold standard annotations
# in gold/ using the NER subtrack. Input files in BRAT format.

import os
import argparse
from classes import BratAnnotation, IndexingAnnotation, NER_Evaluation, Indexing_Evaluation
from collections import defaultdict


def get_document_dict_by_system_id(system_dirs, annotation_format):
    """Takes a list of directories and returns annotations. """

    documents = defaultdict(lambda: defaultdict(int))

    for d in system_dirs:
        for fn in os.listdir(d):
            if fn.endswith(".ann") or fn.endswith(".tsv"):
                sa = annotation_format(d + fn)
                documents[sa.sys_id][sa.id] = sa

    return documents


def evaluate(gs, system, annotation_format, subtrack, **kwargs):
    """Evaluate the system by calling either NER_evaluation or Indexing_Evaluation.
    'system' can be a list containing either one file,  or one or more
    directories. 'gs' can be a file or a directory. """

    gold_ann = {}
    evaluations = []

    # Strip verbose keyword if it exists
    try:
        verbose = kwargs['verbose']
        del kwargs['verbose']
    except KeyError:
        verbose = False

    # Handle if two files were passed on the command line
    if os.path.isfile(system[0]) and os.path.isfile(gs):
        if (system[0].endswith(".ann") and gs.endswith(".ann")) or \
                (system[0].endswith(".tsv") or gs.endswith(".tsv")):
            gs = annotation_format(gs)
            sys = annotation_format(system[0])
            e = subtrack({sys.id: sys}, {gs.id: gs}, **kwargs)
            e.print_docs()
            evaluations.append(e)

    # Handle the case where 'gs' is a directory and 'system' is a list of directories.
    elif all([os.path.isdir(sys) for sys in system]) and os.path.isdir(gs):
        # Get a dict of gold annotations indexed by id

        for filename in os.listdir(gs):
            if filename.endswith(".ann") or filename.endswith(".tsv"):
                annotations = annotation_format(gs + filename)
                gold_ann[annotations.id] = annotations

        for system_id, system_ann in sorted(get_document_dict_by_system_id(system, annotation_format).items()):
            e = subtrack(system_ann, gold_ann, **kwargs)
            e.print_report(verbose=verbose)
            evaluations.append(e)

    else:
        Exception("Must pass file file or [directory/]+ directory/"
                  "on command line!")

    return evaluations[0] if len(evaluations) == 1 else evaluations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation script for the PharmaCoNER track.")

    parser.add_argument("subtrack",
                        choices=["ner", "indexing"],
                        help="Subtrack")
    parser.add_argument('-v', '--verbose',
                        help="List also scores for each document",
                        action="store_true")
    parser.add_argument("gs_dir",
                        help="Directory to load GS from")
    parser.add_argument("sys_dir",
                        help="Directories with system outputs (one or more)",
                        nargs="+")

    args = parser.parse_args()

    evaluate(args.gs_dir,
             args.sys_dir,
             BratAnnotation if args.subtrack == "ner" else IndexingAnnotation,
             NER_Evaluation if args.subtrack == "ner" else Indexing_Evaluation,
             verbose=args.verbose)
