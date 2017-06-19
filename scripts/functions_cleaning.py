import pandas as pd
import numpy as np
import glob
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.cm as cm
import seaborn as sns
import itertools
import re
import time
import math
import json
import random

from collections import Counter

def time_to_slot(seconds) :
	return math.floor(seconds/5)

def seconds_displayed(sec) :
    sign = '-' if (int(sec) < 0) else ''
    s = abs(int(sec))
    minutes, seconds= divmod(s, 60)
    return sign + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)

def minutes_displayed(sec) :
	sign = '-' if (int(sec) < 0) else ''
	return sign + str(int(np.round(abs(int(sec))/60))) + '\''


def time_to_seconds(string) :
	pattern = re.compile('.*\n.*') 
	times = string.split('\n') if pattern.match(string) else string.split(' ')
	final_times = [-0.1]
	for a in times : 
		first_split = a.split(',')
		second_split = first_split[0].split(':')
		final_times.append(3600*int(second_split[0]) + 60*int(second_split[1]) + int(second_split[2]) + int(first_split[1])/1000)
	return final_times

def extract_fancy_timestamps(string) :
    pattern = re.compile('.*\n.*') 
    times = string.split('\n') if pattern.match(string) else string.split(' ')
    final_times = ['00:00']
    for a in times : 
        first_split = a.split(',')
        second_split = first_split[0].split(':')
        final_times.append(second_split[1] + ":" + second_split[2])
    slide_change_timestamps = {}
    for x in range(0,len(final_times)-1) :
        slide_change_timestamps[x] = [final_times[x], final_times[x+1]]
    return slide_change_timestamps

def get_interval(slides_changes):
	intervals = {}
	for i in range(0,len(slides_changes)-1) :
		intervals[i] = slides_changes[i+1] - slides_changes[i]
	return intervals

def compute_time_diff(df,row) :
	if row <= 0 :
		return 0
	else :
		if df['AccountUserID'][row] != df['AccountUserID'][row-1] : 
			return 10
		return df['TimeStamp'][row] - df['TimeStamp'][row-1]

def details_slides(slides_changes) :

    beginning = 0
    end = max(slides_changes)
    length_bar = 640
    ratio_slide_timestamp = []
    slide_timestamp = []

    for x in slides_changes :
        ts = 0 if x < 0 else x
        ratio_slide_timestamp.append(np.round(ts*length_bar/end*2)/2)
        slide_timestamp.append(math.ceil(ts))

    size_slide = {}
    slide_times = {}
    for x in range(1,len(ratio_slide_timestamp)) :
        size_slide[x-1] = [ratio_slide_timestamp[x-1],ratio_slide_timestamp[x]-ratio_slide_timestamp[x-1],
                           length_bar-ratio_slide_timestamp[x]]
    
    for x in range(0,len(slide_timestamp)) :
        slide_times[x] = [int(slide_timestamp[x]),seconds_displayed(slide_timestamp[x]), '-'+seconds_displayed(end-slide_timestamp[x])]

    return size_slide, slide_times, slide_timestamp

