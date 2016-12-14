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
 * ‚Äö√Ñ√∫pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions‚Äö√Ñ√π,
 * in Proceedings of the IEEE International Conference on Acoustics,
 * Speech, and Signal Processing (ICASSP 2014), 2014.
 *
 * M. Mauch, C. Cannam, R. Bittner, G. Fazekas, J. Salamon, J. Dai, J. Bello and S. Dixon,
 * ‚Äö√Ñ√∫Computer-aided Melody Note Transcription Using the Tony Software: Accuracy and Efficiency‚Äö√Ñ√π,
 * in Proceedings of the First International Conference on Technologies for
 * Music Notation and Representation, 2015.
'''

import os, sys
import mir_eval
dir = os.path.dirname(os.path.realpath(__file__))
srcpath = dir+'/src'
sys.path.append(srcpath)

import pYINmain
import essentia.standard as ess
import numpy as np
from YinUtil import RMS

if __name__ == "__main__":
    
#     if len(sys.argv) != 2:
#         sys.exit('usage: {} <recording path>'.format( sys.argv[0]) )
#     filename1 = sys.argv[1]
    
    # initialise
    filename1 = srcpath + '/../vignesh_short.wav'
    filename1 = srcpath + '/../vignesh.wav'

    fs = 44100
    frameSize = 2048
    hopSize = 128
    num_frames_per_sec = float(fs/ hopSize)
    
    pYinInst = pYINmain.PyinMain()
    pYinInst.initialise(channels = 1, inputSampleRate = fs, stepSize = hopSize, blockSize = frameSize,
                   lowAmp = 0.25, onsetSensitivity = 0.7, pruneThresh = 0.1)

    # frame-wise calculation
    audio = ess.MonoLoader(filename = filename1, sampleRate = fs)()


    ########### extract pitch with pYIN
    for frame in ess.FrameGenerator(audio, frameSize=frameSize, hopSize=hopSize):
        featureSet = pYinInst.process(frame)
    
    ##### calculate smoothed pitch and mono note
    estimatedPitch_vocal = pYinInst.getSmoothedPitchTrack() # this is just pitch 
#     for i in range(len(estimatedPitch_vocal)): # to be same as melodia. for comparison in visualization.
#         if estimatedPitch_vocal[i] < 0:
#             estimatedPitch_vocal[i] = 0
#              

    
    ########### extract mono pitch with sercan's melodia
#     from predominantmelodymakam.predominantmelodymakam import PredominantMelodyMakam
#     extractor = PredominantMelodyMakam(hop_size=hopSize, frame_size=frameSize)
#     results = extractor.run(filename1)
#     extractedPitchList = results['pitch']
#       
#     estimatedPitch_andTs = numpy.array(extractedPitchList)
# 
#     
#     ####### read vocal annotation from file
#     parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir))
#     path_intersect_scripts = os.path.join(parentDir, 'turkish_makam_vocal_segments_dataset/scripts')
#     if path_intersect_scripts not in sys.path:
#         sys.path.append(path_intersect_scripts)
#     from intersect_vocal_and_pitch import intersect_section_links
#     voiced_intervals = mir_eval.io.load_intervals('/Users/joro/Downloads/vignesh.vocalNonVocal')
#     estimatedPitch_andTs_vocal =  intersect_section_links(estimatedPitch_andTs, voiced_intervals) # onsets with pitch
#     
#     estimatedPitch_vocal = estimatedPitch_andTs_vocal[:,1]
#     pYinInst.setDecodedMonoPitch(estimatedPitch_vocal)
        
    # output smoothed pitch track
#     print 'pitch track'
#     for ii in pYinInst.fs.m_oSmoothedPitchTrack: # and this has other values
#         print ii.values
#     print '\n'
    
    featureSet, MIDI_pitch_contour = pYinInst.getRemainingFeatures(estimatedPitch_vocal) # 1. convert to MIDI. 2. note segmentation.
    featureSet = pYinInst.noteStatesToPitchTracks(MIDI_pitch_contour, featureSet.m_oMonoNoteOut) 

    # output of mono notes,
    # column 0: frame number,
    # column 1: pitch in midi numuber, this is the decoded pitch
    # column 2: note state: attack 1, stable 2, silence 3
    
    print 'mono note decoded pitch'
    for ii in featureSet.m_oMonoNoteOut:
        ts = float(ii.frameNumber / num_frames_per_sec)
        print ts, ii.pitch, ii.noteState
        print '\n'
    
    ###################### serialize note onset timestamps 
    filename1_detected_onsets = filename1[:-4] + '.onsets.tony'
    
    import csv
    f = open (filename1_detected_onsets, 'w')
    csv_writer = csv.writer(f)
    for onset_frame in featureSet.onsetFrames:
        ts = float(onset_frame / num_frames_per_sec) # first frame centered at 0, becasue using FrameCutter in essentia
        csv_writer.writerow([ts])
    print    'mono note decoded onsets written to file '  + filename1_detected_onsets + '\n'
    f.close()
    
    print 'note pitch tracks'
    for ii in featureSet.m_oNotePitchTracks:
        print ii
    print '\n'

    # median pitch in Hz of the notes
    print 'median note pitch'
    for ii in featureSet.m_oNotes:
        print ii.values
    print '\n'

