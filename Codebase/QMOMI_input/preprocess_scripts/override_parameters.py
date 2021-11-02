import pandas as pd
import os

def override_input_file_parameters(test_data, apikeys, cseid, opdir, idealdoc, vec_model):
    for i,val in enumerate(apikeys):
        test_data['API_keys'][i] = val
    test_data['CSE_id'][0] = cseid
    if opdir : test_data['Output_directory'][0] = os.path.abspath(opdir) 
    if idealdoc : test_data['Ideal_document'][0] = os.path.abspath(idealdoc) 
    if vec_model : test_data['Word_vector_model'][0] = os.path.abspath(vec_model)
    return test_data