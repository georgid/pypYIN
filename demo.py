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
 * ‚Äö√Ñ√∂‚àö√ë‚àö‚à´pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions‚Äö√Ñ√∂‚àö√ë‚àöœÄ,
 * in Proceedings of the IEEE International Conference on Acoustics,
 * Speech, and Signal Processing (ICASSP 2014), 2014.
 *
 * M. Mauch, C. Cannam, R. Bittner, G. Fazekas, J. Salamon, J. Dai, J. Bello and S. Dixon,
 * ‚Äö√Ñ√∂‚àö√ë‚àö‚à´Computer-aided Melody Note Transcription Using the Tony Software: Accuracy and Efficiency‚Äö√Ñ√∂‚àö√ë‚àöœÄ,
 * in Proceedings of the First International Conference on Technologies for
 * Music Notation and Representation, 2015.





'''
WITH_BAR_POSITIONS = 1
WITH_MELODIA = 1
WITH_ONSETS_SAME_PITCH = 1

fs = 44100
frameSize = 2048
hopSize = 256
hop_time = float(hopSize)/float(fs)

import os, sys
import mir_eval
import numpy as np
import logging
import math
dir = os.path.dirname(os.path.realpath(__file__))
srcpath = dir+'/code'
if srcpath not in sys.path:
    sys.path.append(srcpath)
from MonoNote import frame_to_ts
import YinUtil

import pYINmain
import essentia.standard as ess
import numpy as np
from YinUtil import RMS
VOCAL_ACTIVITY_EXT = '.vocal_anno'


parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir))
path_intersect_scripts = os.path.join(parentDir, 'otmm_vocal_segments_dataset/scripts')
if path_intersect_scripts not in sys.path:
        sys.path.append(path_intersect_scripts)
from load_data import load_excerpt, load_beat_anno
path_Alignment_duration =     os.path.join(parentDir, 'AlignmentDuration')
if path_Alignment_duration not in sys.path:
        sys.path.append(path_Alignment_duration)
from src.align.FeatureExtractor import extractPredominantPitch
from makammusicbrainz.audiometadata import AudioMetadata


def doit( fs, frameSize, hopSize, hop_time, argv):
    if len(argv) != 3:
#         sys.exit('usage: {} <recording URI> <beat_annotaions URI> <rec MBID>'.format(argv[0]))
        sys.exit('usage: {} <recording dir>  <rec MBID>'.format(argv[0]))
    rec_ID = argv[2]
    filename1 = os.path.join(argv[1], rec_ID + '.wav')
    beat_file_URI = os.path.join(argv[1], rec_ID + '.beats' )
    start_ts, end_ts = load_excerpt(argv[1])
# initialise
#     filename1 = srcpath + '/../vignesh_short.wav'
#     filename1 = srcpath + '/../vignesh.wav'
    pYinInst = pYINmain.PyinMain()
    pYinInst.initialise(channels=1, inputSampleRate=fs, stepSize=hopSize, blockSize=frameSize, lowAmp=0.25, onsetSensitivity=0.7, pruneThresh=0.1)
    if WITH_MELODIA: # calculate RMS, which is done in pYIN pitch
        calc_rms(pYinInst, filename1)
    #     frame_beat_annos = numpy.ones((estimatedPitch_vocal.shape[0]),dtype=int) # dummy
    if WITH_BAR_POSITIONS: #         frame_beat_annos = load_beat_anno_to_frames(beat_file_URI, estimatedPitch_vocal.shape[0]) # depreceated, mark frames with bar position
        bar_position_ts, bar_labels = load_beat_anno(beat_file_URI, start_ts) #
        usul_type = get_usul_from_rec(rec_ID)
    else:
        bar_position_ts = []
        bar_labels = []
        usul_type = None
    
    ########### extract  pitch from polyphonic with sercan's melodia
    estimatedPitch_vocal = extract_predominant_vocal_melody(filename1, hopSize, frameSize, pYinInst, end_ts)
    pYinInst.setDecodedMonoPitch(estimatedPitch_vocal) # not sure if this really changes s.th., but does not break things

    ### get remaining features
    featureSet, MIDI_pitch_contour = pYinInst.getRemainingFeatures(estimatedPitch_vocal, WITH_BAR_POSITIONS, bar_position_ts, bar_labels, hop_time, usul_type) # 1. convert to MIDI. 2. note segmentation.
    noteStates = []
    for mnOut in featureSet.m_oMonoNoteOut:
        noteStates.append(mnOut.noteState)
    
    print noteStates
    featureSet = pYinInst.postprocessPitchTracks(MIDI_pitch_contour, featureSet.m_oMonoNoteOut, WITH_ONSETS_SAME_PITCH) # postprocess to get onsets
    store_results(WITH_BAR_POSITIONS, WITH_MELODIA, WITH_ONSETS_SAME_PITCH, hop_time, filename1, featureSet)


    

def extract_predominant_vocal_melody(filename1, hopSize, frameSize, pYinInst, end_ts):
    '''
    extract predominant vocal pitch contour
    as workaround, intersect extracted pitch with vocal annotation
    
    Returns
    -------------------
    list of estimated pitch values in Hz, at non-vocal returns value <= 0 
    '''
    if WITH_MELODIA:#### predominant melody makam
        estimatedPitch_andTs = extractPredominantPitch( filename1[:-4], frameSize, hopSize, jointAnalysis=False, musicbrainzid=None, preload=True) #jointAnalysis=False, becasue no   
    
    
    else: ######### pYIN 
        audio = ess.MonoLoader(filename = filename1, sampleRate = fs)()
        for frame in ess.FrameGenerator(audio, frameSize=frameSize, hopSize=hopSize):
            featureSet = pYinInst.process(frame)
            
        ##### calculate smoothed pitch and mono note
        estimatedPitch = pYinInst.decodePitchTrack() # this is just pitch 
        ts = [] ### generate timestamps
        for onset_frame_number,frame in enumerate(estimatedPitch):
            ts.append( frame_to_ts(onset_frame_number, float(hopSize/fs)) ) 
        estimatedPitch_andTs = np.vstack( (np.array(ts),estimatedPitch )).T
    
    idx_end_ts = np.searchsorted(estimatedPitch_andTs[:,0], end_ts) #  until end_ts
    estimatedPitch_andTs = estimatedPitch_andTs[:min(idx_end_ts+1,estimatedPitch_andTs.shape[0]),:]
    ####### read vocal annotation from file and intersect
   
    from intersect_vocal_and_pitch import intersect_section_links 
    from main import load_voiced_segments
    voiced_segments = load_voiced_segments(filename1[:-4] + VOCAL_ACTIVITY_EXT)    
    estimatedPitch_andTs_vocal =  intersect_section_links(estimatedPitch_andTs, voiced_segments) # onsets with pitch
    
    #  
    estimatedPitch_vocal = estimatedPitch_andTs_vocal[:,1]
    return estimatedPitch_vocal

def calc_rms(pYINinstnce, filename1):
    '''
    copied from pYINMain.pYIN. done here as  a separate func to call when using melodia
    '''        
    audio = ess.MonoLoader(filename = filename1, sampleRate = fs)()
    
    for frame in ess.FrameGenerator(audio, frameSize=pYINinstnce.m_blockSize, hopSize=pYINinstnce.m_stepSize):
# this might be needed to ensure a frame has enough entries for pYINinstnce.m_yin.m_yinBufferSize
#              dInputBuffers = np.zeros((self.m_blockSize,), dtype=np.float64) # make sure it is zero-padded at end
#         for i in range(self.m_blockSize):
#             dInputBuffers[i] = inputBuffers[i]
        
        rms = math.sqrt(YinUtil.sumSquare(frame, 0, pYINinstnce.m_yin.m_yinBufferSize)/pYINinstnce.m_yin.m_yinBufferSize)
        pYINinstnce.m_level = np.append(pYINinstnce.m_level, rms)




def get_usul_from_rec(rec_ID):
    '''
    automatically extract the usul given the recording MB ID
    '''
    from makammusicbrainz.audiometadata import AudioMetadata
    audioMetadata = AudioMetadata(get_work_attributes=True, print_warnings=True)
    

    audio_meta = audioMetadata.from_musicbrainz(rec_ID)
    usul_type = audio_meta['usul'][0]['attribute_key'] 
    return usul_type

def store_results(WITH_BAR_POSITIONS, WITH_MELODIA, WITH_ONSETS_SAME_PITCH, hop_time, filename1, featureSet):
###################### serialize note onset timestamps
    if WITH_BAR_POSITIONS: # with bar-position trans probs
        extension = '.onsets.bars'
    else:
        extension = '.onsets.tony' # default tony
    if not WITH_MELODIA:
        extension += '.pYINPitch'
    if not WITH_ONSETS_SAME_PITCH:
        extension += '.no_postprocessing'
    filename1_detected_onsets = filename1[:-4] + extension
    import csv
    f = open(filename1_detected_onsets, 'w')
    csv_writer = csv.writer(f)
    for onset_frame_number in featureSet.onsetFrames:
        ts = frame_to_ts(onset_frame_number, hop_time) # first frame centered at 0, becasue using default of FrameCutter in essentia
        csv_writer.writerow([ts])
    
    print 'mono note decoded onsets written to file \n' + filename1_detected_onsets + '\n'
    f.close()


if __name__ == "__main__":
    
    doit(fs, frameSize, hopSize, hop_time, sys.argv)


# def load_beat_anno_to_frames(beats_URI, len_frames):
#     '''
#     load beat annotations and distribute labels to each frame 
#     @deprecated: 
#     Returns
#     -------------------
#     sample_labels: list
#         beat labels at each frame 
#     '''
#     num_beats_usul = 9 # aksak 
#     num_beats_usul = 10 # curcuna 
#     
#     beat_ts, beat_labels = load_beat_anno(beat_file_URI)
# 
#     beat_labels = np.array(beat_labels)
#     beat_labels -= 1 #  start from 0, not from 1
#     
#     # # generate secondary-beat ts 
#     # beat_ts_middle = []
#     # for iB in range(len(boundaries)-1):
#     #       beat_ts_middle.append( np.mean([boundaries[iB], boundaries[iB+1]]) )
#     
#     # beat_ts.extend(beat_ts_middle)        
#     # beat_labels_middle = beat_labels[:len(beat_ts_middle)+1]
#     # beat_labels*=2
#     # beat_labels.extend(beat_labels_middle)
#     # # TODO: sort intervals
#     
#     beat_time_intervals = mir_eval.util.boundaries_to_intervals(beat_ts)
#     pre_beat_label = (beat_labels[0] - 1) % num_beats_usul # label of frames preceding first annotaated label
#     sample_times, sample_labels = mir_eval.util.intervals_to_samples(beat_time_intervals, beat_labels, sample_size=256./44100., fill_value=pre_beat_label )
#     if len_frames >len(sample_labels): # etend with last annotated beat
#         sample_labels.extend([beat_labels[-1]] * (len_frames - len(sample_labels) ) )
#     return sample_labels