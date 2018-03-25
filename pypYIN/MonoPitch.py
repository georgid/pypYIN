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

from MonoPitchHMM import MonoPitchHMM
import numpy as np
from math import *

class MonoPitch(object):
    def __init__(self):
        self.hmm = MonoPitchHMM()

    def process(self, pitchProb):
        obsProb = [self.hmm.calculatedObsProb(pitchProb[0]),]
        for iFrame in range(1,len(pitchProb)):
            obsProb += [self.hmm.calculatedObsProb(pitchProb[iFrame])]

        out = np.array([], dtype=np.float32)

        path, scale = self.hmm.decodeViterbi(obsProb)

        for iFrame in range(len(path)):
            hmmFreq = self.hmm.m_freqs[path[iFrame]]
            bestFreq = 0.0
            leastDist = 10000.0
            if hmmFreq > 0:
                # This was a Yin estimate, so try to get original pitch estimate back
                # ... a bit hacky, since we could have direclty saved the frequency
                # that was assigned to the HMM bin in hmm.calculateObsProb -- but would
                # have had to rethink the interface of that method.
                for iPitch in range(len(pitchProb[iFrame])):
                    freq = 440. * pow(2.0, (pitchProb[iFrame][iPitch][0] - 69)/12.0)
                    dist = fabs(hmmFreq-freq)
                    if dist < leastDist:
                        leastDist = dist
                        bestFreq = freq
            else:
                bestFreq = hmmFreq
            out = np.append(out, bestFreq)
        return out