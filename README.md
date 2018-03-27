# pypYIN
python pYIN

Pitch and note tracking in monophonic (a cappella) audio  

This is a fork of the python version of pYIN of Matthias Mauch originally ported [here](https://github.com/ronggong/pypYIN)


In this fork, following modifications of the original implementation are made: 

- we add efficient numpy data structures for HMM-based note-segmentation (2. step of pYIN)   

- the transition model for note tracking is adapted to take into account positions in the musical measure/bar.  This is activated by the flag [WITH_BEAT_ANNOS](https://github.com/georgid/pypYIN/blob/master/pypYIN/MonoNoteParameters.py#L55)
More specifically, we use likelihoods of note onset events (in `code.MonoNoteParameters.barPositionDist_Probs`), at different bar position (e.g. from 0 to 9, depending on the bar). In the original version the transition likelihood from silence to a following note attack state is distributed by the pitch difference from current to following note. NOTE: the sum of the transition likelihoods over all possible following notes is a constant `1-selfSilenceTransition`. In this version, on decoding, this constant is replaced for each time frame by the likelihood of the closest bar position from `barPositionDist_Probs`. This means essentially, that the same pitch-difference distribution scheme is kept, but scaled varyingly when close in time to a beginning of the bar (e.g. scaled more at downbeats and less else).  

- the pYIN pitch tracking is replaced by [predominantmelodymakam](https://github.com/sertansenturk/predominantmelodymakam). The method is in [AlignmentDuration](https://github.com/georgid/AlignmentDuration/blob/5c5ba9064948f36c3349ca2f42156f8a63b1c990/src/align/FeatureExtractor.py#L132)
If you want to eliminate the dependence on it, simply call another pitch extraction algorithm or set [WITH_MELODIA](https://github.com/georgid/pypYIN/blob/master/demo.py#L48)=0  

- for efficient Viterbi decoding numpy is used in the class https://github.com/georgid/pypYIN/blob/master/pypYIN/MonoNoteHMM.py

## pYIN project page
[https://code.soundsoftware.ac.uk/projects/pyin](https://code.soundsoftware.ac.uk/projects/pyin)

## Dependencies
Numpy  
Scipy  
Essentia  
https://github.com/craffel/mir_eval 

## Usage
python demo.py <data directory>  <recording musicbrainz id> <using beats>

## License
 Copyright (C) 2017  Music Technology Group - Universitat Pompeu Fabra  
 
 This file is part of pypYIN  
 
 pypYIN is free software: you can redistribute it and/or modify it under  
 the terms of the GNU Affero General Public License as published by the Free  
 Software Foundation (FSF), either version 3 of the License, or (at your  
 option) any later version.  
 
 This program is distributed in the hope that it will be useful, but WITHOUT  
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS  
 FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more  
 details.  
 
 You should have received a copy of the Affero GNU General Public License  
 version 3 along with this program.  If not, see http://www.gnu.org/licenses/  

## Citation

> Georgi Dzhambazov, André Holzapfel, Ajay Srinivasamurthy, Xavier Serra, 
> Metrical-Accent Aware Vocal Onset Detection in Polyphonic Audio, In Proceedings of ISMIR 2017


## Contact
 If you have any problem about this python version code, please contact:
 georgi.dzhambazov@upf.edu  
 
 If you have any problem about this algorithm, I suggest you to contact: Matthias Mauch  
 m.mauch@qmul.ac.uk who is the original C++ version author of this algorithm or consider the paper 
 > M. Mauch, C. Cannam, R. Bittner, G. Fazekas, J. Salamon, J. Dai, J. Bello and S. Dixon,  
 > “Computer-aided Melody Note Transcription Using the Tony Software: Accuracy and Efficiency”,  
 > in Proceedings of the First International Conference on Technologies for  
 > Music Notation and Representation, 2015.  

