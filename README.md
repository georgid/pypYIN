# pypYIN
python pYIN

A python version of pYIN of Matthias Mauch  
Pitch and note tracking in monophonic audio  
In this fork, two modifications are made: 
- the transition model for note tracking is adapted to take into account positions in the musical measure/bar.  
More specifically, we use likelihoods of note onset events (in `code.MonoNoteParameters.barPositionDist_Probs`), at different bar position (e.g. from 0 to 9, depending on the bar). In the original version the transition likelihood from silence to a following note attack state is distributed by the pitch difference from current to following note. NOTE: the sum of the transition likelihoods over all possible following notes is a constant `1-selfSilenceTransition`. In this version, on decoding, this constant is replaced for each time frame by the likelihood of the closest bar position from `barPositionDist_Probs`. This means essentially, that the same pitch-difference distribution scheme is kept, but scaled varyingly when close in time to a beginning of the bar (e.g. scaled more at downbeats and less else).  
- the pYIN pitch tracking is replaced by melodia

## pYIN project page
[https://code.soundsoftware.ac.uk/projects/pyin](https://code.soundsoftware.ac.uk/projects/pyin)

## Dependencies
Numpy  
Scipy  
Essentia  

## Usage
MBID=92ef6776-09fa-41be-8661-025f9b33be4f;
path_rec=/Users/joro/workspace/otmm_vocal_segments_dataset/data/92ef6776-09fa-41be-8661-025f9b33be4f/;
python demo.py $path_rec  $MBID

### Initialise:  
Here are the parameters which need to be initialised before executing the main program:  

inputSampleRate:      sampling rate
stepSize:             hopSize  
blockSize:            frameSize  
lowAmp(0,1):          RMS of audio frame under lowAmp will be considered non voiced  
onsetSensitivity:     high value means note is easily separated into two notes if low amplitude is presented.  
pruneThresh(second):  discards notes shorter than this threshold

### Output:
Transcribed notes in Hz  
Smoothed pitch track  
Pitch tracks of transcribed notes in MIDI note number  

### Other issues:
See demo.py  
To set bar-position-aware scheme, set the parameter WITH_BAR_POSITIONS = 1

## License
 Copyright (C) 2015  Music Technology Group - Universitat Pompeu Fabra  
 
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

 If you have any problem about this python version code, please contact: Rong Gong  
 rong.gong@upf.edu  
 
 If you have any problem about this algorithm, I suggest you to contact: Matthias Mauch  
 m.mauch@qmul.ac.uk who is the original C++ version author of this algorithm  
 
 If you want to refer this code, please consider these articles: 
 
 > M. Mauch and S. Dixon,  
 > “pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions”,  
 > in Proceedings of the IEEE International Conference on Acoustics,  
 > Speech, and Signal Processing (ICASSP 2014), 2014.  
 
 > M. Mauch, C. Cannam, R. Bittner, G. Fazekas, J. Salamon, J. Dai, J. Bello and S. Dixon,  
 > “Computer-aided Melody Note Transcription Using the Tony Software: Accuracy and Efficiency”,  
 > in Proceedings of the First International Conference on Technologies for  
 > Music Notation and Representation, 2015.  