def click_views(df_click_views_full,slide_change,interval_limit,minimal_interval,intervals) :
	
	df_click_views = df_click_views_full[df_click_views_full['EventType'] == 'Video.Seek'].copy()

	# Depends on the platform (Coursera / EDX)

	# Coursera
	# df_click_views.drop(['DataPackageID','SessionUserID','VideoID','CurrentTime',
	#                      'SeekType','NewSpeed','EventType'], axis=1, inplace=True)

	# EDX
	df_click_views.drop(['DataPackageID','VideoID','SeekType','NewSpeed','EventType'], axis=1, inplace=True)

	df_click_views.sort_values(['AccountUserID','TimeStamp'], inplace=True)
	df_click_views = df_click_views.reset_index()
	df_click_views['time_slot'] = df_click_views.apply(lambda row : compute_time_diff(df_click_views,row.name), axis=1)

	df_click_views = df_click_views[df_click_views['time_slot'] >= interval_limit]

	df_click_views['oldtime_slots'] = pd.cut(df_click_views['OldTime'], slide_change,labels=[x for x in range(0,len(slide_change)-1)])
	df_click_views['newtime_slots'] = pd.cut(df_click_views['NewTime'], slide_change,labels=[x for x in range(0,len(slide_change)-1)])
	df_click_views['TimeDiff'] = df_click_views['NewTime'] - df_click_views['OldTime']
	df_click_views['SameSlot'] = df_click_views.apply(lambda row : 1 if row['oldtime_slots'] ==
													  row['newtime_slots'] else 0,axis=1)

	df_click_views = df_click_views[df_click_views['TimeDiff'].apply(lambda x : abs(x) > minimal_interval) ]

	df_click_views.to_csv('../deprecated/temp.csv')
	df_click_views = pd.read_csv('../deprecated/temp.csv')
	df_click_views.drop(['Unnamed: 0'], axis=1, inplace=True)

	df_click_views['SlotDiff'] = df_click_views['newtime_slots'] - df_click_views['oldtime_slots']

	df_click_views = df_click_views[df_click_views['TimeDiff'] != 0].copy()

	df_click_views['old_slots'] = df_click_views['oldtime_slots'].apply(lambda x : 'source ' + str(x))
	df_click_views['new_slots'] = df_click_views['newtime_slots'].apply(lambda x : 'target ' + str(x))
	
	df_click_views['source_interval_length'] = df_click_views['oldtime_slots'].apply(lambda x : intervals[x])
	df_click_views['target_interval_length'] = df_click_views['newtime_slots'].apply(lambda x : intervals[x])


	print('Minimum Time Difference to be considered as a Seek : {} seconds'.format(interval_limit))
	print('Minimum interval between two different Seeks : {} seconds'.format(minimal_interval))

	print('Percentage of jumps inside the same Slide : ',
		int(len(df_click_views[df_click_views['SameSlot'] 
									 == 1])/len(df_click_views)*10000)/100, '%')
	print("Total number of Seeks : ", len(df_click_views))
	print("Total number of Seeks between different Slides : ",len(df_click_views[df_click_views['SameSlot'] != 1]) )

	return df_click_views.sort_values(['AccountUserID','TimeStamp'])

def write_to_json_source_target(dataframe, path_name, size_slide, fancy_timestamps, slide_times):

    df_grpby_target = dataframe.groupby(['target']).agg({'value' : 'sum'})
    df_grpby_target.reset_index(inplace=True)
    df_grpby_target['slide'] = df_grpby_target['target'].apply(lambda x : x.split(' ')[1])
    df_grpby_target['slide'] = pd.to_numeric(df_grpby_target['slide'])
    df_grpby_target['norm_ratio'] = df_grpby_target['value']/df_grpby_target['value'].max()
    df_grpby_target['alpha'] = df_grpby_target['norm_ratio'].apply(lambda x : x*0.8 + 0.1)

    df_grpby_source = dataframe.groupby(['source']).agg({'value' : 'sum'})
    df_grpby_source.reset_index(inplace=True)
    df_grpby_source['slide'] = df_grpby_source['source'].apply(lambda x : x.split(' ')[1])
    df_grpby_source['slide'] = pd.to_numeric(df_grpby_source['slide'])
    df_grpby_source['norm_ratio'] = df_grpby_source['value']/df_grpby_source['value'].max()
    df_grpby_source['alpha'] = df_grpby_source['norm_ratio'].apply(lambda x : x*0.8 + 0.1)

    alpha_target = {}
    total_incoming = {}
    for x in df_grpby_target.iterrows() :
        alpha_target[x[1].slide] = x[1].alpha
        total_incoming[x[1].slide] = x[1].value

    alpha_source = {}
    total_outgoing = {}
    for x in df_grpby_source.iterrows() :
        alpha_source[x[1].slide] = x[1].alpha
        total_outgoing[x[1].slide] = x[1].value

    flare = dict()
    flare = {"links" : [], "nodes":[]}

    color = "#C0C0C0"

    for source in range(0, len(dataframe.source.unique())) :
        flare['nodes'].append({'name' : 'source ' + str(source).zfill(2), 'color' : '#0057e7', 'alpha' : alpha_source[source], 'class_type' : 'source',
            'progress_before' : size_slide[source][0], 'progress_highlight' : size_slide[source][1], 'progress_after' : size_slide[source][2],
            'timestamp_start' : fancy_timestamps[source][0], 'timestamp_end' : fancy_timestamps[source][1], 'incoming_links' : total_incoming[source],
            'outgoing_links' : total_outgoing[source], 'remaining_time_start' : slide_times[source][2], 'starting_time' : slide_times[source][0]})
    for target in range(0, len(dataframe.target.unique())) :
        current_alpha = alpha_target[target] if target in alpha_target.keys() else 0.1;
        flare['nodes'].append({'name' : 'target ' + str(target).zfill(2), 'color' : '#008744', 'alpha' : current_alpha, 'class_type' : 'target',
            'progress_before' : size_slide[target][0], 'progress_highlight' : size_slide[target][1], 'progress_after' : size_slide[target][2],
            'timestamp_start' : fancy_timestamps[target][0], 'timestamp_end' : fancy_timestamps[target][1], 'incoming_links' : total_incoming[target],
            'outgoing_links' : total_outgoing[target], 'remaining_time_start' : slide_times[target][2], 'starting_time' : slide_times[target][0]})

    for line in dataframe.values:
        source = line[dataframe.columns.get_loc('source')]
        source_n = source[7:].zfill(2)
        source = 'source ' + source_n
        target = line[dataframe.columns.get_loc('target')]
        target_n = target[7:].zfill(2)
        target = 'target ' + target_n
        value_text = line[dataframe.columns.get_loc('value')]
        value = line[dataframe.columns.get_loc('value_norm')]

        flare["links"].append({"source": source, "target": target, "value" : str(value), "value_text" : str(value_text), "color" : color})

    with open('../Visualisation/data/json/' + path_name + '.json', 'w') as outfile:
        json.dump(flare, outfile)

    return df_grpby_target, df_grpby_source

