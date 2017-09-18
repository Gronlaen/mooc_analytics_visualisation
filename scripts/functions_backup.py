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


def compute_validity(df,row) :
	if row <= 0 :
		return 0
	else :
		if df['AccountUserID'][row] == df['AccountUserID'][row-1] :
			if (df['EventType'][row] == 'Video.Play' and df['EventType'][row-1] == 'Video.Pause'):
				if df['CurrentTime'][row] == df['CurrentTime'][row-1]:
					return 1
		return 0
	
def hist_slide_diff(df_click_views_jump,slides_number):
	fig = plt.figure(figsize=(10,5))
	df_slot_diff = df_click_views_jump.groupby(['SlotDiff']).agg({'AccountUserID' : 'count'}).reset_index()
	plt.bar(df_slot_diff['SlotDiff'], df_slot_diff['AccountUserID'], width=1)
	plt.xlim([-slides_number,slides_number])
	plt.xlabel('Slide difference');
	
def visu_slide_diff(df_click_views_jump,slides_number):
	fig = plt.figure(figsize=(10,5))
	df_slot_diff_per_source = df_click_views_jump.groupby(['oldtime_slots','SlotDiff']).agg({'TimeDiff' : 'count'}).reset_index()
	df_slot_diff_per_source.sort_values(['oldtime_slots','SlotDiff'], inplace=True)
	colors = ['orange','cyan','red','seagreen','blue','skyblue','yellow','gold','limegreen','black',
	         'brown','pink','green','tomato','chocolate','fuchsia','crimson','salmon','thistle','powderblue',
	         'snow','lightskyblue','darkred']
	for i in range(0,slides_number) :
		for j in range(-slides_number+1,slides_number) :
			if not ((df_slot_diff_per_source['oldtime_slots'] == i) & (df_slot_diff_per_source['SlotDiff'] == j)).any() :
				df_slot_diff_per_source.loc[df_slot_diff_per_source.index.max() + 1] = [i,j,0]
	df_slot_diff_per_source.sort_values(['oldtime_slots','SlotDiff'], inplace=True)
	for i in range(0,slides_number) :
		data = df_slot_diff_per_source[df_slot_diff_per_source['oldtime_slots'] == i].copy()
		total_sum = data.TimeDiff.sum()
		df_slot_diff_per_source['TimeDiff'] = df_slot_diff_per_source['TimeDiff']*1.3
		data['TimeDiff'] = data['TimeDiff']/total_sum
		plt.plot(data['SlotDiff'], data['TimeDiff'], label=i, color=random.choice(colors), alpha=1)
	plt.xlabel('Slide Difference');
	plt.legend();
	return df_slot_diff_per_source;

def scatter_slide_diff(df_slot_diff_per_source,df_click_views_jump,slides_number):
	plt.figure(figsize=(10,6))
	plt.scatter(x=df_slot_diff_per_source['SlotDiff'],y=df_slot_diff_per_source['oldtime_slots'],
				s=df_slot_diff_per_source['TimeDiff']/5, color='darkblue', label='data')
	plt.ylim([-1,slides_number])
	plt.xlabel('Slide Difference')
	plt.ylabel('Slide Number')
	
	plt.figure(figsize=(10,10))
	df_slots = df_click_views_jump.groupby(['oldtime_slots','newtime_slots']).agg({'TimeDiff' : 'count'}).reset_index()
	df_slots.sort_values(['oldtime_slots','newtime_slots'], inplace=True)
	df_slots['TimeDiff'] = df_slots['TimeDiff']*40
	plt.scatter(x=df_slots['newtime_slots'],y=df_slots['oldtime_slots'],
				s=df_slots['TimeDiff'], color='darkblue', label='data')
	plt.ylim([-1,slides_number])
	plt.xlabel('Slide Source')
	plt.ylabel('Slide Target')
	
