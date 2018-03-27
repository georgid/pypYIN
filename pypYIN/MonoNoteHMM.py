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
'''

import numpy as np
from SparseHMM import SparseHMM
from MonoNoteParameters import MonoNoteParameters
from math import *
from scipy.stats import norm
import sys
import logging
from pypYIN.MonoNoteParameters import WITH_BEAT_ANNOS



class MonoNoteHMM(SparseHMM):
    '''
    creates the self.transProbs matrix
    self.transProbs : shape (num_beats, num_distances + 1) 
    # num_beats: num_beats in a bar for rhythmic pattern
    # dist_from_beat: distance from beat (in number of frames) last is default (limit distance) transition 
    
    '''
    
    def __init__(self,  STEPS_PER_SEMITONE, NUMBER_SEMITONES, with_bar_dependent_probs, hopTime, usul_type):
        self.with_bar_dependent_probs = with_bar_dependent_probs
        self.par = MonoNoteParameters(STEPS_PER_SEMITONE, NUMBER_SEMITONES, with_bar_dependent_probs, hopTime, usul_type)
        if with_bar_dependent_probs: # list of trans matrices
            num_beats = self.par.barPositionDistance_Probs.shape[0] # num beats in a bar for rhythmic pattern
            dist_from_beat = self.par.barPositionDistance_Probs.shape[1] + 1 # distance from beat (in number of frames) last is default (limit distance) transition
            SparseHMM.__init__(self, num_beats, dist_from_beat ) # 
        else: # only the  trans matrix of model of Mauch
            SparseHMM.__init__(self, 1,1 )
        self.pitchDistr = []
        
        

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
                
                    obs_probs[i, :] = 1 # attack or sustain emits zero pitch with prob= 1
                    obs_probs[i, indices_non_zero_pitch] = factorTrust * self.pitchDistr[i].pdf(pitches[indices_non_zero_pitch]) # computation of actual pdf
     
        return obs_probs
    
    
        
    def normalize_obs_probs(self, obs_probs, pitch_contour_and_prob):
        '''
        Seconds loop though probs because easier to normalize by z
        
        Parameters
        ----------------
        obs_probs: nd.array, shape=(self.n,t)
        '''
        z = np.sum(obs_probs,axis = 0)  # normalizing factor 
        z[np.where(z==0)] = 1 # avoid  division by zero
       
        
        #  probability of each frame being piched: combination of prior and assigned by pitch detection. check Ryynanen's paper
        posteriorPichedProb = pitch_contour_and_prob[:,1] * (1-self.par.priorWeight) + self.par.priorPitchedProb * self.par.priorWeight
        
        ######### normalize 
        number_silent_states = self.par.nPPS * self.par.nS
        for i in range(self.par.n): 
            if i % self.par.nSPP != 2: # non-silent states
                    obs_probs[i,:] =  obs_probs[i,:] / z 
                    obs_probs[i,:] *= posteriorPichedProb # normalize so that prob at non-silent states sums up to posteriorPichedProb
            else:  # silent states
               
                obs_probs[i,:] = (1-posteriorPichedProb) / (number_silent_states) #  probs at silent states sums up to  1-posteriorPichedProb

        return obs_probs

    def getMidiPitch(self, index):
        return self.pitchDistr[index].mean()

    def getFrequency(self, index):
        return 440 * pow(2.0, (self.pitchDistr[index].mean()-69)/12)


    


    def build_obs_model(self):
        '''
        build gmms for pitch observations
        '''
        for iState in range(self.par.n):
            self.pitchDistr.append(norm(loc=0, scale=1))
            if iState % self.par.nSPP == 2: # silent state starts tracking
                self.init = np.append(self.init, np.float64(1.0 / (self.par.nS * self.par.nPPS)))
            else:
                self.init = np.append(self.init, np.float64(0.0))
        
        for iPitch in range(self.par.nS * self.par.nPPS):
            index = iPitch * self.par.nSPP # each pitch has 3 state
            mu = self.par.minPitch + iPitch * 1.0 / self.par.nPPS
            self.pitchDistr[index] = norm(loc=mu, scale=self.par.sigmaYinPitchAttack)
            self.pitchDistr[index + 1] = norm(loc=mu, scale=self.par.sigmaYinPitchStable)
            self.pitchDistr[index + 2] = norm(loc=mu, scale=1.0) # dummy
        

    def build_trans_probs(self, with_bar_dependent_probs):
        # the states are organised as follows:
        # 0-2. lowest pitch
        #    0. attack state
        #    1. stable state
        #   2. silent state
        # 3-5. second-lowest pitch
        #    3. attack state
        #    ...

       
        
        ################### set sparse transition probabilities self.transProbs
        
        # the note transition probability depending on distance
        noteDistanceDistr = norm(loc=0, scale=self.par.sigma2Note)

        
        logging.warning('building transition matrix between note states...')    
        for iPitch in range(self.par.nS * self.par.nPPS): # loop through all discrete pitch states
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
            
            
            tempTransProbSilent, probSumSilent = self._build_silent_to_attack(iPitch, index, noteDistanceDistr)
            
            if WITH_BEAT_ANNOS:
                self._build_bar_aware_silent_to_attack(tempTransProbSilent, probSumSilent)
    
    def _build_silent_to_attack(self, iPitch, index, noteDistanceDistr):
        '''
        the more complicated transitions from the silent
        this prob only applies to transitions from silent to non silent, which is the transition to a new note
        
        Returns
        -----------------------
        nonzero_transProb_from_silent: list (~ 38)
            non-zero transitions to neighbouring pitches 
        '''
        probSumSilent = 0.0
        nonzero_transProb_from_silent = []
        for jPitch in range(self.par.nS * self.par.nPPS): # compute fromIndex, toIndex and tempTransProbsSilent: the weighted from silent to non-silent
            fromPitch = iPitch
            toPitch = jPitch
            semitoneDistance = fabs(fromPitch - toPitch) * 1.0 / self.par.nPPS
            if semitoneDistance == 0 or (semitoneDistance > self.par.minSemitoneDistance and semitoneDistance < self.par.maxJump): # store only transitions to states, which are within meaningful range
                toIndex = jPitch * self.par.nSPP # note attack index
                tempWeightSilent = noteDistanceDistr.pdf(semitoneDistance) # transitions according to note distance form weights that sum to one
                probSumSilent += tempWeightSilent
                nonzero_transProb_from_silent.append(tempWeightSilent)
                self.fromIndex = np.append(self.fromIndex, np.uint64(index + 2)) # from a silence
                self.toIndex = np.append(self.toIndex, np.uint64(toIndex)) # to an attack
        
        return nonzero_transProb_from_silent, probSumSilent
    
    
    def _build_bar_aware_silent_to_attack(self, transProbs_from_silent, probSumSilent):
        '''
         weight  transProbs_from_silent with bar-position-aware 
         
         Parameters:
         --------------------------
         transProbs_from_silent:
             trasitions probabilities from silent_to_attack for all pitches
        '''
        
        for i in range(len(transProbs_from_silent)):
                givenPitchTransProbSilent = transProbs_from_silent[i]/probSumSilent
                # weight by bar-position
                givenPitch_barPositionDistance_Probs = self.par.barPositionDistance_Probs  * givenPitchTransProbSilent
                
                for iBarPos in range(self.transProbs.shape[0]): #
                    for iDistance in range(self.transProbs.shape[1]-1): 
                        self.transProbs[iBarPos, iDistance] = np.append(self.transProbs[iBarPos, iDistance],
                                          np.float64( givenPitch_barPositionDistance_Probs[iBarPos, iDistance]) ) 
                    
                    # last distance is the default fixed silence-to-note transition from model of Mauch
                    self.transProbs[iBarPos, -1] = np.append(self.transProbs[iBarPos, -1],
                                          np.float64( (1-self.par.pSilentSelftrans) * givenPitchTransProbSilent  ) ) 