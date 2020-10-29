import pandas as pd


def combine_all_results_together(reading_quantity_df, metric_df, initial_uni_list_df, output_dir):

	# merged_result = pd.merge(reading_quantity_df, metric_df, on='University name', how='inner')

	# merged_result = pd.merge(reading_quantity_df, metric_df, how='inner',
	# 						 left_on=['University name', 'Count of keywords matching webpages on SHC',
	# 								  'Keywords matched webpages on SHC'],
	# 						 right_on=['University name', 'Count of keywords matching webpages on SHC',
	# 								   'Keywords matched webpages on SHC']).drop(columns=['Content on all pages'])
	# drop(columns=['Unnamed: 0', 'University name', 'institutionname'])

	metric_df = metric_df.drop(columns=['Keywords matched webpages on SHC', 'Content on all pages'])
	reading_quantity_df = reading_quantity_df.drop(columns=['Num of sentences', 'Num of syllables', 'Num of words'])

	merged_result = pd.merge(reading_quantity_df, metric_df, how='inner',
							 on=['University name','Count of keywords matching webpages on SHC'])


	print("\nprinting columns in merged dataframe\n")
	for col in merged_result.columns:
		print(col)

	# merged_result = merged_result.loc[:, ~merged_result.columns.duplicated()]	### to remove duplicate columns

	print("\nAfter removing duplicate columns in merged dataframe\n")
	for col in merged_result.columns:
		print(col)

	merged_result.to_csv(output_dir + '/merged_results.csv')

	##add data found column by comparing with initial university list

	final_output =  pd.merge(initial_uni_list_df, merged_result, left_on=['University_name', 'University SHC URL'],
							 right_on=['University name', 'University SHC URL'], how='left').drop(columns=['University name'])

	# adding data found column for convenience
	final_output['Data found'] = [1 if x > 0 else 0 for x in
								   final_output['Count of keywords matching webpages on SHC']]

	final_output.to_csv(output_dir + '/final_output.csv')
	return final_output


# reading_quantity_df= pd.read_csv("/Users/tejasvibelsare/Desktop/condom/Output 2020-07-15 15:30:34/Keywords_count_for_universities.csv")
# metric_df= pd.read_csv("/Users/tejasvibelsare/Desktop/condom/Output 2020-07-15 15:30:34/measures_result.csv")
# initial_uni_list_df= pd.read_csv("/Users/tejasvibelsare/Desktop/condom/Output 2020-07-15 15:30:34/University_SHC.csv")
# output_dir= "/Users/tejasvibelsare/Desktop/condom/Output 2020-07-15 15:30:34/"
#
# combine_all_results_together(reading_quantity_df, metric_df, initial_uni_list_df, output_dir)