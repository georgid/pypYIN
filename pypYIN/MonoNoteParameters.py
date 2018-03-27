# -*- coding: utf-8 -*-

'''
     This is a set with Parameters  
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
'''

import numpy as np
import sys


from onsets.OnsetSmoothing import OnsetSmoothingFunction

WITH_MAKAM = 0

WITH_BEAT_ANNOS = 0 #  read beats from annotation, if set, it means we do beat-aware note onset detection 
WITH_MELODIA = 1 # use melodia for pitch tracking. =1 to reproduce results of ISMIR 2017 paper
WITH_ONSETS_SAME_PITCH = 1 # detect onsets on same pitch. ==0 to reproduce results of ISMIR 2017 paper 
WITH_VOCAL_SEGMENTS = 0

STEPS_PER_SEMITONE = 3 # =1 to reproduce results of paper ISMIR 2017
NUM_SEMITONES = 35

# STEPS_PER_SEMITONE = 2
# NUM_SEMITONES = 15

PITCH_PROB = 0.9  # prior probabilitiy of voice being pitch

################ parameters needed when WITH BEAT DETECTION ###############################
WITH_NOTES_STATES = 0 # no note states, e.g. decoding equivalent to the default Pattern Tracking Processor.  
WITH_NOTES_STATES = 1


SMOOTHING_WINDOW = 0.058 # corresponds to around 10 frames when hopsize=256
# SMOOTHING_WINDOW = 0
DELTA = 0.3 # weight of importance of the note_onset_probs
DELTA = 1

# probabilities of note onset at a position for a bar: taken from figure 5 in http://www.rhythmos.org/MMILab-Andre_files/JNMR2014_a_Holzapfel.pdf
note_onset_probs = dict()
note_onset_probs['aksak'] = [0.92, 0.45, 0.8, 0.8, 0.92, 0.65, 0.85, 0.5, 0.6] 
note_onset_probs['curcuna'] = [0.90, 0.25, 0.8, 0.85, 0.5, 0.95, 0.6, 0.9, 0.3, 0.5] # curcuna
note_onset_probs['kapali_curcuna'] = [0.90, 0.25, 0.8, 0.85, 0.5, 0.95, 0.6, 0.9, 0.3, 0.5] # same as curcuna
note_onset_probs['duyek'] = [0.75, 0.7, 0.55, 0.75, 0.85, 0.5, 0.75, 0.45] # duyek

note_onset_probs['44'] = [0.9, 0.6, 0.9, 0.6] # 4/4
# note_onset_probs['turkaksagi_ii'] = [] # TODO

class MonoNoteParameters(object):
    def __init__(self, steps_per_semitone, number_semitones, with_bar_dependent_probs, hop_time, usul_type):
        self.minPitch = 52 # in MIDI
        self.DISTANCES  = int(round(SMOOTHING_WINDOW / hop_time)) # consider frames until this distance far from an event (unit: frames) 
        self.nPPS = steps_per_semitone  #  steps per semitone
        self.nS = number_semitones # number of semitones
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
            if usul_type in note_onset_probs.keys():
                self.barPositionProbs = note_onset_probs[usul_type]
            else:
                sys.exit('there is no onset probability pattern defined for usul {} '.format(usul_type))
            self.barPositionDistance_Probs = np.zeros((len(self.barPositionProbs), self.DISTANCES))
            
            # create array here using smoothing by distance from event
            self.osf = OnsetSmoothingFunction(self.DISTANCES)
            for ibarPos in range(len(self.barPositionProbs)):
                for iDist in range(self.DISTANCES):    
                    currProb = self.osf.calcOnsetWeight(iDist) * self.barPositionProbs[ibarPos] # TODO: normalize highest Weight to be 1
                    self.barPositionDistance_Probs[ibarPos,iDist] = currProb
            self.barPositionDistance_Probs = np.power(self.barPositionDistance_Probs, DELTA) # raise to power to control influence of bars
        else: # no bar-positions used
            self.barPositionDistance_Probs = [1-self.pSilentSelftrans] 
        

        self.n = self.nPPS * self.nS * self.nSPP 