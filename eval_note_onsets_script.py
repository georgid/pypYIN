import mir_eval
import sys

data_dir = '/Users/joro/Documents/Phd/UPF/voxforge/myScripts/turkish_makam_vocal_segments_dataset/data/'

TOLERANCE_TIME = 0.05

list_rec_IDs = [
#     'f5a89c06-d9bc-4425-a8e6-0f44f7c108ef',
#     'b49c633c-5059-4658-a6e0-9f84a1ffb08b',
#     '567b6a3c-0f08-42f8-b844-e9affdc9d215',
    '9c26ff74-8541-4282-8a6e-5ba9aa5cc8a1',
#     'feda89e3-a50d-4ff8-87d4-c1e531cc1233'
]

def eval_onsets_all(list_rec_IDs):
    for recID in list_rec_IDs:
        output_dir = data_dir + recID + '/' 
        
    #     TODO: fetch from URL 'https://github.com/MTG/turkish_makam_vocal_segments_dataset/tree/master/data'
        annotation_URI = output_dir + recID + '.vocal_onsets_anno' 
        estimated_URI = output_dir + recID + '.onsets.bars.no_postprocessing'
        
        reference_onsets = mir_eval.io.load_events(annotation_URI)
    #     print reference_onsets
        estimated_onsets = mir_eval.io.load_events(estimated_URI)
    #     print estimated_onsets
        F, P, R = mir_eval.onset.f_measure(reference_onsets,                                  estimated_onsets, window=TOLERANCE_TIME)
        print F, P, R

if __name__ == "__main__":
#     eval_onsets_all(list_rec_IDs)

    if len(sys.argv) != 3:
        sys.exit('usage: {} <annotated onset > <detected >'.format( sys.argv[0]) )
    annotation_URI = sys.argv[1]
    estimated_URI = sys.argv[2]
    reference_onsets = mir_eval.io.load_events(annotation_URI)
    estimated_onsets = mir_eval.io.load_events(estimated_URI)
    F, P, R = mir_eval.onset.f_measure(reference_onsets,                                  estimated_onsets, window=TOLERANCE_TIME)
    print F, P, R