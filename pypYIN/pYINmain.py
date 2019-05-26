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
import copy
from math import *
from pypYIN.Yin import Yin
from pypYIN.YinUtil import RMS
from pypYIN.MonoPitch import MonoPitch
from pypYIN.MonoNote import MonoNote
from pypYIN.MonoNoteParameters import NUM_SEMITONES, STEPS_PER_SEMITONE,\
    PITCH_PROB



class Feature(object):
    def __init__(self):
        self.values = np.array([], dtype=np.float64)

    def resetValues(self):
        self.values = np.array([], dtype=np.float64)

class FeatureSet(object):
    def __init__(self):
        self.m_oF0Candidates = []
        self.m_oF0Probs = []
        self.m_oVoicedProb = []
        self.m_oCandidateSalience = []
        self.m_oSmoothedPitchTrack = []
        self.m_oMonoNoteOut = []
        self.m_oNotes = []
        self.m_oNotePitchTracks = []

class PyinMain(object):

    def __init__(self):
        self.m_channels = 0
        self.m_stepSize = 256
        self.m_blockSize = 2048
        self.m_inputSampleRate = 44100
        self.m_fmin = 40
        self.m_fmax = 1600

        self.m_yin = Yin()

        self.m_threshDistr = 2.0
        self.m_outputUnvoiced = 2
        self.m_preciseTime = 0.0
        self.m_lowAmp = 0.1
        self.m_onsetSensitivity = 0.7
        self.m_pruneThresh = 0.1

        self.m_pitchProb = []
        self.m_level = np.array([], dtype=np.float32)

        self.fs = FeatureSet()

    def initialise(self, channels = 1, inputSampleRate = 44100, stepSize = 256, blockSize = 2048,
                   lowAmp = 0.1, onsetSensitivity = 0.7, pruneThresh = 0.1 ):

        if channels != 1:
            return False

        self.m_channels = channels
        self.m_inputSampleRate = inputSampleRate
        self.m_stepSize = stepSize
        self.m_blockSize = blockSize

        self.m_lowAmp = lowAmp
        self.m_onsetSensitivity = onsetSensitivity
        self.m_pruneThresh = pruneThresh

        self.reset()

        return True

    def reset(self):

        self.m_yin.setThresholdDistr(self.m_threshDistr)
        self.m_yin.setFrameSize(self.m_blockSize)
        self.m_yin.setFast(not self.m_preciseTime)

        self.m_pitchProb = np.array([], dtype=np.float64)
        self.m_level = np.array([], dtype=np.float32)

    def process(self, inputBuffers):
        '''
        inputBuffers is samples for one frames
        '''
        dInputBuffers = np.zeros((self.m_blockSize,), dtype=np.float64) # make sure it is zero-padded at end
        for i in range(self.m_blockSize):
            dInputBuffers[i] = inputBuffers[i]

        rms = RMS(inputBuffers, self.m_blockSize)

        isLowAmplitude = rms < self.m_lowAmp

        yo = self.m_yin.processProbabilisticYin(dInputBuffers)

        self.m_level = np.append(self.m_level, yo.rms)

        '''
        First, get the things out of the way that we don't want to output
        immediately, but instead save for later
        '''
        tempPitchProb = np.array([], dtype=np.float32)
        firstStack = False
        for iCandidate in range(yo.freqProb.shape[0]):
            tempPitch = 12.0 * log(yo.freqProb[iCandidate][0]/440.0)/log(2.0) + 69.0
            if not isLowAmplitude:
                if firstStack == False:
                    tempPitchProb = np.array([np.array([tempPitch, yo.freqProb[iCandidate][1]], dtype=np.float64),])
                    firstStack = True
                else:
                    tempPitchProb = np.vstack((tempPitchProb, np.array([tempPitch, yo.freqProb[iCandidate][1]], dtype=np.float64)))
            else:
                factor = ((rms+0.01*self.m_lowAmp)/(1.01*self.m_lowAmp))
                if firstStack == False:
                    tempPitchProb = np.array([np.array([tempPitch, yo.freqProb[iCandidate][1]*factor], dtype=np.float64),])
                    firstStack = True
                else:
                    tempPitchProb = np.vstack((tempPitchProb, np.array([tempPitch, yo.freqProb[iCandidate][1]*factor], dtype=np.float64)))
       
        if len(self.m_pitchProb) < 1 and len(tempPitchProb) > 0:
            self.m_pitchProb = [tempPitchProb,]
        elif len(self.m_pitchProb) >= 1:
            self.m_pitchProb = self.m_pitchProb + [tempPitchProb]

        # f0 CANDIDATES
        f = Feature()
        for i in range(yo.freqProb.shape[0]):
            f.values = np.append(f.values, yo.freqProb[i][0])
        self.fs.m_oF0Candidates.append(copy.copy(f))

        f.resetValues()
        voicedProb = 0.0
        for i in range(yo.freqProb.shape[0]):
            f.values = np.append(f.values, yo.freqProb[i][1])
            voicedProb += yo.freqProb[i][1]
        self.fs.m_oF0Probs.append(copy.copy(f))

        f.values = np.append(f.values, voicedProb)
        self.fs.m_oVoicedProb.append(copy.copy(f))

        # SALIENCE -- maybe this should eventually disappear
        f.resetValues()
        salienceSum = 0.0
        for iBin in range(yo.salience.shape[0]):
            f.values = np.append(f.values, yo.salience[iBin])
            salienceSum += yo.salience[iBin]
        self.fs.m_oCandidateSalience.append(copy.copy(f))

        return self.fs

    def decodePitchTrack(self):
        '''
        1. decode pitch with Viterbi
        
        '''
        

        if len(self.m_pitchProb) == 0:
            return self.fs

        # MONO-PITCH STUFF
        mp = MonoPitch()
        mpOut = mp.process(self.m_pitchProb)
        
        return mpOut
   
    def setDecodedMonoPitch(self, mpOut):
        '''
        store monoPitch mpOut in the field self.fs.m_oSmoothedPitchTrack 
        '''
        f = Feature()
        for iFrame in range(len(mpOut)):
            if mpOut[iFrame] < 0 and self.m_outputUnvoiced == 0: # skip unvoiced frames, if not desired to output them
                continue
            f.resetValues()
            if self.m_outputUnvoiced == 1:
                f.values = np.append(f.values, np.fabs(mpOut[iFrame])) #  absolute value of unvoiced if desired to output them 
            else:
                f.values = np.append(f.values, mpOut[iFrame])
    
            self.fs.m_oSmoothedPitchTrack.append(copy.copy(f))
    

    def segment_notes(self, pitch_contour, with_bar_positions, bar_position_ts, bar_labels, hop_time, usul_type):
        '''
        decode note states using MonoNote probabilistic model
        
        
        Parameters
        ----------------------
        pitch_contour :
            only pitch values
            
        with_bar_positions: bool
            metrical-accent aware detection set
        
        Returns
        -----------------------
        feature set:
            updated with  m_oMonoNoteOut: array of FrameOutput
        MIDI_pitch_contour:
              midi pitch
        '''
        
        MIDI_pitch_contour_and_prob = np.zeros((len(pitch_contour),2)) 
        MIDI_pitch_contour_and_prob[:,0] = pitch_contour
        
        if len(pitch_contour) == 0:
            return self.fs


        ############ convert to MIDI scale
        mn = MonoNote(STEPS_PER_SEMITONE, NUM_SEMITONES, with_bar_positions, hop_time, usul_type) # if frame_beat_annos is set, use bar-position dependent annotation   
        
