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


def minutes_displayed(sec) :
	sign = '-' if (int(sec) < 0) else ''
	return sign + str(int(np.round(abs(int(sec))/60))) + '\''
	
def hist_slide_diff(df_click_views_jump,slides_number):
	fig = plt.figure(figsize=(10,5))
	df_slot_diff = df_click_views_jump.groupby(['SlotDiff']).agg({'AccountUserID' : 'count'}).reset_index()
	plt.bar(df_slot_diff['SlotDiff'], df_slot_diff['AccountUserID'], width=0.8, color='red', alpha=0.5, label='ma bite')
	plt.xlim([-slides_number,slides_number])
	plt.xlabel('Slide difference');
	plt.ylabel('Number of Seeks')
	
def visu_slide_diff(df_click_views_jump,slides_number):
	# fig = plt.figure(figsize=(10,5))
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
	# 	plt.plot(data['SlotDiff'], data['TimeDiff'], label=i, color=random.choice(colors), alpha=1)
	# plt.xlabel('Slide Difference');
	# plt.legend();
	# plt.ylabel('Ratio (normalized)')
	return df_slot_diff_per_source;

def scatter_slide_diff(df_slot_diff_per_source,df_click_views_jump,slides_number):
	plt.figure(figsize=(10,5))
	plt.scatter(x=df_slot_diff_per_source['SlotDiff'],y=df_slot_diff_per_source['oldtime_slots'],
				s=df_slot_diff_per_source['TimeDiff']/3, color='darkblue', label='data')
	plt.ylim([-1,slides_number])
	plt.xlabel('Slide Difference')
	plt.ylabel('Slide Number')
	
	# plt.figure(figsize=(10,10))
	# df_slots = df_click_views_jump.groupby(['oldtime_slots','newtime_slots']).agg({'TimeDiff' : 'count'}).reset_index()
	# df_slots.sort_values(['oldtime_slots','newtime_slots'], inplace=True)
	# df_slots['TimeDiff'] = df_slots['TimeDiff']*40
	# plt.scatter(x=df_slots['newtime_slots'],y=df_slots['oldtime_slots'],
	# 			s=df_slots['TimeDiff'], color='darkblue', label='data')
	# plt.ylim([-1,slides_number])
	# plt.xlabel('Slide Source')
	# plt.ylabel('Slide Target')
	
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

def number_seek_user(df_click_views):
	fig = plt.figure(figsize=(10,5))
	user_dict = Counter(df_click_views['AccountUserID'].values).values()
	plt.hist(list(user_dict), bins=100);
	plt.xlabel('Number of Video.Seek per user')
	
def hist_time_diff(df_click_views):
	df_hist_time_diff = df_click_views.copy()

	begin_temp = df_hist_time_diff['TimeDiff'].min()
	end_temp = df_hist_time_diff['TimeDiff'].max()
	end = end_temp + 10 - (end_temp%10) if (end_temp%10 != 0) else end_temp
	begin = begin_temp - 10 + ((-begin_temp)%10) if (begin_temp%10 != 0) else begin_temp

	time_cuts = [x for x in range(int(begin),int(end)+10,10)]
	ticks = [x for x in range(math.floor(begin_temp/60)*60, math.ceil(end_temp/60)*60+1, 60)]
	ticks_labels = [minutes_displayed(x) for x in ticks]

	df_hist_time_diff['time_diff_slots'] = pd.cut(df_hist_time_diff['TimeDiff'], time_cuts,
	                                         labels=[x + 5 for x in time_cuts[:-1]])
	df_time_diff = df_hist_time_diff.groupby(['time_diff_slots']).agg({'AccountUserID' : 'count'}).reset_index()

	fig = plt.figure(figsize=(10,5))
	plt.bar(df_time_diff['time_diff_slots'], df_time_diff['AccountUserID'], width=8, color='red', alpha=0.5)
	max_height = np.round(df_time_diff['AccountUserID'].max()*1.4)
	plt.plot((0, 0), (0, max_height), 'k-', alpha=1)
	plt.ylim(0,max_height)
	plt.xlabel('Time Difference')
	plt.ylabel('Number of Seeks')
	plt.xticks(ticks, ticks_labels);



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
    df_pauses_plays.to_csv('../deprecated/temp2.csv')
    df_pauses_plays = pd.read_csv('../deprecated/temp2.csv')
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

    # fig3 = plt.figure(figsize=(10,5))
    # plt.bar(df_final_pauses['indexes_1']+1, df_final_pauses['pauses_per_user_normalized'], width=2, color='red', alpha=0.5, label='Normalized Pauses per User')
    # plt.bar(df_final_pauses['indexes_2']+1, df_final_pauses['total_pauses_normalized'], width=2, color='blue', alpha=0.5, label='Normalized Total Pauses')
    # plt.ylim([0,0.2])
    # plt.xlim([0,df_final_pauses['indexes_2'].max()+2])
    # plt.xticks(labels*5 + 2, [int(x) for x in labels])
    # plt.xlabel('Slide Number')
    # plt.ylabel('Ratio')

    # plt.plot([0,5*df_final_pauses['slide'].max()+4], [1/(df_final_pauses['slide'].max()+1),1/(df_final_pauses['slide'].max()+1)], color='black', label='Mean')
    # plt.ylim([0,max(df_final_pauses['pauses_per_user_normalized'].max(),df_final_pauses['total_pauses_normalized'].max())*1.3])

    # plt.legend();

    fig4 = plt.figure(figsize=(10,5))
    plt.bar(df_final_pauses['indexes_1']+1, df_final_pauses['unique_pausers'], width=2, color='red', alpha=0.5, label='Number of Unique Pausers')
    plt.bar(df_final_pauses['indexes_2']+1, df_final_pauses['total_pauses'], width=2, color='blue', alpha=0.5, label='Total Number of  Pauses')
    plt.xlim([0,df_final_pauses['indexes_2'].max()+2])
    plt.xlabel('Slide Number')
    plt.ylabel('Number of Pauses')
    plt.xticks(labels*5 + 2, [int(x) for x in labels])
    plt.legend();