def click_views(df_click_views_full,slide_change,interval_limit,intervals) :
	
	df_click_views = df_click_views_full[df_click_views_full['EventType'] == 'Video.Seek'].copy()

	# Depends on the platform (Coursera / EDX)

	# Coursera
	# df_click_views.drop(['DataPackageID','SessionUserID','VideoID','CurrentTime',
	#                      'SeekType','NewSpeed','EventType'], axis=1, inplace=True)

	# EDX
	df_click_views.drop(['DataPackageID','VideoID',
					 'SeekType','NewSpeed','EventType'], axis=1, inplace=True)

	df_click_views.sort_values(['AccountUserID','TimeStamp'], inplace=True)
	df_click_views = df_click_views.reset_index()
	df_click_views['time_slot'] = df_click_views.apply(lambda row : compute_time_diff(df_click_views,row.name), axis=1)

	df_click_views = df_click_views[df_click_views['time_slot'] >= interval_limit]

	df_click_views['oldtime_slots'] = pd.cut(df_click_views['OldTime'], slide_change,
											 labels=[x for x in range(0,len(slide_change)-1)])
	df_click_views['newtime_slots'] = pd.cut(df_click_views['NewTime'], slide_change,
											 labels=[x for x in range(0,len(slide_change)-1)])
	df_click_views['TimeDiff'] = df_click_views['NewTime'] - df_click_views['OldTime']
	df_click_views['SameSlot'] = df_click_views.apply(lambda row : 1 if row['oldtime_slots'] ==
													  row['newtime_slots'] else 0,axis=1)
	print("before : " , len(df_click_views))
	df_click_views = df_click_views[df_click_views['TimeDiff'].apply(lambda x : abs(x) > 10) ]
	print("after : " , len(df_click_views))

	df_click_views.to_csv('../deprecated/temp.csv')
	df_click_views = pd.read_csv('../deprecated/temp.csv')
	df_click_views.drop(['Unnamed: 0'], axis=1, inplace=True)

	df_click_views['SlotDiff'] = df_click_views['newtime_slots'] - df_click_views['oldtime_slots']

	df_click_views = df_click_views[df_click_views['TimeDiff'] != 0].copy()

	df_click_views['old_slots'] = df_click_views['oldtime_slots'].apply(lambda x : 'source ' + str(x))
	df_click_views['new_slots'] = df_click_views['newtime_slots'].apply(lambda x : 'target ' + str(x))
	
	df_click_views['source_interval_length'] = df_click_views['oldtime_slots'].apply(lambda x : intervals[x])
	df_click_views['target_interval_length'] = df_click_views['newtime_slots'].apply(lambda x : intervals[x])

	print('Percentage of jumps inside the same slot : ',
		int(len(df_click_views[df_click_views['SameSlot'] 
									 == 1])/len(df_click_views)*10000)/100, '%')
	print("total number of Seeks : ", len(df_click_views))
	print("total number of Seeks between different slides : ",len(df_click_views[df_click_views['SameSlot'] != 1]) )

	return df_click_views.sort_values(['AccountUserID','TimeStamp'])

def number_seek_user(df_click_views):
	fig = plt.figure(figsize=(10,5))
	user_dict = Counter(df_click_views['AccountUserID'].values).values()
	plt.hist(list(user_dict), bins=100);
	plt.xlabel('Number of Video.Seek per user')
	
def hist_time_diff(df_click_views):
	user_dict = df_click_views['TimeDiff'].values
	user_dict
	fig = plt.figure(figsize=(10,5))
	aa = plt.hist(list(user_dict), bins=2000);
	plt.plot((0, 0), (0, 100), 'k-', alpha=1)
	plt.xlim([-100,100]);
	print('Percentage of jumps back in time : ',
		  int(len(df_click_views[df_click_views['TimeDiff'] < 0])/len(df_click_views)*10000)/100, '%')
	print('Percentage of jumps forward in time : ',
		  int(len(df_click_views[df_click_views['TimeDiff'] > 0])/len(df_click_views)*10000)/100, '%')

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

        color = "#C0C0C0"

        flare["links"].append({"source": source, "target": target, "value" : str(value), "value_text" : str(value_text), "color" : color})

    with open('../Visualisation/data/' + path_name + '.json', 'w') as outfile:
        json.dump(flare, outfile)

    return df_grpby_target, df_grpby_source

def to_json(df_click_views,df_click_views_jump, path_name, size_slide, fancy_timestamps, slide_times):
	
	# slides_number = len(slide_times)

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
	print('to_json : Done')

	# return df_to_d3_norm, df_to_d3_clean_norm
	return df_to_d3_norm,bb