#         import matplotlib.pyplot as plt
#         plt.plot(mn.hmm.transProbs[0,1][30*75 + 5: 31*75 +5])
#         plt.show()

        for iFrame in range(len(pitch_contour)):
            if pitch_contour[iFrame] > 0:  # zero or negative value (silence) remains with 0 probability and negative frequency in Herz
                MIDI_pitch_contour_and_prob[iFrame][0] = 12 * log(pitch_contour[iFrame]/440.0)/log(2.0) + 69
                MIDI_pitch_contour_and_prob[iFrame][1] = PITCH_PROB # constant voicing probability = 0.9
        
        mnOut = mn.process(MIDI_pitch_contour_and_prob, bar_position_ts, bar_labels, hop_time) # decode note states Viterbi

        self.fs.m_oMonoNoteOut = mnOut # array of FrameOutput 
        return self.fs, MIDI_pitch_contour_and_prob[:,0] 

    def postprocessPitchTracks(self, MIDI_pitch_contour, mnOut, with_same_pitch_onsets):        
        '''
        
        postprocessing of MIDI_pitch noteStatesToPitch
        1. filter detected onsets and store them as fields in  self.fs.onsetFrames
        2.  filter also MIDI_pitch tracks per note (notePitchTracks) and median pitches
        
        Parameters
        --------------------------
        MIDI_pitch_contour:
            pitch contour in MIDI 
        mnOut: array of FrameOutput 
            decoded note states
            
    
        
        '''
        f = Feature()
        f.resetValues()
        
        self.fs.onsetFrames = [] #  onsetFrames where there is change from state 3 to 1 
        isVoiced = 0
        oldIsVoiced = 0
        nFrame = len(MIDI_pitch_contour)
        
        minNoteFrames = (self.m_inputSampleRate*self.m_pruneThresh)/self.m_stepSize # minimum number of frames  per note
        
        notePitchTrack = np.array([], dtype=np.float32) # collects pitches for one note at a time
        

                
        for iFrame in range(nFrame):
                        
            isVoiced = mnOut[iFrame].noteState < 3 and MIDI_pitch_contour[iFrame] > 0
            
            is_samepitch_onset = False
            if with_same_pitch_onsets: 
                is_samepitch_onset = (iFrame >= nFrame-3 ) \
                    or (self.m_level[iFrame]/self.m_level[iFrame+2]>self.m_onsetSensitivity) # onset at same pitch if pitch amplitude changes above a threshold 
