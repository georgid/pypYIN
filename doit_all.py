'''
Created on Feb 16, 2017

@author: joro
'''
from demo import doit
import collections
import sys
import os
from pypYIN.MonoNoteParameters import STEPS_PER_SEMITONE, NUM_SEMITONES,\
    WITH_NOTES_STATES, WITH_BEAT_ANNOS
    


# symbTr name is hard coded, because the function to get returns sometimes inproper naming....

# sorted by bar-state space size in increasing order
list_MBID = {}
# duyek
list_MBID['f5a89c06-d9bc-4425-a8e6-0f44f7c108ef'] =  ('nihavent--sarki--aksak--bakmiyor_cesm-i--haci_arif_bey',188)
list_MBID['9c26ff74-8541-4282-8a6e-5ba9aa5cc8a1'] =    ('ussak--sarki--aksak--bu_aksam_gun--tatyos_efendi',240)
list_MBID['7c338e4a-58f5-4c5e-853e-8d7975df5bbc'] =   ('muhayyer--sarki--aksak--iltimas_etmeye--haci_arif_bey',129)
list_MBID['9f172b31-69b9-4cea-bfb0-6b7aaaaadf1c'] = ('hicaz--sarki--aksak--ben_gamli_hazan--melahat_pars',123)

# aksak
list_MBID['a2e650dc-8822-4647-9f4c-c41c0f81b601'] =   ('neva--sarki--duyek--ben_yururum--selahaddin_pinar',145)
# list_MBID['c7a31756-a7d5-4882-bdf7-9c6b23493597'] = ('rast--sarki--duyek--hicran_olacaksa--ferit_sidal', 141)    # no annotation
list_MBID['cd87a0cc-5f54-4b30-ac1c-01c3cbc423ee'] =  ('ussak--sarki--duyek--her_mevsim--semahat_ozdenses',125)
list_MBID['b244d4e3-2cfb-4475-98d3-73e2d96271f7'] =   ('muhayyerkurdi--sarki--duyek--var_mi_hacet--nikogos_aga',116)


# curcuna
# list_MBID['feda89e3-a50d-4ff8-87d4-c1e531cc1233'] =  ('nihavent--sarki--kapali_curcuna--kimseye_etmem--kemani_sarkis_efendi',203)
# list_MBID['5bcc3b05-e744-410d-b1c9-554d60bc04af'] =  ('hicazkar--sarki--kapali_curcuna--mani_oluyor--tatyos_efendi',210)
# list_MBID['7115dba2-8a0f-4f50-b1e1-f1cca26535b0'] =  ('huseyni--sarki--curcuna--cektim_elimi--tatyos_efendi',240)
# list_MBID['7aec9833-6482-4917-87bd-e60c7c1dae3c'] =  ('rast--sarki--kapali_curcuna--nedendir_bu--sevki_bey',188)



# list_MBID['5a3266e9-7b7a-4a99-ab75-872910c80bdd']  =  ('hisarbuselik--sarki--aksak--aman_ey--ii_mahmud', 116) # needs 47 Giga, not done
    
### those are excluded as very long audio
# list_MBID['92ef6776-09fa-41be-8661-025f9b33be4f']  =  ('ussak--sarki--duyek--aksam_oldu_huzunlendim--semahat_ozdenses',101) # the beat annotations start at 32 second, so one should forbid the beat detector to detect before 32
# list_MBID['eb4d2af4-851c-43f3-aaad-33a5b7bd3c34'] =   ('hicaz--sarki--aksak--dil_yaresini--sevki_bey',96)


ordered_list_MBID = collections.OrderedDict(sorted(list_MBID.items()))


def create_output_dirs(data_dir, with_beat_annotations=True):
    
    if with_beat_annotations:
        sub_dir = 'experiments/beat_anno/'
    elif WITH_NOTES_STATES: 
        sub_dir = 'experiments/ht_0_0058_semitones_' +  str(NUM_SEMITONES) + '_steps_' + str(STEPS_PER_SEMITONE) + '/'  
    else: # just beat detection
        sub_dir = 'experiments/ht_0_0058/'
    
    experiments_dir =  os.path.join(data_dir, sub_dir)
    if not os.path.exists(experiments_dir):
        os.mkdir(experiments_dir)
        
    for MBID in ordered_list_MBID.keys():
            MBID_dir  = os.path.join(experiments_dir, MBID)
            if not os.path.exists(MBID_dir):
                os.mkdir(MBID_dir)
    return experiments_dir        





def doit_all(argv):
    
    
    if len(argv) != 2:
        sys.exit('usage: {} <data dir> '.format(argv[0]))
    data_dir = argv[1]
#     data_dir = '/Users/joro/workspace/otmm_vocal_segments_dataset/'
    
    output_dir = create_output_dirs(data_dir, WITH_BEAT_ANNOS)
    input_dir = data_dir + '/data/'
    
    for MBID in ordered_list_MBID.keys():
#         print 'MBID={}'.format(MBID)
#         print 'python ~/workspace/madmom_notes/bin/GMMNotePatternTracker single  -o $PATH_DATASET/experiments/ht_0_02/$MBID/$MBID.estimatedbeats   $PATH_DATASET/data/$MBID/$MBID.wav'
#         print '/Users/joro/workspace/otmm_vocal_segments_dataset/data/' + MBID + '/' + MBID + '.wav'
        doit(['dummy', input_dir + '/', MBID, output_dir ]) 

if __name__ == '__main__':
    doit_all(sys.argv)