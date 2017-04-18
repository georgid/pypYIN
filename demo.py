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



import json
from pypYIN.MonoNoteParameters import NUM_SEMITONES, STEPS_PER_SEMITONE,\
    WITH_MELODIA, WITH_BEAT_ANNOS, WITH_ONSETS_SAME_PITCH, WITH_NOTES_STATES

fs = 44100
frameSize = 2048

# default hopSize of essentia
hopSize = 256
hop_time = float(hopSize)/float(fs)

# hop_time = 0.02 # dont change for ISMIR 2017
# hopSize = int (hop_time * float(fs))


import os, sys
import mir_eval
import numpy as np
import logging
import math
# dir = os.path.dirname(os.path.realpath(__file__))
# srcpath = dir+'/code'
# if srcpath not in sys.path:
#     sys.path.append(srcpath)
from pypYIN.MonoNote import frame_to_ts
import pypYIN.YinUtil

import pypYIN.pYINmain
import essentia.standard as ess
from pypYIN.YinUtil import RMS
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


def doit( argv):
    if len(argv) != 4:
#         sys.exit('usage: {} <recording URI> <beat_annotaions URI> <rec MBID>'.format(argv[0]))
        sys.exit('usage: {} <data dir>  <rec MBID> <output_dir>'.format(argv[0]))
    rec_ID = argv[2]
    rec_URI = argv[1] + '/' + rec_ID + '/'
    filename1 = os.path.join(rec_URI, rec_ID + '.wav')
    beat_file_URI = os.path.join(rec_URI, rec_ID + '.beats' )
    excerpt_URI = os.path.join(rec_URI,  'excerpt.txt')
    pitch_file_URI = os.path.join(rec_URI, rec_ID + '.pitch_audio_analysis' )
    output_dir = argv[3]
    
    start_ts, end_ts = load_excerpt(excerpt_URI)
# initialise
#     filename1 = srcpath + '/../vignesh_short.wav'
#     filename1 = srcpath + '/../vignesh.wav'
    pYinInst = pypYIN.pYINmain.PyinMain()
    pYinInst.initialise(channels=1, inputSampleRate=fs, stepSize=hopSize, blockSize=frameSize, lowAmp=0.25, onsetSensitivity=0.7, pruneThresh=0.1)
    if WITH_MELODIA: # calculate RMS, which is done in pYIN pitch
        calc_rms(pYinInst, filename1)
    #     frame_beat_annos = numpy.ones((estimatedPitch_vocal.shape[0]),dtype=int) # dummy
    if WITH_BEAT_ANNOS: #         frame_beat_annos = load_beat_anno_to_frames(beat_file_URI, estimatedPitch_vocal.shape[0]) # depreceated, mark frames with bar position
        bar_position_ts, bar_labels = load_beat_anno(beat_file_URI, 0) #
        usul_type = get_usul_from_rec(rec_ID)
    else:
        bar_position_ts = []
        bar_labels = []
        usul_type = None
    
    ########### extract  pitch from polyphonic with sercan's melodia
    if os.path.isfile(pitch_file_URI):
        with open(pitch_file_URI, 'r') as f1:
            estimatedPitch_vocal = json.load(f1)
            estimatedPitch_vocal = np.array(estimatedPitch_vocal)
    else:
        estimatedPitch_vocal = extract_predominant_vocal_melody(filename1, hopSize, frameSize, pYinInst, end_ts)
        with open(pitch_file_URI, 'w') as f:
            json.dump(estimatedPitch_vocal.tolist(), f)
    pYinInst.setDecodedMonoPitch(estimatedPitch_vocal) # not sure if this really changes s.th., but does not break things
    

    
    
    ### get remaining features
    featureSet, MIDI_pitch_contour = pYinInst.getRemainingFeatures(estimatedPitch_vocal, WITH_BEAT_ANNOS, bar_position_ts, bar_labels, hop_time, usul_type) # 1. convert to MIDI. 2. note segmentation.
    
    ########## print note step states
    noteStates = []
    for mnOut in featureSet.m_oMonoNoteOut:
        noteStates.append(mnOut.noteState)
#     print noteStates

    featureSet = pYinInst.postprocessPitchTracks(MIDI_pitch_contour, featureSet.m_oMonoNoteOut, WITH_ONSETS_SAME_PITCH) # postprocess to get onsets
    
    extension = determine_file_with_extension(NUM_SEMITONES, STEPS_PER_SEMITONE, WITH_BEAT_ANNOS, WITH_DETECTED_BEATS=0)
    
    MBID = os.path.basename(filename1)[:-4]
    URI_output = os.path.join(output_dir, MBID,  MBID + extension)
    store_results(featureSet.onsetFrames, URI_output, hop_time)

    

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
        
        rms = math.sqrt(pypYIN.YinUtil.sumSquare(frame, 0, pYINinstnce.m_yin.m_yinBufferSize)/pYINinstnce.m_yin.m_yinBufferSize)
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



def determine_file_with_extension( NUM_SEMITONES, STEPS_PER_SEMITONE, WITH_BEAT_ANNOS, WITH_DETECTED_BEATS):
    

    extension = '.onsets'
    if WITH_BEAT_ANNOS and WITH_DETECTED_BEATS:
        sys.exit('cannot be with both annotations and detected beats')
    if WITH_BEAT_ANNOS: # with beat-aware trans probs from annotated beats
        extension += '.bars'
        extension += '_nSemi_'
        extension += str(NUM_SEMITONES)
        extension += '_stepsPSemi_'
        extension += str(STEPS_PER_SEMITONE)
    elif WITH_DETECTED_BEATS:
        
        extension += '.madmom'
        if WITH_NOTES_STATES:
            extension += '_nSemi_'
            extension += str(NUM_SEMITONES)
            extension += '_stepsPSemi_'
            extension += str(STEPS_PER_SEMITONE)
    else:
        extension += '.tony' # default tony
        extension += '_nSemi_'
        extension += str(NUM_SEMITONES)
        extension += '_stepsPSemi_'
        extension += str(STEPS_PER_SEMITONE)
        
        
    if not WITH_MELODIA:
        extension += '.pYINPitch'
    if WITH_ONSETS_SAME_PITCH:
        extension += '.postprocessing'
    return extension

def store_results( onsetFrames, URI_output, hop_time ):
###################### serialize note onset timestamps
    
    
    import csv
    f = open(URI_output, 'w')
    csv_writer = csv.writer(f)
    for onset_frame_number in onsetFrames:
        ts = frame_to_ts(onset_frame_number, hop_time) # first frame centered at 0, because using default of FrameCutter in essentia
        csv_writer.writerow([ts])
    
    print 'mono note decoded onsets written to file \n' + URI_output + '\n'
    f.close()

if __name__ == "__main__":
    
    doit( sys.argv)