def pause_play(df_click_views_full,slide_change, max_interval, intervals):
    df_pauses = df_click_views_full[df_click_views_full['EventType'] == 'Video.Pause'].copy()
    df_plays = df_click_views_full[df_click_views_full['EventType'] == 'Video.Play'].copy()
    df_pauses_plays = pd.concat([df_pauses,df_plays])
    df_pauses_plays.drop(['DataPackageID','SessionUserID','VideoID','OldTime','NewTime',
    'SeekType','NewSpeed'], axis=1, inplace=True)
    df_pauses_plays.sort_values(['AccountUserID','TimeStamp'], inplace=True)
    df_pauses_plays = df_pauses_plays.reset_index()
    df_pauses_plays['time_slot'] = df_pauses_plays.apply(lambda row : compute_time_diff(df_pauses_plays,row.name), axis=1)
    df_pauses_plays['valid_stop'] = df_pauses_plays.apply(lambda row : compute_validity(df_pauses_plays,row.name), axis=1)
    df_pauses_plays['play_pause'] = df_pauses_plays['time_slot']*df_pauses_plays['valid_stop']
    df_pauses_plays.drop(['time_slot','valid_stop'], axis=1, inplace=True)

    df_pauses_plays['current_slot'] = pd.cut(df_pauses_plays['CurrentTime'], slide_change,
        labels=[x for x in range(0,len(slide_change)-1)])
    df_pauses_plays.to_csv('temp2.csv')
    df_pauses_plays = pd.read_csv('temp2.csv')
    df_pauses_plays.drop(['Unnamed: 0'], axis=1, inplace=True)
    df_pauses_plays = df_pauses_plays[df_pauses_plays['play_pause'] > 10]
    df_pauses_plays = df_pauses_plays[df_pauses_plays['play_pause'] < max_interval]
    
    df_unique_pausers = df_pauses_plays.groupby(['current_slot']).agg({'AccountUserID' : lambda x: x.nunique()})
    df_total_pausers = df_pauses_plays.groupby(['current_slot']).agg({'AccountUserID' : 'count'})

    df_unique_pausers.rename(columns={'AccountUserID' : 'unique_pausers'}, inplace=True)
    df_total_pausers.rename(columns={'AccountUserID' : 'total_pauses'}, inplace=True)
    
    df_final_pauses = pd.concat([df_unique_pausers,df_total_pausers], axis=1)

    df_final_pauses = df_final_pauses.reset_index()
    df_final_pauses.rename(columns={'current_slot' : 'slide'}, inplace=True)
    
    df_final_pauses['pauses_per_user'] = df_final_pauses['total_pauses']/df_final_pauses['unique_pausers']
    sum_1 = df_final_pauses['pauses_per_user'].sum()
    sum_2 = df_final_pauses['total_pauses'].sum()
    df_final_pauses['pauses_per_user_normalized'] = df_final_pauses['pauses_per_user']/sum_1
    df_final_pauses['total_pauses_normalized'] = df_final_pauses['total_pauses']/sum_2
    df_final_pauses['indexes_1'] = df_final_pauses['slide']*5
    df_final_pauses['indexes_2'] = df_final_pauses['slide']*5+2
    df_final_pauses['indexes_3'] = df_final_pauses['slide']
    df_final_pauses['time'] = df_final_pauses['indexes_3'].apply(lambda x : intervals[x])
    df_final_pauses['ratio_time'] = df_final_pauses['total_pauses']/df_final_pauses['time']
    
    labels = np.linspace(0,df_final_pauses['slide'].max(),df_final_pauses['slide'].max()+1)

    fig3 = plt.figure(figsize=(10,5))
    plt.bar(df_final_pauses['indexes_1'], df_final_pauses['pauses_per_user_normalized'], width=2, color='red', alpha=0.5, label='Normalized Pauses per User')
    plt.bar(df_final_pauses['indexes_2'], df_final_pauses['total_pauses_normalized'], width=2, color='blue', alpha=0.5, label='Normalized Total Pauses')
    plt.ylim([0,0.2])
    plt.xlim([0,df_final_pauses['indexes_2'].max()+2])
    plt.xticks(labels*5 + 2, [int(x) for x in labels])
    plt.xlabel('Slide Number')
    plt.ylabel('Ratio')

    plt.plot([0,5*df_final_pauses['slide'].max()+4], [1/(df_final_pauses['slide'].max()+1),1/(df_final_pauses['slide'].max()+1)], color='black', label='Mean')
    plt.ylim([0,max(df_final_pauses['pauses_per_user_normalized'].max(),df_final_pauses['total_pauses_normalized'].max())*1.3])

    plt.legend();

    fig4 = plt.figure(figsize=(7,5))
    plt.bar(df_final_pauses['indexes_1'], df_final_pauses['unique_pausers'], width=2, color='red', alpha=0.5, label='Number of Unique Pausers')
    plt.bar(df_final_pauses['indexes_2'], df_final_pauses['total_pauses'], width=2, color='blue', alpha=0.5, label='Total Number of  Pauses')
    plt.xlim([0,df_final_pauses['indexes_2'].max()+2])
    plt.xlabel('Slide Number')
    plt.xticks(labels*5 + 2, [int(x) for x in labels])
    plt.legend();
