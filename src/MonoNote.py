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


class FrameOutput(object):
    def __init__(self, frameNumber, pitch, noteState):
        self.frameNumber = frameNumber
        self.pitch = pitch
        self.noteState = noteState

class MonoNote(object):

    def __init__(self):
        self.hmm = MonoNoteHMM()

    def process(self, pitch_contour_and_prob):
        
        logging.warning('computing note state observation likelihoods...')
        
        obs_probs = self.hmm.calculatedObsProb(pitch_contour_and_prob)
        obs_probs = self.hmm.normalize_obs_probs(obs_probs, pitch_contour_and_prob)
        obs_probs_T = obs_probs.T
        path, _ = self.hmm.decodeViterbi(obs_probs_T) # transpose to have time t as first dimension 

        out = [] # convert to a list of FrameOutput type
        for iFrame in range(len(path)):
            currPitch = -1.0
            stateKind = 0

            currPitch = self.hmm.par.minPitch + (path[iFrame]/self.hmm.par.nSPP) * 1.0/self.hmm.par.nPPS
            stateKind = (path[iFrame]) % self.hmm.par.nSPP + 1 # 1: attack, 2: sustain, 3: silence

            out.append(FrameOutput(iFrame, currPitch, stateKind))

        return out