def to_json(df_click_views,df_click_views_jump, path_name, size_slide, fancy_timestamps, slide_times):

	df_to_d3 = df_click_views.groupby(['old_slots','new_slots']).agg({'AccountUserID' : 'count', 'source_interval_length' : 'first','target_interval_length' : 'first'}).copy()
	df_to_d3 = df_to_d3.reset_index().rename(index=str, columns={'old_slots': 'source', 'new_slots': 'target', 'AccountUserID' : 'value'})
	
	df_to_d3_norm = df_to_d3.copy()
	df_to_d3_grouped = df_to_d3_norm.groupby(['target']).agg({'value' : 'sum'}).copy()
	dict_d3 = {}
	for row in df_to_d3_grouped.reset_index().iterrows() :
		dict_d3[row[1][0]] = row[1][1]
	df_to_d3_norm['value_norm'] = df_to_d3_norm.apply(lambda row : row['value']/dict_d3[row['target']] if dict_d3[row['target']] != 0 else 0, axis=1)
	
	df_to_d3_clean = df_click_views_jump.groupby(['old_slots','new_slots']).agg({'AccountUserID' : 'count', 'source_interval_length' : 'first','target_interval_length' : 'first'}).copy()
	df_to_d3_clean = df_to_d3_clean.reset_index().rename(index=str, columns={'old_slots': 'source', 'new_slots': 'target', 'AccountUserID' : 'value'})

	df_to_d3_clean_norm = df_to_d3_clean.copy()
	df_to_d3_grouped = df_to_d3_clean_norm.groupby(['source']).agg({'value' : 'sum'}).copy()
	dict_d3 = {}
	for row in df_to_d3_grouped.reset_index().iterrows() :
		dict_d3[row[1][0]] = row[1][1]
	df_to_d3_clean_norm['value'] = df_to_d3_clean_norm.apply(lambda row : row['value']/dict_d3[row['source']] if dict_d3[row['source']] != 0 else 0, axis=1)

	aa,bb = write_to_json_source_target(df_to_d3_norm,path_name,size_slide, fancy_timestamps, slide_times)
	print('\nJSON successfully created.')

	return df_to_d3_norm,bb