#     plt.savefig('pauses.png')
    
    fig5 = plt.figure(figsize=(7,5))
    plt.bar(df_final_pauses['indexes_3'], df_final_pauses['ratio_time'], width=0.8, color='blue', alpha=0.5, label='Number of Unique Pausers')
    plt.xlim([0,df_final_pauses['indexes_3'].max()+0.8])
    plt.xlabel('Slide Number')
    plt.xticks(labels+0.4, [int(x) for x in labels])
    plt.legend();
#     plt.savefig('pauses_ratio.png')


    df_final_pauses.set_index(['slide'], inplace=True)
    

    return df_final_pauses




def visu_slide_pause(df_pause_views):
	fig = plt.figure(figsize=(10,5))
	aa = df_pause_views.groupby(['current_slot','SlotDiff']).agg({'TimeDiff' : 'count'}).reset_index()
	aa.sort_values(['oldtime_slots','SlotDiff'], inplace=True)
	colors = ['orange','cyan','red','seagreen','blue','skyblue','yellow','gold','limegreen','black']
	for i in range(0,10) :
		for j in range(-9,10) :
			if not ((aa['oldtime_slots'] == i) & (aa['SlotDiff'] == j)).any() :
				aa.loc[aa.index.max() + 1] = [i,j,0]
	aa.sort_values(['oldtime_slots','SlotDiff'], inplace=True)
	for i in range(0,10) :
		data = aa[aa['oldtime_slots'] == i].copy()
		total_sum = data.TimeDiff.sum()
		aa['TimeDiff'] = aa['TimeDiff']*1.3
		data['TimeDiff'] = data['TimeDiff']/total_sum
		plt.fill_between(data['SlotDiff'], data['TimeDiff'], label=i, color=colors[i], alpha=0.3)
	plt.xlabel('Slide Difference');
	plt.legend();
	return aa;

def visu_slide_views_vs_norm(df_click_views, source):
	colu = 'oldtime_slots' if source else 'newtime_slots'
	inter = 'source_interval_length' if source else 'target_interval_length'
	df_click_source_ratio = df_click_views.groupby([colu]).agg({'time_slot':'count', inter:'first'})
	df_click_source_ratio = df_click_source_ratio.reset_index().rename(columns={'time_slot' : 'total_views', colu : 'slide'})
	df_click_source_ratio['norm_total_views'] = df_click_source_ratio['total_views']/df_click_source_ratio[inter].sum()
	df_click_source_ratio['linear_views'] = df_click_source_ratio['total_views']/df_click_source_ratio[inter]
	df_click_source_ratio['norm_linear_views'] = df_click_source_ratio['linear_views']/df_click_source_ratio['linear_views'].sum()
	df_click_source_ratio['indexes_1'] = df_click_source_ratio['slide']*5
	df_click_source_ratio['indexes_2'] = df_click_source_ratio['slide']*5+2

	labels = df_click_source_ratio['slide'].values
	fig3 = plt.figure(figsize=(10,5))
	plt.bar(df_click_source_ratio['indexes_1'], df_click_source_ratio['norm_total_views'], width=2, color='gold', alpha=0.5, label='Total Views')
	plt.bar(df_click_source_ratio['indexes_2'], df_click_source_ratio['norm_linear_views'], width=2, color='seagreen', alpha=0.5, label='Normalized Total Views')
	plt.xticks(labels*5 + 2, labels)
	plt.xlabel('Slide')
	plt.title('Slide views per {}'.format('Source' if source else 'Target'))
	plt.legend();
	return df_click_source_ratio

