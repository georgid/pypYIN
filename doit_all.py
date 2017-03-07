'''
Created on Feb 16, 2017

@author: joro
'''
from demo import doit
import collections
    


list_MBID = {}
# list_MBID['f5a89c06-d9bc-4425-a8e6-0f44f7c108ef'] =  'nihavent--sarki--aksak--bakmiyor_cesm-i--haci_arif_bey'
# list_MBID['feda89e3-a50d-4ff8-87d4-c1e531cc1233'] =  'nihavent--sarki--kapali_curcuna--kimseye_etmem--kemani_sarkis_efendi'
list_MBID['9c26ff74-8541-4282-8a6e-5ba9aa5cc8a1'] =    'ussak--sarki--aksak--bu_aksam_gun--tatyos_efendi'
# list_MBID['92ef6776-09fa-41be-8661-025f9b33be4f']  =  'ussak--sarki--duyek--aksam_oldu_huzunlendim--semahat_ozdenses'
#     list_MBID['c7a31756-a7d5-4882-bdf7-9c6b23493597'] = ''    
# list_MBID['cd87a0cc-5f54-4b30-ac1c-01c3cbc423ee'] =  'ussak--sarki--duyek--her_mevsim--semahat_ozdenses'
# list_MBID['eb4d2af4-851c-43f3-aaad-33a5b7bd3c34'] =   'hicaz--sarki--aksak--dil_yaresini--sevki_bey'
# list_MBID['5bcc3b05-e744-410d-b1c9-554d60bc04af'] =  'hicazkar--sarki--kapali_curcuna--mani_oluyor--tatyos_efendi'
# list_MBID['5a3266e9-7b7a-4a99-ab75-872910c80bdd']  =  'hisarbuselik--sarki--aksak--aman_ey--ii_mahmud'
# list_MBID['b244d4e3-2cfb-4475-98d3-73e2d96271f7'] =   'muhayyerkurdi--sarki--duyek--var_mi_hacet--nikogos_aga'

# list_MBID['a2e650dc-8822-4647-9f4c-c41c0f81b601'] =   'neva--sarki--duyek--ben_yururum--selahaddin_pinar'
# list_MBID['7c338e4a-58f5-4c5e-853e-8d7975df5bbc'] =   'muhayyer--sarki--aksak--iltimas_etmeye--haci_arif_bey'
list_MBID['9f172b31-69b9-4cea-bfb0-6b7aaaaadf1c'] = 'hicaz--sarki--aksak--ben_gamli_hazan--melahat_pars'

ordered_list_MBID = collections.OrderedDict(sorted(list_MBID.items()))


def doit_all():

    
    for MBID in ordered_list_MBID.keys():
        data_dir = '/Users/joro/workspace/otmm_vocal_segments_dataset/data/'
        
        doit(['dummy', data_dir+MBID + '/', MBID ]) 

if __name__ == '__main__':
    doit_all()