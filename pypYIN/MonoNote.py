# -*- coding: utf-8 -*-

'''
 * Copyright (C) 2015  Music Technology Group - Universitat Pompeu Fabra
 *
 * This file is part of pypYIN
 *
 * pypYIN is free software: you can redistribute it and/or modify it under
 * the terms of the GNU Affero General Public License as published by the Free
 * Software Foundation (FSF), either version 3 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
 * details.
 *
 * You should have received a copy of the Affero GNU General Public License
 * version 3 along with this program.  If not, see http://www.gnu.org/licenses/
 *
 * If you have any problem about this python version code, please contact: Rong Gong
 * rong.gong@upf.edu
 *
 * If you have any problem about this algorithm, I suggest you to contact: Matthias Mauch
 * m.mauch@qmul.ac.uk who is the original C++ version author of this algorithm
 *
 * If you want to refer this code, please consider this article:
 *
 * M. Mauch and S. Dixon,
 * “pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions”,
 * in Proceedings of the IEEE International Conference on Acoustics,
 * Speech, and Signal Processing (ICASSP 2014), 2014.
 *
 * M. Mauch, C. Cannam, R. Bittner, G. Fazekas, J. Salamon, J. Dai, J. Bello and S. Dixon,
 * “Computer-aided Melody Note Transcription Using the Tony Software: Accuracy and Efficiency”,
 * in Proceedings of the First International Conference on Technologies for
 * Music Notation and Representation, 2015.
'''

from MonoNoteHMM import MonoNoteHMM
from MonoNoteParameters import MonoNoteParameters
import logging
import sys
import numpy as np


class FrameOutput(object):
    def __init__(self, frameNumber, pitch, noteState):
        self.frameNumber = frameNumber
        self.pitch = pitch
        self.noteState = noteState

class MonoNote(object):

    def __init__(self, STEPS_PER_SEMITONE, NUM_SEMITONES, with_bar_dependent_probs, hopTime, usul_type):
        '''
        create hmm and build its transition matrix
        '''
        self.with_bar_dependent_probs = with_bar_dependent_probs
        self.hmm = MonoNoteHMM(STEPS_PER_SEMITONE, NUM_SEMITONES, with_bar_dependent_probs, hopTime, usul_type)
        
        self.hmm.build_trans_probs(with_bar_dependent_probs)
        self.hmm.build_obs_model()
        
    def process(self, pitch_contour_and_prob, bar_position_ts, bar_labels, hop_time):
        '''
        compute obs. probabilities and decode with Viterbi
         
        Parameters
        ----------------------
        pitch_contour_and_prob
            pitch observation feature
        bar_position_ts: list
            timestamps of bar positions
        bar_labels: list
            labels of bar types corresponding to timestamps 
        '''
        
        obs_probs = self.hmm.calculatedObsProb(pitch_contour_and_prob)
        obs_probs = self.hmm.normalize_obs_probs(obs_probs, pitch_contour_and_prob)
        obs_probs_T = obs_probs.T
        
        self.create_beatPositions(obs_probs_T, bar_position_ts, bar_labels, hop_time)
        path, _ = self.hmm.decodeViterbi(obs_probs_T) # transpose to have time t as first dimension 

        out = [] # convert to a list of FrameOutput type
        for iFrame in range(len(path)):
            currPitch = -1.0
            stateKind = 0

            currPitch = self.hmm.par.minPitch + (path[iFrame]/self.hmm.par.nSPP) * 1.0/self.hmm.par.nPPS
            stateKind = (path[iFrame]) % self.hmm.par.nSPP + 1 # 1: attack, 2: sustain, 3: silence

            out.append(FrameOutput(iFrame, currPitch, stateKind))

        return out
    
    def create_beatPositions(self,obs_probs_T, beat_position_ts, beat_labels, hop_time):
        '''
        load beat annotaiton. and create beat position markers at frames  
        creates MonoNoteHMM.beatPositions: shape(time, 2); 
            dimension 0: one if no bar pos, else zero; 
            dimension 1: bar pos label (form 0 to num_beats in usul)
        '''
        nFrames = obs_probs_T.shape[0]
        self.hmm.beatPositions = np.zeros((nFrames, 2)) # create output 
        for beat_pos_ts, beat_label in zip(beat_position_ts, beat_labels ):
            iFrame = ts_to_frame(beat_pos_ts, hop_time)
            if iFrame >= nFrames-1:
                logging.warning('bar position ts beyond duration of audio... ignoring')
                break
            self.hmm.beatPositions[iFrame,0] = 1
            self.hmm.beatPositions[iFrame,1] = int(beat_label) - 1 

def frame_to_ts(frame_number, hop_time):
    return float(hop_time * frame_number )
def ts_to_frame(ts, hop_time):
    return round(ts/ hop_time)