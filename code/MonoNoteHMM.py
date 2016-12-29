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
from SparseHMM import SparseHMM
from MonoNoteParameters import MonoNoteParameters
from math import *
from scipy.stats import norm
import sys
import logging



class MonoNoteHMM(SparseHMM):
    def __init__(self, with_bar_dependent_probs, hopTime):
        self.with_bar_dependent_probs = with_bar_dependent_probs
        self.par = MonoNoteParameters(with_bar_dependent_probs, hopTime)
        if with_bar_dependent_probs: # list of trans matrices
            SparseHMM.__init__(self, self.par.barPositionDistance_Probs.shape[0], self.par.barPositionDistance_Probs.shape[1] + 1 ) # last is limit distance
        else: # only one trans matrix
            SparseHMM.__init__(self, 1,1 )
        self.pitchDistr = []
        self.build(with_bar_dependent_probs)

    def calculatedObsProb(self, pitch_contour_and_prob):
        '''
        calculate the obs probability for all states of one pitch
        
        refer to section 3.2. equation (1)
        
        Parameters
        ---------------
        pitch_contour_and_prob: nd.array, shape=(t,2)
            array of (pitch, probability) pairs 
        
        Returns
        ----------------
        obs_probs: nd.array, shape=(self.n,t)
            pdfs of states, before normalization
        '''
        # pitchProb is a pair (pitches and its probability)
       
        pitches = pitch_contour_and_prob[:,0]
        indices_non_zero_pitch = np.where(pitches > 0)[0]
        factorTrust = np.power(pitch_contour_and_prob[indices_non_zero_pitch,1], self.par.yinTrust) # how much pitch estimate is trusted
        
