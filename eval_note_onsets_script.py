
import mir_eval
import sys
import os
from doit_all import list_MBID, ordered_list_MBID
from demo import WITH_ONSETS_SAME_PITCH, determine_file_with_extension
from pypYIN.MonoNoteParameters import NUM_SEMITONES, STEPS_PER_SEMITONE,\
    WITH_BEAT_ANNOS, WITH_MELODIA

parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir))
path_intersect_scripts = os.path.join(parentDir, 'otmm_vocal_segments_dataset/scripts')
if path_intersect_scripts not in sys.path:
        sys.path.append(path_intersect_scripts)
        
from load_data import load_aligned_notes

# note onset extension: alignedNotes_vocal.txt


TOLERANCE_TIME = 0.05



def determine_extension(MBID, output_dir, WITH_BEAT_ANNOS):
    if WITH_BEAT_ANNOS:
        estimated_URI = output_dir + MBID + '.onsets.bars'
    else:
        estimated_URI = output_dir + MBID + '.onsets.tony'
    if not WITH_ONSETS_SAME_PITCH:
        estimated_URI += '.no_postprocessing'
    return estimated_URI



def print_eval_onsets_all(data_dir, WITH_BEAT_ANNOS, WITH_DETECTED_BEATS):
    
    print 'computing onset \n same_pitch_onsets ={} \n  with_bar_anno-s = {}, \n  with_detected_beats = {} \n tolerance={},  '.format(WITH_ONSETS_SAME_PITCH, WITH_BEAT_ANNOS, WITH_DETECTED_BEATS, TOLERANCE_TIME) 
    
    totalF = 0
    totalP = 0
    totalR = 0
    
    for MBID in ordered_list_MBID.keys():
        output_dir = data_dir + MBID + '/'
        score_allignment_dir = '/Users/joro/workspace/otmm_audio_score_alignment_dataset/data/'
        annotation_URI = os.path.join(score_allignment_dir + ordered_list_MBID[MBID][0] + '/' + MBID, 'alignedNotes_vocal.txt')
        
        extension = determine_file_with_extension( NUM_SEMITONES, STEPS_PER_SEMITONE, WITH_BEAT_ANNOS, WITH_DETECTED_BEATS)

        estimated_URI = os.path.join(output_dir, MBID + extension)
        
        
        argv = ['dummy', annotation_URI, estimated_URI]
        F, P, R = eval_onsets_one_file(TOLERANCE_TIME, argv)
        P *= 100
        R *= 100
        F *= 100
        
        totalF += F
        totalP += P
        totalR += R
        
        print estimated_URI
#         print 'P: {0:.2f}'.format(P)
#         print 'R: {0:.2f}'.format(R)
#         print 'F: {0:.2f}'.format(F)
        print str(['{:0.1f}'.format(x) for x in [P,R,F]]) . replace("'", "") . replace(",", ""). replace("[", "") . replace("]", "").replace(" ", "\t")
        
    avrgF = totalF/len(ordered_list_MBID)
    avrgP = totalP/len(ordered_list_MBID)
    avrgR = totalR/len(ordered_list_MBID)
    print 'total:'
    print str(['{:0.1f}'.format(x) for x in [avrgP,avrgR,avrgF]]) . replace("'", "") . replace(",", ""). replace("[", "") . replace("]", "").replace(" ", "\t")   

        

def eval_onsets_one_file(TOLERANCE_TIME, argv):
    if len(argv) != 3:
        sys.exit('usage: {} <annotated onset > <detected >'.format(sys.argv[0]))
    annotation_URI = argv[1]
    estimated_URI = argv[2]
    
    reference_onsets_ts, _ = load_aligned_notes(annotation_URI)

    estimated_onsets = mir_eval.io.load_events(estimated_URI)
    F, P, R = mir_eval.onset.f_measure(reference_onsets_ts, estimated_onsets, window=TOLERANCE_TIME)
    return F, P, R


if __name__ == "__main__":

    
#     data_dir = '/Users/joro/workspace/otmm_vocal_segments_dataset/data/'
    if len(sys.argv) != 4:
        sys.exit('usage: {} <results_path> WITH_BEAT_ANNOS WITH_DETECTED_BEATS'.format(sys.argv[0]))
    data_dir = sys.argv[1]    
    WITH_BEAT_ANNOS = int(sys.argv[2])
    WITH_DETECTED_BEATS = int(sys.argv[3])
    print_eval_onsets_all(data_dir, WITH_BEAT_ANNOS, WITH_DETECTED_BEATS)
    
