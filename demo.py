    # -*- coding: utf-8 -*-

'''
 * Copyright (C) 2017  Music Technology Group - Universitat Pompeu Fabra
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



import json
from pypYIN.MonoNoteParameters import NUM_SEMITONES, STEPS_PER_SEMITONE,\
    WITH_MELODIA, WITH_ONSETS_SAME_PITCH, WITH_NOTES_STATES,\
    WITH_MAKAM
from pypYIN.YinUtil import extractPredominantMelody, load_excerpt
from pypYIN import MonoNoteParameters

fs = 44100
frameSize = 2048

# default hopSize of essentia
hopSize = 256
hop_time = float(hopSize)/float(fs)

# hop_time = 0.02 ## used to reproduce results in paper ISMIR 2017 
# hopSize = int (hop_time * float(fs))


import os, sys
import numpy as np
import math
# dir = os.path.dirname(os.path.realpath(__file__))
# srcpath = dir+'/code'
# if srcpath not in sys.path:
#     sys.path.append(srcpath)
from pypYIN.MonoNote import frame_to_ts
import pypYIN.YinUtil

import pypYIN.pYINmain
import essentia.standard as ess
VOCAL_ACTIVITY_EXT = '.vocal_anno'





def parse_arguments(argv):
    if len(argv) != 4: #         sys.exit('usage: {} <recording URI> <beat_annotaions URI> <rec MBID>'.format(argv[0]))
        sys.exit('usage: {} <data dir>  <rec MBID> <beat-aware>'.format(argv[0]))
    rec_ID = argv[2]
    dataset_dir = argv[1]
    rec_URI = dataset_dir + '/data/' + rec_ID + '/'
    filename1 = os.path.join(rec_URI, rec_ID + '.wav')
    beat_file_URI = os.path.join(rec_URI, rec_ID + '.beats_tab')
    excerpt_URI = os.path.join(rec_URI, 'excerpt.txt')
    pitch_file_URI = os.path.join(rec_URI, rec_ID + '.pitch_audio_analysis')
    pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS = int(argv[3]) # if metrical-accent aware detection desired, beats are read from annotations. no automatic beat detection implemented
    output_dir = create_output_dirs(dataset_dir, pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS)
    start_ts, end_ts = load_excerpt(excerpt_URI)
    return filename1, beat_file_URI, rec_ID, pitch_file_URI, end_ts, output_dir

def doit( argv):
#     filename1, beat_file_URI, rec_ID, pitch_file_URI, end_ts, output_dir = parse_arguments(argv)
    
    if len(argv) != 3 and len(argv) != 2 : #         sys.exit('usage: {} <recording URI> <beat_annotaions URI> <rec MBID>'.format(argv[0]))
        sys.exit('usage: {} <path_to_audio> <optional: extracted pitch file>'.format(argv[0]))
    
    audio_filename = argv[1]
    pitch_file_URI = None
    if len(argv) == 3:
        pitch_file_URI = argv[2]
    end_ts = None
    
    pYinInst = pypYIN.pYINmain.PyinMain()
    pYinInst.initialise(channels=1, inputSampleRate=fs, stepSize=hopSize, blockSize=frameSize, lowAmp=0.25, onsetSensitivity=0.7, pruneThresh=0.1)
    
    if WITH_MELODIA: # calculate RMS as a preprocessing step, ( done internally for pYIN pitch extraction) 
        calc_rms(pYinInst, audio_filename)

    if pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS:
        from pypYIN.YinUtil import load_beat_anno
        bar_position_ts, bar_labels = load_beat_anno(beat_file_URI, 0) #
        if WITH_MAKAM:
            get_meter_from_rec(rec_ID)
        else:  # for western pop assume 4/4 meter
            usul_type = '44' 
    else:
        bar_position_ts = []
        bar_labels = []
        usul_type = None
    
    ########### extract  pitch from polyphonic
    if pitch_file_URI is not None and os.path.isfile(pitch_file_URI):
        with open(pitch_file_URI, 'r') as f1:
            estimatedPitch_vocal = json.load(f1)
            estimatedPitch_vocal = np.array(estimatedPitch_vocal)
    else:
        estimatedPitch_vocal = extract_predominant_vocal_melody(audio_filename, hopSize, frameSize, pYinInst, end_ts)
#         with open(pitch_file_URI, 'w') as f:
#             json.dump(estimatedPitch_vocal.tolist(), f)
    pYinInst.setDecodedMonoPitch(estimatedPitch_vocal) # not sure if this really changes s.th., but does not break things
    
    ### note transcription
    featureSet, MIDI_pitch_contour = pYinInst.segment_notes(estimatedPitch_vocal, pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS, bar_position_ts, bar_labels, hop_time, usul_type) # 1. convert to MIDI. 2. note segmentation.
    
    ########## print note step states
    noteStates = []
    for mnOut in featureSet.m_oMonoNoteOut:
        noteStates.append(mnOut.noteState)
#     print noteStates

    featureSet = pYinInst.postprocessPitchTracks(MIDI_pitch_contour, featureSet.m_oMonoNoteOut, WITH_ONSETS_SAME_PITCH) # postprocess to get onsets
    
    extension = determine_file_with_extension(NUM_SEMITONES, STEPS_PER_SEMITONE, pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS, WITH_DETECTED_BEATS=0)
    
    print featureSet.onsetFrames # these are states of a note (1,2,3). 1 following 3 means an onset  
    print featureSet.m_oNotes # note pitches 
    
    ## TODO: fix output dir
#     output_dir = '.'
#     MBID = os.path.basename(audio_filename)[:-4]
#     URI_output = os.path.join(output_dir, MBID,  MBID + extension)
#     store_results(featureSet.onsetFrames, URI_output, hop_time)

    




def extract_predominant_vocal_melody(audio_filename, hopSize, frameSize, pYinInst, end_ts=None):
    '''
    extract predominant vocal pitch contour
    as workaround, intersect extracted pitch with vocal annotation
    
    Parameters
    -----------------------
    end_ts: extract until this ts, disregard the rest of the audio  
    
    Returns
    -------------------
    list of estimated pitch values in Hz, at non-vocal returns value <= 0 
    '''
    if WITH_MELODIA:
        
        if WITH_MAKAM: #### use predominant melody tailored to makam
            path_Alignment_duration =     os.path.join(parentDir, 'AlignmentDuration')
            if path_Alignment_duration not in sys.path:
                sys.path.append(path_Alignment_duration)
            from src.align.FeatureExtractor import extractPredominantMelodyMakam
            estimatedPitch_andTs = extractPredominantMelodyMakam( audio_filename[:-4], frameSize, hopSize, jointAnalysis=False, musicbrainzid=None, preload=True) #jointAnalysis=False, becasue no   
        else: # use melodia
            estimatedPitch_andTs = extractPredominantMelody(audio_filename, frameSize, hopSize)
            
    else: ######### pYIN 
        audio = ess.MonoLoader(filename = audio_filename, sampleRate = fs)()
        for frame in ess.FrameGenerator(audio, frameSize=frameSize, hopSize=hopSize):
            featureSet = pYinInst.process(frame)
            
        estimatedPitch = pYinInst.decodePitchTrack() # pitch extraction 
        ts = [] ### generated timestamps
        for onset_frame_number,frame in enumerate(estimatedPitch):
            ts.append( frame_to_ts(onset_frame_number, float(hopSize/fs)) ) 
        estimatedPitch_andTs = np.vstack( (np.array(ts), estimatedPitch )).T
    
    if end_ts is not None:
        idx_end_ts = np.searchsorted(estimatedPitch_andTs[:,0], end_ts) #  until end_ts
        estimatedPitch_andTs = estimatedPitch_andTs[:min(idx_end_ts+1,estimatedPitch_andTs.shape[0]),:]
    
    if MonoNoteParameters.WITH_VOCAL_SEGMENTS: # vocal segments given
        estimatedPitch_andTs = intersect_vocal_segments(audio_filename, estimatedPitch_andTs)
    
    return estimatedPitch_andTs[:,1]


def intersect_vocal_segments(filename1, estimatedPitch_andTs):
    '''
    read vocal activity from a file and intersect with extracted pitch contour
    '''
    from intersect_vocal_and_pitch import intersect_section_links  
    from main import load_voiced_segments
    voiced_segments = load_voiced_segments(filename1[:-4] + VOCAL_ACTIVITY_EXT)
    estimatedPitch_andTs_vocal = intersect_section_links(estimatedPitch_andTs, voiced_segments) # onsets with pitch
    return estimatedPitch_andTs_vocal

def calc_rms(pYINinstnce, filename1):
    '''
    calculare root mean square
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


