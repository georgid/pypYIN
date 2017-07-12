'''
Created on Jul 9, 2017

@author: joro
'''
from eval_note_onsets_script import eval_onsets_one_file, TOLERANCE_TIME
import sys

if __name__ == "__main__":
    # detected = '/Users/joro/workspace/lakh_vocal_segments_dataset/experiments/beat_anno/dido/dido.onsets.tony_nSemi_35_stepsPSemi_1'
    # annot = '/Users/joro/workspace/lakh_vocal_segments_dataset/data/dido/dido.vocal_anno'
    
    F, P, R = eval_onsets_one_file(TOLERANCE_TIME, sys.argv)
    print F,P,R