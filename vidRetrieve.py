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
    dict = {v:k for k,v in json.load(open(\
    '/home/gengshan/public_html/data/dictTitleAll.json', 'r')).items()}
    if idx in dict.keys():
        return(dict[int(idx)])
    else:
        return None  # doesn't exist

def title2idx(title):
    dict = json.load(open('/home/gengshan/public_html/data/dictTitleAll.json'\
           , 'r'))
    if title in dict.keys():
        return(dict[title])
    else:
        return -1  # doesn't exist