#     plt.savefig('pauses.png')

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

def slide_duration_color(intervals) :

	fig6 = plt.figure(figsize=(12.5,5));
	
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
 
	
	
	plt.bar(df_duration['slide']+0.4,df_duration['duration'], color=df_duration['color']);
	plt.xticks([x + 0.4 for x in range(0,len(intervals))],range(0,len(intervals)));
	plt.xlim([0,len(intervals)]);
	plt.xlabel('Slide Number');
	plt.ylabel('Duration [s]');
	plt.title('Duration of Slides');
	cbar = plt.colorbar(CS3);

def seeks_out_in(df_norm) :
    df_seeks_source = df_norm.groupby(['source']).agg({'value' : 'sum'})
    df_seeks_source = df_seeks_source.reset_index()
    df_seeks_source['indexes'] = df_seeks_source['source'].apply(lambda x : int(x.split(" ")[1]))
    df_seeks_source['indexes_1'] = df_seeks_source['indexes']*5
    df_seeks_source

    df_seeks_target = df_norm.groupby(['target']).agg({'value' : 'sum'})
    df_seeks_target = df_seeks_target.reset_index()
    df_seeks_target['indexes'] = df_seeks_target['target'].apply(lambda x : int(x.split(" ")[1]))
    df_seeks_target['indexes_1'] = df_seeks_target['indexes']*5+2
    df_seeks_target['normalize'] = df_seeks_target['value']/df_seeks_target.value.sum()
    df_seeks_target

    labels = np.linspace(0,df_seeks_source['indexes'].max(),df_seeks_source['indexes'].max()+1)

    fig4 = plt.figure(figsize=(10,5))
    plt.bar(df_seeks_source['indexes_1']+1, df_seeks_source['value'], width=2, color='red', alpha=0.5, label='Number of Outgoing Seeks')
    plt.bar(df_seeks_target['indexes_1']+1, df_seeks_target['value'], width=2, color='blue', alpha=0.5, label='Number of Incoming Seeks')
    plt.xlim([0,df_seeks_target['indexes_1'].max()+2])
    plt.xlabel('Slide Number')
    plt.xticks(labels*5 + 2, [int(x) for x in labels])

    plt.legend();
    # plt.savefig('seeks.png')

    return df_seeks_target
    
def comparison(df_final_pauses,df_seeks_target):

    labels = np.linspace(0,df_seeks_target['indexes'].max(),df_seeks_target['indexes'].max()+1)

    fig5 = plt.figure(figsize=(10,5))
    plt.bar(df_final_pauses['indexes_1']+1, df_final_pauses['total_pauses_normalized'], width=2, color='red', alpha=0.5, label='Total Number of Pauses (normalized)')
    plt.bar(df_seeks_target['indexes_1']+1, df_seeks_target['normalize'], width=2, color='blue', alpha=0.5, label='Number of Incoming Seeks (normalized)')
    plt.xlim([0,df_seeks_target['indexes_1'].max()+2])
    plt.xlabel('Slide Number')
    plt.xticks(labels*5 + 2, [int(x) for x in labels])

    plt.legend();
    # plt.savefig('comparison.png')
	