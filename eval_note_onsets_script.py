
import mir_eval
import sys
import os
from doit_all import list_MBID, ordered_list_MBID
from demo import WITH_BAR_POSITIONS

parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__) ), os.path.pardir))
path_intersect_scripts = os.path.join(parentDir, 'otmm_vocal_segments_dataset/scripts')
if path_intersect_scripts not in sys.path:
        sys.path.append(path_intersect_scripts)
        
from load_data import load_aligned_notes

# note onset extension: alignedNotes_vocal.txt

data_dir = '/Users/joro/workspace/otmm_vocal_segments_dataset/data/'

TOLERANCE_TIME = 0.05



def eval_onsets_one_file(TOLERANCE_TIME, argv):
    if len(argv) != 3:
        sys.exit('usage: {} <annotated onset > <detected >'.format(sys.argv[0]))
    annotation_URI = argv[1]
    estimated_URI = argv[2]
    
    reference_onsets_ts, _ = load_aligned_notes(annotation_URI)

    estimated_onsets = mir_eval.io.load_events(estimated_URI)
    F, P, R = mir_eval.onset.f_measure(reference_onsets_ts, estimated_onsets, window=TOLERANCE_TIME)
    return F, P, R


def eval_onsets_all(list_rec_IDs):
    '''
    combine events together and eval together
    '''
    totalF = 0
    totalP = 0
    totalR = 0
    for recID in list_rec_IDs:
        output_dir = data_dir + recID + '/' 
        
    #     TODO: fetch from URL 'https://github.com/MTG/turkish_makam_vocal_segments_dataset/tree/master/data'
        annotation_URI = output_dir + recID + '.vocal_onsets_anno' 
        estimated_URI = output_dir + recID + '.onsets.bars'

#         estimated_URI = output_dir + recID + '.onsets.bars.no_postprocessing'
#         estimated_URI = output_dir + recID + '.onsets.tony.no_postprocessing'
        estimated_URI = output_dir + recID + '.onsets.tony'

        
        reference_onsets = mir_eval.io.load_events(annotation_URI)
    #     print reference_onsets
        estimated_onsets = mir_eval.io.load_events(estimated_URI)
    #     print estimated_onsets
        F, P, R = mir_eval.onset.f_measure(reference_onsets, estimated_onsets, window=TOLERANCE_TIME)
        totalF += F
        totalP += P
        totalR += R
    return totalF/len(list_rec_IDs), totalP/len(list_rec_IDs), totalR/len(list_rec_IDs)

if __name__ == "__main__":
#     F, P, R = eval_onsets_all(list_rec_IDs)
    
    for MBID in ordered_list_MBID.keys():
        data_dir = '/Users/joro/workspace/otmm_vocal_segments_dataset/data/'
        output_dir = data_dir + MBID + '/' 
        score_allignment_dir = '/Users/joro/workspace/otmm_audio_score_alignment_dataset/data/'
        annotation_URI = os.path.join(score_allignment_dir + ordered_list_MBID[MBID] + '/' + MBID, 'alignedNotes_vocal.txt' )
        if WITH_BAR_POSITIONS:
            estimated_URI = output_dir + MBID + '.onsets.bars'
        else:
            estimated_URI = output_dir + MBID + '.onsets.tony.no_postprocessing'
        argv = ['dummy', annotation_URI, estimated_URI ]         
   
        F, P, R = eval_onsets_one_file(TOLERANCE_TIME, argv)
        P *= 100
        R *= 100
        F *= 100
        
#         print MBID
#         print '{0:.2f}'.format( P )
        print '{0:.2f}'.format( R )
#         print '{0:.2f}'.format( F )
#         print