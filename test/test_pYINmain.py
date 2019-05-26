'''
Created on Mar 8, 2017

@author: joro
'''
import unittest
from pypYIN.pYINmain import PyinMain
from pypYIN.MonoNote import FrameOutput
import pypYIN.pYINmain
import pypYIN
from demo import calc_rms, extract_predominant_vocal_melody
from pypYIN.MonoNoteParameters import WITH_ONSETS_SAME_PITCH


class Test(unittest.TestCase):


    def testPostprocessPitchTracks(self):
        pYinInst = PyinMain()
        nSPP = 3
        WITH_ONSETS_SAME_PITCH = 0
        
        path_indices_note =  [ 281, 279,  280, 280, 280, 281, 279, 280 ]
        f0_values = [35, 48, 48 , 48 , 48 , 0, 0 ,0 ]
        
        ################# simulate  method  pypYIN.MonoNote.MonoNote.path_to_stepstates
        out = [] # convert to a list of FrameOutput type
        for iFrame in range(len(path_indices_note)):
            currPitch = -1
            stateKind = (path_indices_note[iFrame]) % nSPP + 1 # 1: attack, 2: sustain, 3: silence
            out.append(FrameOutput(iFrame, currPitch, stateKind))
            
        featureSet = pYinInst.postprocessPitchTracks(f0_values, out, WITH_ONSETS_SAME_PITCH)
        self.assertEquals(featureSet.onsetFrames, [1])
    
    def test_note_transcription(self):
        
        '''
        with melodia, for Enlish pop
        '''
        audio_filename = 'example/TRALLSG128F425A685.wav'
        beat_file_URI = 'example/TRALLSG128F425A685.beats'
        
        frameSize = 2048
        hopSize = 256
        fs = 44100 
        hop_time = float(hopSize)/float(fs)

        pYinInst = pypYIN.pYINmain.PyinMain()
        pYinInst.initialise(channels=1, inputSampleRate=fs, stepSize=hopSize, blockSize=frameSize, lowAmp=0.25, onsetSensitivity=0.7, pruneThresh=0.1)
        
        calc_rms(pYinInst, audio_filename)
    
        if pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS:
            from pypYIN.YinUtil import load_beat_anno
            bar_position_ts, bar_labels = load_beat_anno(beat_file_URI, 0) #
            usul_type = '44' 
        else:
            bar_position_ts = []
            bar_labels = []
            usul_type = None
        
        ########### extract  pitch from polyphonic
        estimatedPitch_vocal = extract_predominant_vocal_melody(audio_filename, hopSize, frameSize, pYinInst)
        pYinInst.setDecodedMonoPitch(estimatedPitch_vocal) # not sure if this really changes s.th., but does not break things
        
        ### note transcription
        featureSet, MIDI_pitch_contour = pYinInst.segment_notes(estimatedPitch_vocal, pypYIN.MonoNoteParameters.WITH_BEAT_ANNOS, bar_position_ts, bar_labels, hop_time, usul_type) # 1. convert to MIDI. 2. note segmentation.
    
        featureSet = pYinInst.postprocessPitchTracks(MIDI_pitch_contour, featureSet.m_oMonoNoteOut, WITH_ONSETS_SAME_PITCH) # postprocess to get onsets
        
        ########## print note step states
        noteStates = []
        for mnOut in featureSet.m_oMonoNoteOut:
            noteStates.append(mnOut.noteState)
        print(noteStates)
#         print featureSet.onsetFrames
        assert 1
         

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPostprocessPitchTracks']
    unittest.main()