import mir_eval
import sys



data_dir = '/Users/joro/Documents/Phd/UPF/voxforge/myScripts/turkish_makam_vocal_segments_dataset/data/'

TOLERANCE_TIME = 0.05

list_rec_IDs = [
    'f5a89c06-d9bc-4425-a8e6-0f44f7c108ef',
#     'b49c633c-5059-4658-a6e0-9f84a1ffb08b',
#     '567b6a3c-0f08-42f8-b844-e9affdc9d215',
    '9c26ff74-8541-4282-8a6e-5ba9aa5cc8a1',
    'feda89e3-a50d-4ff8-87d4-c1e531cc1233',
    '92ef6776-09fa-41be-8661-025f9b33be4f'
]

def eval_onsets_one_file(TOLERANCE_TIME, argv):
    if len(argv) != 3:
        sys.exit('usage: {} <annotated onset > <detected >'.format(sys.argv[0]))
    annotation_URI = argv[1]
    estimated_URI = argv[2]
    reference_onsets = mir_eval.io.load_events(annotation_URI)
    estimated_onsets = mir_eval.io.load_events(estimated_URI)
    F, P, R = mir_eval.onset.f_measure(reference_onsets, estimated_onsets, window=TOLERANCE_TIME)
    return F, P, R


def eval_onsets_all(list_rec_IDs):
    totalF = 0
    totalP = 0
    totalR = 0
    for recID in list_rec_IDs:
        output_dir = data_dir + recID + '/' 
        
    #     TODO: fetch from URL 'https://github.com/MTG/turkish_makam_vocal_segments_dataset/tree/master/data'
        annotation_URI = output_dir + recID + '.vocal_onsets_anno' 
        estimated_URI = output_dir + recID + '.onsets.bars.no_postprocessing'
        estimated_URI = output_dir + recID + '.onsets.bars'

#         estimated_URI = output_dir + recID + '.onsets.tony.no_postprocessing'
        estimated_URI = output_dir + recID + '.onsets.tony'

        
        reference_onsets = mir_eval.io.load_events(annotation_URI)
    #     print reference_onsets
        estimated_onsets = mir_eval.io.load_events(estimated_URI)
    #     print estimated_onsets
        F, P, R = mir_eval.onset.f_measure(reference_onsets,                                  estimated_onsets, window=TOLERANCE_TIME)
        totalF += F
        totalP += P
        totalR += R
    return totalF/len(list_rec_IDs), totalP/len(list_rec_IDs), totalR/len(list_rec_IDs)

if __name__ == "__main__":
    F, P, R = eval_onsets_all(list_rec_IDs)

#     F, P, R = eval_onsets_one_file(TOLERANCE_TIME)
    print 'F: {0:.4f}'.format( F )
    print 'P: {0:.4f}'.format( P )
    print 'R: {0:.4f}'.format( R )