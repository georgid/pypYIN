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
WITH_BAR_POSITIONS = 0
WITH_MELODIA = True
fs = 44100
frameSize = 2048
hopSize = 256
hop_time = float(hopSize)/float(fs)

import os, sys
import mir_eval
import numpy
import logging
dir = os.path.dirname(os.path.realpath(__file__))
srcpath = dir+'/code'
if srcpath not in sys.path:
    sys.path.append(srcpath)
from MonoNote import frame_to_ts

import pYINmain
import essentia.standard as ess
import numpy as np
from YinUtil import RMS
VOCAL_ACTIVITY_EXT = '.vocal_anno'


parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir))
path_intersect_scripts = os.path.join(parentDir, 'turkish_makam_vocal_segments_dataset/scripts')
if path_intersect_scripts not in sys.path:
        sys.path.append(path_intersect_scripts)
path_Alignment_duration =     os.path.join(parentDir, 'AlignmentDuration')
if path_Alignment_duration not in sys.path:
        sys.path.append(path_Alignment_duration)
from src.align.FeatureExtractor import extractPredominantPitch

def extract_predominant_vocal_melody(filename1, hopSize, frameSize, pYinInst):
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
    
    
    ####### read vocal annotation from file
   
    from intersect_vocal_and_pitch import intersect_section_links 
    from main import load_voiced_segments
    voiced_segments = load_voiced_segments(filename1[:-4] + VOCAL_ACTIVITY_EXT)    
    estimatedPitch_andTs_vocal =  intersect_section_links(estimatedPitch_andTs, voiced_segments) # onsets with pitch
      
    estimatedPitch_vocal = estimatedPitch_andTs_vocal[:,1]
    return estimatedPitch_vocal



def load_beat_anno(beats_URI):
    '''
    load beat annotations 
    
    Returns
    -------------------
    sample_labels: list
        beat labels at each frame 
    '''
    
    try:
        beat_ts, beat_labels = mir_eval.io.load_delimited(beats_URI,[float,int],delimiter=',')
    except:
        beat_ts, beat_labels = mir_eval.io.load_delimited(beats_URI,[float,int],delimiter='\t')
        return beat_ts, beat_labels

def load_beat_anno_to_frames(beats_URI, len_frames):
    '''
    load beat annotations and distribute labels to each frame 
    @deprecated: 
    Returns
    -------------------
    sample_labels: list
        beat labels at each frame 
    '''
    num_beats_usul = 9 # aksak 
    num_beats_usul = 10 # curcuna 
    
    beat_ts, beat_labels = load_beat_anno(beat_file_URI)

    beat_labels = np.array(beat_labels)
    beat_labels -= 1 #  start from 0, not from 1
    
    # # generate secondary-beat ts 
    # beat_ts_middle = []
    # for iB in range(len(boundaries)-1):
    #       beat_ts_middle.append( np.mean([boundaries[iB], boundaries[iB+1]]) )
    
    # beat_ts.extend(beat_ts_middle)        
    # beat_labels_middle = beat_labels[:len(beat_ts_middle)+1]
    # beat_labels*=2
    # beat_labels.extend(beat_labels_middle)
    # # TODO: sort intervals
    
    beat_time_intervals = mir_eval.util.boundaries_to_intervals(beat_ts)
    pre_beat_label = (beat_labels[0] - 1) % num_beats_usul # label of frames preceding first annotaated label
    sample_times, sample_labels = mir_eval.util.intervals_to_samples(beat_time_intervals, beat_labels, sample_size=256./44100., fill_value=pre_beat_label )
    if len_frames >len(sample_labels): # etend with last annotated beat
        sample_labels.extend([beat_labels[-1]] * (len_frames - len(sample_labels) ) )
    return sample_labels



if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        sys.exit('usage: {} <recording path> <beat_annotaions URI>'.format( sys.argv[0]) )
    filename1 = sys.argv[1]
    beat_file_URI = sys.argv[2]
    
    # initialise
#     filename1 = srcpath + '/../vignesh_short.wav'
#     filename1 = srcpath + '/../vignesh.wav'
    
   


    pYinInst = pYINmain.PyinMain()
    pYinInst.initialise(channels = 1, inputSampleRate = fs, stepSize = hopSize, blockSize = frameSize,
                   lowAmp = 0.25, onsetSensitivity = 0.7, pruneThresh = 0.1)



    
    ########### extract  pitch from polyphonic with sercan's melodia
    estimatedPitch_vocal = extract_predominant_vocal_melody(filename1, hopSize, frameSize, pYinInst )
    pYinInst.setDecodedMonoPitch(estimatedPitch_vocal) # not sure if this really changes s.th., but does not break things
    
#     frame_beat_annos = numpy.ones((estimatedPitch_vocal.shape[0]),dtype=int) # dummy
    if WITH_BAR_POSITIONS:
#         frame_beat_annos = load_beat_anno_to_frames(beat_file_URI, estimatedPitch_vocal.shape[0]) # depreceated, mark frames with bar position
        bar_position_ts, bar_labels = load_beat_anno(beat_file_URI) #
    else:
        bar_position_ts = []
        bar_labels = []
    
    featureSet, MIDI_pitch_contour = pYinInst.getRemainingFeatures( estimatedPitch_vocal, WITH_BAR_POSITIONS, bar_position_ts, bar_labels, hop_time) # 1. convert to MIDI. 2. note segmentation.
    noteStates = []
    for mnOut in featureSet.m_oMonoNoteOut:
        noteStates.append(mnOut.noteState)
    print noteStates



    
    featureSet = pYinInst.postprocessPitchTracks(MIDI_pitch_contour, featureSet.m_oMonoNoteOut)  # postprocess to get onsets


    
    ###################### serialize note onset timestamps
    if WITH_BAR_POSITIONS:   # with bar-position trans probs
        extension = '.onsets.bars'
    else:  # default tony  
        extension =  '.onsets.tony'
    if not WITH_MELODIA:
            extension += '.pYINPitch'
    extension += '.no_postprocessing'
    
    filename1_detected_onsets = filename1[:-4] + extension
    
     
    import csv
    f = open (filename1_detected_onsets, 'w')
    csv_writer = csv.writer(f)
    for onset_frame_number in featureSet.onsetFrames:
        ts = frame_to_ts(onset_frame_number, hop_time) # first frame centered at 0, becasue using default of FrameCutter in essentia
        csv_writer.writerow([ts])
    print    'mono note decoded onsets written to file '  + filename1_detected_onsets + '\n'
    f.close()
