'''
Created on Mar 8, 2017

@author: joro
'''
import unittest
from pypYIN.pYINmain import PyinMain
from pypYIN.MonoNote import FrameOutput


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
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testPostprocessPitchTracks']
    unittest.main()