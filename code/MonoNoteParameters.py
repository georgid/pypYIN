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

import numpy as np
import sys
import os

from src.onsets.OnsetSmoothing import OnsetSmoothingFunction

distance_in_secs = 0.058 # corresponds to around 10 frames with hopsize 256
DELTA = 0.3

class MonoNoteParameters(object):
    def __init__(self, with_bar_dependent_probs, hop_time):
        self.minPitch = 35
        self.DISTANCES  = int(round(distance_in_secs / hop_time)) # consider frames until this distance far from an event (unit: frames) 
        self.nPPS = 3  # 3 steps per semitone
        self.nS = 69
        self.nSPP = 3  # states per pitch: attack, sustain, silence
        self.n = 0
        self.initPi = np.array([], dtype=np.float64)
        self.pAttackSelftrans = 0.9
        self.pStableSelftrans = 0.99
        self.pStable2Silent = 0.01
        self.pSilentSelftrans = 0.9999
        self.sigma2Note = 0.7
        self.maxJump = 13.0
        self.pInterSelftrans = 0.0
        self.priorPitchedProb = 0.7
        self.priorWeight = 0.5
        self.minSemitoneDistance = 0.5
        self.sigmaYinPitchAttack = 5.0
        self.sigmaYinPitchStable = 0.8
        self.sigmaYinPitchInter = 0.1
        self.yinTrust = 0.1
        
        if with_bar_dependent_probs:
            self.barPositionProbs = [0.92, 0.45, 0.8, 0.8, 0.92, 0.65, 0.85, 0.5, 0.6] # aksak. probabilities of note onset at a position for a bar: taken from figure 5 in http://www.rhythmos.org/MMILab-Andre_files/JNMR2014_a_Holzapfel.pdf
#             self.barPositionProbs = [0.90, 0.25, 0.8, 0.85, 0.5, 0.95, 0.6, 0.9, 0.3, 0.5] # curcuna
#             self.barPositionProbs = [0.75, 0.7, 0.55, 0.75, 0.85, 0.5, 0.75, 0.45] # duyek
            self.barPositionDistance_Probs = np.zeros((len(self.barPositionProbs), self.DISTANCES))
            
            # create array here using smoothing by distance from event
            self.osf = OnsetSmoothingFunction(self.DISTANCES)
            for ibarPos in range(len(self.barPositionProbs)):
                for iDist in range(self.DISTANCES):    
                    currProb = self.osf.calcOnsetWeight(iDist) * self.barPositionProbs[ibarPos] # TODO: normalize highest Weight to be 1
                    self.barPositionDistance_Probs[ibarPos,iDist] = currProb
            self.barPositionDistance_Probs = np.power(self.barPositionDistance_Probs, DELTA) # raise to power to control influence of bars
        else:
            self.barPositionDistance_Probs = [1-self.pSilentSelftrans] # in case of no bar-positions used
        
          
        

        self.n = self.nPPS * self.nS * self.nSPP 