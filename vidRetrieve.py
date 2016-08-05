####
 # Filename:        vidRetrieve.py
 # Date:            Aug 05 2016
 # Last Edited by:  Gengshan Yang
 # Description:     Retrive video title by index.
 #                  Usage: idx2title(1)
 #                  Retrive video number by title.
 #                  Usage: title2idx(FvWTyzjD690)
 ####

import json

def idx2title(idx):
    return({v:k for k,v in json.load(open(\
    '/home/gengshan/public_html/data/ori_data_list.json', 'r')).items()}\
    [int(idx)])

def title2idx(title):
    return(json.load(open('/home/gengshan/public_html/data/ori_data_list.json'\
           , 'r'))[title])