#         if nCandidate == 0: # GEORGI: non-vocal frames with empty pitch should have zero prob?
#             pIsPitched = 0
        obs_probs = np.zeros((self.par.n, pitches.shape[0]), dtype=np.float64)
        for i in range(self.par.n): # loop though states
            if i % self.par.nSPP != 2: #  attack and sustain states
                
                    obs_probs[i, :] = 1 # zero pitched remain with const prob= 1
                    obs_probs[i, indices_non_zero_pitch] = factorTrust * self.pitchDistr[i].pdf(pitches[indices_non_zero_pitch]) # computation of actual pdf
     
        return obs_probs
    
    
        
    def normalize_obs_probs(self, obs_probs, pitch_contour_and_prob):
        '''
        Seconds loop needed because easier to normalize by z
        Parameters
        ----------------
        obs_probs: nd.array, shape=(self.n,t)
        '''
        z = np.sum(obs_probs,axis = 0)  # normalizing factor 
        z[np.where(z==0)] = 1 # avoid  division by zero
       
        
        # the pitched probability, check Ryynanen's paper
        posteriorPichedProb = pitch_contour_and_prob[:,1] * (1-self.par.priorWeight) + self.par.priorPitchedProb * self.par.priorWeight
        
        ######### normalize 
        number_silent_states = self.par.nPPS * self.par.nS
        for i in range(self.par.n): 
            if i % self.par.nSPP != 2: # non-silent states
                    obs_probs[i,:] =  obs_probs[i,:] / z # normalize so that prob at non-voiced states sums up to 1
                    obs_probs[i,:] *= posteriorPichedProb
            else:  # the prob of silent states based on detectd pitch 
               
                obs_probs[i,:] = (1-posteriorPichedProb) / (number_silent_states)

        return obs_probs

    def getMidiPitch(self, index):
        return self.pitchDistr[index].mean()

    def getFrequency(self, index):
        return 440 * pow(2.0, (self.pitchDistr[index].mean()-69)/12)

    def build(self, with_bar_dependent_probs):
        # the states are organised as follows:
        # 0-2. lowest pitch
        #    0. attack state
        #    1. stable state
        #   2. silent state
        # 3-5. second-lowest pitch
        #    3. attack state
        #    ...

        ################## observation distributions
        for iState in range(self.par.n):
            self.pitchDistr.append(norm(loc=0, scale=1))
            if iState % self.par.nSPP == 2: # silent state starts tracking
                self.init = np.append(self.init, np.float64(1.0/(self.par.nS * self.par.nPPS)))
            else:
                self.init = np.append(self.init, np.float64(0.0))

        for iPitch in range(self.par.nS * self.par.nPPS):
            index = iPitch * self.par.nSPP   # each pitch has 3 state
            mu = self.par.minPitch + iPitch * 1.0/self.par.nPPS
            self.pitchDistr[index] = norm(loc=mu, scale=self.par.sigmaYinPitchAttack)
            self.pitchDistr[index+1] = norm(loc=mu, scale=self.par.sigmaYinPitchStable)
            self.pitchDistr[index+2] = norm(loc=mu, scale=1.0) # dummy
        
        
        ################### set sparse transition probabilities self.transProbs
        # this might be the note transition probability function
        noteDistanceDistr = norm(loc=0, scale=self.par.sigma2Note)

        
        logging.warning('building transition matrix...')    
        for iPitch in range(self.par.nS * self.par.nPPS): # loop through all notes and set sparse transition probabilities self.transProbs
            index = iPitch * self.par.nSPP

            # transitions from attack state
            self.fromIndex = np.append(self.fromIndex, np.uint64(index))
            self.toIndex = np.append(self.toIndex, np.uint64(index))
            for iBarPos in range(self.transProbs.shape[0]):
                for iDistance in range(self.transProbs.shape[1]): 
                    self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance], np.float64(self.par.pAttackSelftrans))

            self.fromIndex = np.append(self.fromIndex, np.uint64(index))
            self.toIndex = np.append(self.toIndex, np.uint64(index+1))
            for iBarPos in range(self.transProbs.shape[0]):
                for iDistance in range(self.transProbs.shape[1]): 
                    self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance], np.float64(1-self.par.pAttackSelftrans))

            # transitions from stable state
            self.fromIndex = np.append(self.fromIndex, np.uint64(index+1))
            self.toIndex = np.append(self.toIndex, np.uint64(index+1)) # to itself
            for iBarPos in range(self.transProbs.shape[0]):
                for iDistance in range(self.transProbs.shape[1]): 
                    self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance], np.float64(self.par.pStableSelftrans))

            self.fromIndex = np.append(self.fromIndex, np.uint64(index+1))
            self.toIndex = np.append(self.toIndex, np.uint64(index+2)) # to silent
            for iBarPos in range(self.transProbs.shape[0]):
                for iDistance in range(self.transProbs.shape[1]): 
                    self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance], np.float64(self.par.pStable2Silent))

            # the "easy" transitions from silent state
            self.fromIndex = np.append(self.fromIndex, np.uint64(index+2))
            self.toIndex = np.append(self.toIndex, np.uint64(index+2))
            for iBarPos in range(self.transProbs.shape[0]):
                for iDistance in range(self.transProbs.shape[1]-1): 
                    self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance], np.float64(1 - self.par.barPositionDistance_Probs[iBarPos, iDistance] ) ) # prob. of wait in silence 
                self.transProbs[iBarPos, -1] = np.append(self.transProbs[iBarPos, -1], np.float64(self.par.pSilentSelftrans ) ) # last distance is the default fixed silence self transition
            
            # the more complicated transitions from the silent
            # this prob only applies to transitions from silent to non silent
            # which is the note transition
            probSumSilent = 0.0

            tempTransProbSilent = []
            for jPitch in range(self.par.nS * self.par.nPPS): # compute fromIndex, toIndex and tempTransProbsSilent: the weighted from silent to non-silent
                fromPitch = iPitch
                toPitch = jPitch
                semitoneDistance = fabs(fromPitch - toPitch) * 1.0 / self.par.nPPS

                if semitoneDistance == 0 or \
                        (semitoneDistance > self.par.minSemitoneDistance and semitoneDistance < self.par.maxJump): # store only transitions to states, which are within meaningful range 

                    toIndex = jPitch * self.par.nSPP  # note attack index

                    tempWeightSilent = noteDistanceDistr.pdf(semitoneDistance) # transitions according to note distance form weights that sum to one
                    probSumSilent += tempWeightSilent

                    tempTransProbSilent.append(tempWeightSilent)

                    self.fromIndex = np.append(self.fromIndex, np.uint64(index+2))  # from a silence
                    self.toIndex = np.append(self.toIndex, np.uint64(toIndex))  # to an attack
            
            for i in range(len(tempTransProbSilent)): # append to transProbs  the computed  tempProbSilent
                givenPitchTransProbSilent = tempTransProbSilent[i]/probSumSilent
                givenPitch_barPositionDistance_Probs = self.par.barPositionDistance_Probs  * givenPitchTransProbSilent # bar-position probs weighted by transitions for transition towards given pitch
                
                for iBarPos in range(self.transProbs.shape[0]):
                    for iDistance in range(self.transProbs.shape[1]-1): 
                        self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance],
                                          np.float64( givenPitch_barPositionDistance_Probs[iBarPos, iDistance]) ) 
                    # last distance is the default fixed silence-to-note transition
                    self.transProbs[iBarPos, -1] = np.append(self.transProbs[iBarPos, -1],
                                          np.float64( (1-self.par.pSilentSelftrans) * givenPitchTransProbSilent  ) ) 