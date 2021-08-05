import pandas as pd


def combine_all_results_together(reading_quantity_df, metric_df, initial_uni_list_df, output_dir):

	metric_df = metric_df.drop(columns=['Keywords matched webpages on SHC', 'Content on all pages'])
	reading_quantity_df = reading_quantity_df.drop(columns=['Num of sentences', 'Num of syllables', 'Num of words'])

	merged_result = pd.merge(reading_quantity_df, metric_df, how='inner',
							 on=['University name', 'Count of SHC webpages matching keywords'])

	merged_result.to_csv(output_dir + '/merged_results.csv')

	# Add data found column by comparing with initial university list
	final_output = pd.merge(initial_uni_list_df, merged_result, left_on=['University_name', 'University SHC URL'],
							right_on=['University name', 'University SHC URL'], how='left').drop(columns=['University name'])

	# Adding data found column for convenience
	final_output['Data found'] = [1 if x > 0 else 0 for x in final_output['Count of SHC webpages matching keywords']]

	# Store final output
	final_output.to_csv(output_dir + '/final_output.csv')
	print("- All results (intermediate and final) have been stored at location: ", output_dir)