#                 isVoiced = isVoiced and is_samepitch_onset
                is_samepitch_onset = isVoiced and is_samepitch_onset # REPLACED
            
            
#             if isVoiced and iFrame != nFrame-1: # sanity check
#                 if oldIsVoiced == 0: # set onset at non-voiced-to-voiced transition
#                     self.fs.onsetFrames.append( iFrame )
            
            if isVoiced and iFrame != nFrame-1: # sanity check                      # REPLACED
                if oldIsVoiced == 0 or is_samepitch_onset: # set onset at non-voiced-to-voiced transition
                    self.fs.onsetFrames.append( iFrame )
                    
            
                MIDI_pitch = MIDI_pitch_contour[iFrame]
                notePitchTrack = np.append(notePitchTrack, MIDI_pitch) # add to the note's MIDI_pitch
                
            else: # not currently voiced
                if oldIsVoiced == 1: # end of the note
                    if len(notePitchTrack) >= minNoteFrames:

                        notePitchTrack = np.sort(notePitchTrack) # what is this?
                        self.fs.m_oNotePitchTracks.append(copy.copy(notePitchTrack)) # store current note pitch track 
                        
                        medianPitch = notePitchTrack[int(len(notePitchTrack)/2)]
                        medianFreq = pow(2, (medianPitch-69)/12)*440
                        f.resetValues()
                        f.values = np.append(f.values, np.double(medianFreq))
                        self.fs.m_oNotes.append(copy.copy(f)) # store median frequency per note. NOT EFFICIENT

                    
                    notePitchTrack = np.array([], dtype=np.float32) # new note starts
            oldIsVoiced = isVoiced

        return self.fs
    