def get_meter_from_rec(recording_ID):
    '''
    automatically extract the meter from the metadata of the recording by ID (MusicBrainzID)
    '''
    
    # otherwise for makam
    from makammusicbrainz.audiometadata import AudioMetadata
    audioMetadata = AudioMetadata(get_work_attributes=True, print_warnings=True)

    audio_meta = audioMetadata.from_musicbrainz(recording_ID)
    try:
        usul_type = audio_meta['usul'][0]['attribute_key'] 
        
    except:
        if recording_ID == '7aec9833-6482-4917-87bd-e60c7c1dae3c':
            usul_type = 'kapali_curcuna'
        else:
            sys.exit('no usul type can be automatically fetched')
            
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
    
def create_output_dirs(data_main_dir, with_beat_annotations=True):
    
    if with_beat_annotations:
        sub_dir = 'experiments/beat_anno/'
    elif WITH_NOTES_STATES: 
        sub_dir = 'experiments/ht_0_0058_semitones_' +  str(NUM_SEMITONES) + '_steps_' + str(STEPS_PER_SEMITONE) + '/'  
    else: # just beat detection with the note-onset+beat capable model
        sub_dir = 'experiments/ht_0_0058/'
    
    experiments_dir =  os.path.join(data_main_dir, sub_dir)
    if not os.path.exists(experiments_dir):
        os.mkdir(experiments_dir)
        

    return experiments_dir   

if __name__ == "__main__":
    
    doit( sys.argv)
