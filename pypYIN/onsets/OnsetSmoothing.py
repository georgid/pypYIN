'''
Created on Apr 5, 2016

@author: joro
'''

from scipy.stats import norm
from numpy.core.function_base import linspace
import numpy

class OnsetSmoothingFunction(object):
    '''
    Smooths/distributes the probability to gradually decay with increasing distance from onset (or event in generally), 
     uses half lobe of normal distribution
    
    to reduce code dependency copied from https://github.com/georgid/AlignmentDuration/tree/noteOnsets/src/onsets  
    '''

    def __init__(self, ONSET_SIGMA_IN_FRAMES):
        '''
        Constructor
        ONSET_SIGMA_IN_FRAMES: 
            the distance to onset, unit: number of frames, zero means at an onset frame
        '''
        
        minVal = norm.ppf(0.01)
        maxVal= norm.ppf(0.5)
    
        quantileVals  = linspace(maxVal, minVal, ONSET_SIGMA_IN_FRAMES + 1 )
        self.liks = numpy.zeros((ONSET_SIGMA_IN_FRAMES + 1,1)) 
        
        for onsetDist in range(ONSET_SIGMA_IN_FRAMES + 1):
            self.liks[onsetDist] = norm.pdf(quantileVals[onsetDist])
    
    def calcOnsetWeight(self, onsetDist):
        '''
        according to noraml distribution
        '''
#         g = 1.0/(onsetDist + 1)
    
        
        return self.liks[onsetDist]


def getDistFromEvent(noteOnsets, t):
        '''
        get distance in frames from time t to closest onset
        start at onset and keep looking right and left simultanously while it finds a 1
        
        to reduce code dependency copied from https://github.com/georgid/AlignmentDuration/tree/noteOnsets/src/onsets/OnsetDetector.py  
        
        Parameters
        -------------------------
        noteOnsets: list of size equal to timeframes
            1-s at timeframes with onsets, all other frames = 0
        
        Returns
        --------------------------
        dist
        iFrame: int
            index of frame with closest 
         
        '''
        #### find closest onset 
        dist = 0
        rightIdx = t
        leftIdx = t
        while  noteOnsets[rightIdx] == 0 and  noteOnsets[leftIdx] == 0:
            dist += 1
            rightIdx =  min(t + dist, noteOnsets.shape[0]-1)
            leftIdx = max(t - dist, 0) 
        if noteOnsets[rightIdx] == 1:
            iFrame = rightIdx
        else:
            iFrame = leftIdx
        return dist, iFrame
    
if __name__ == '__main__':
    
    osf = OnsetSmoothingFunction(7)
    for i in range(8):    
        print osf.calcOnsetWeight(i)