def visu_ratios_incoming(df_norm,df_norm_clean) :
	df_norm['value_source_norm'] = df_norm['value']/df_norm['source_interval_length']
	ratio_incoming = df_norm.groupby(['target']).agg({'value' : 'sum','target_interval_length' : 'first', 'value_source_norm':'sum'})
	ratio_incoming.reset_index(inplace=True)
	ratio_incoming['name'] = ratio_incoming['target'].apply(lambda x : x.split(' ')[1])
	ratio_incoming['name'] = pd.to_numeric(ratio_incoming['name'])
	ratio_incoming = ratio_incoming.drop('target',axis=1)
	ratio_incoming['value_target_norm'] = ratio_incoming['value']/len(ratio_incoming)
	ratio_incoming['mean'] = 1/len(ratio_incoming)
	ratio_incoming['indexes_1'] = ratio_incoming['name']*5
	ratio_incoming['indexes_2'] = ratio_incoming['name']*5+2


	ratio_incoming_clean = df_norm_clean.groupby(['target']).agg({'value' : 'sum','target_interval_length' : 'first'})
	ratio_incoming_clean.reset_index(inplace=True)
	ratio_incoming_clean['name'] = ratio_incoming_clean['target'].apply(lambda x : x.split(' ')[1])
	ratio_incoming_clean['name'] = pd.to_numeric(ratio_incoming['name'])
	ratio_incoming_clean = ratio_incoming_clean.drop('target',axis=1)
	ratio_incoming_clean['value_norm'] = ratio_incoming_clean['value']/ratio_incoming_clean['target_interval_length']
	ratio_incoming_clean['mean'] = 1/len(ratio_incoming_clean)
	ratio_incoming_clean['indexes_2'] = ratio_incoming_clean['name']*5+2

	fig4 = plt.figure(figsize=(10,5))
	labels = ratio_incoming['name'].values
	plt.bar(ratio_incoming['indexes_1'], ratio_incoming['value_target_norm'], width=2, color='red', alpha=0.3, label='Ratio of incoming seeks, for normalized targets')
	plt.bar(ratio_incoming['indexes_2'], ratio_incoming['value_source_norm'], width=2, color='blue', alpha=0.7, label='Ratio of incoming seeks, for normalized sources')
#    plt.bar(ratio_incoming_clean['indexes_2'], ratio_incoming_clean['value_norm'], width=2, color='blue', alpha=0.7, label='Ratio of incoming seeks, for normalized targets')
	plt.plot([0,5*(len(ratio_incoming))], [ratio_incoming['mean'].values[0],ratio_incoming['mean'].values[0]], color='black', label='Mean')
	plt.xticks(labels*5 + 2, labels)
	plt.ylim([0,max(ratio_incoming['value_target_norm'].max(),ratio_incoming['value_source_norm'].max())*1.3])
	plt.xlim([0,ratio_incoming_clean['indexes_2'].max()+2])
	plt.xlabel('Slide Number')
	plt.ylabel('Ratio')
	plt.legend();

	ratio_incoming.drop(['indexes_1','mean', 'indexes_2'], axis=1, inplace=True)
	ratio_incoming.rename(index=str, columns={'name': 'slide','value_norm' : 'incoming_ratio_normalized','value' : 'incoming_ratio'}, inplace=True)
	ratio_incoming.set_index(['slide'], inplace=True)


	return ratio_incoming

def slide_duration(intervals) :
	plt.figure(figsize=(10,5))
	plt.bar(list(intervals.keys()),list(intervals.values()), color='seagreen', alpha=0.8);
	plt.xticks([x + 0.4 for x in range(0,len(intervals))],range(0,len(intervals)))
	plt.xlim([0,len(intervals)])
	plt.xlabel('Slide Number')
	plt.ylabel('Time [s]')
	plt.title('Duration of Slides');


def slide_duration_color(intervals) :
	
	df_duration = pd.DataFrame.from_dict(intervals, orient='index', dtype=float)
	df_duration.columns = ['duration']
	df_duration['ratio'] = df_duration['duration']/df_duration['duration'].max()
	df_duration['color'] = df_duration['ratio'].apply(lambda x : cm.PuBu(x))
	df_duration.reset_index(inplace=True)
	df_duration.rename(index=str, columns={'index':'slide'}, inplace=True)
	
	cMap = plt.cm.get_cmap("PuBu")
	
	# Mock Figure
	a, b = (0, df_duration['duration'].max())
	iterations = 11
	Z = [[0,0],[0,0]]
	levels = np.linspace(a,b,iterations)
	CS3 = plt.contourf(Z, levels, cmap=cMap)
	plt.clf();
 
	
	plt.figure(figsize=(10,5));
	plt.bar(df_duration['slide'],df_duration['duration'], color=df_duration['color']);
	plt.xticks([x + 0.4 for x in range(0,len(intervals))],range(0,len(intervals)));
	plt.xlim([0,len(intervals)]);
	plt.xlabel('Slide Number');
	plt.ylabel('Time [s]');
	plt.title('Duration of Slides');
	cbar = plt.colorbar(CS3);

	return df_duration;
	