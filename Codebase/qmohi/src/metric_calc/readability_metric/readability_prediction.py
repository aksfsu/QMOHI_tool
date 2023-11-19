import os
import gc

from tqdm import tqdm

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from transformers import AutoTokenizer, AutoModel, AutoConfig

gc.enable()

NUM_WORKERS = 7
BATCH_SIZE = 8
MAX_LEN = 512
DROP_OUT_RATE = 0.1

MODEL_PATH = 'allenai/biomed_roberta_base'
TOKENIZER_PATH = 'allenai/biomed_roberta_base'
DEVICE = "mps" if torch.backends.mps.is_available() and torch.backends.mps.is_built() else "cpu"
# conda env config vars set PYTORCH_ENABLE_MPS_FALLBACK=1
# Ref: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#setting-environment-variables

class MyDataset(Dataset):
    def __init__(self, df, inference_only=False):
        super().__init__()

        self.df = df
        self.inference_only = inference_only
        self.text = df.sentences
        self.tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH, use_fast=False)
        if not self.inference_only:
            self.grade_level = torch.tensor(df.grade_level.values, dtype=torch.float)
        else:
            self.grade_level = None     

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        encoded = self.tokenizer.encode_plus(
            self.text.iloc[index],
            padding = 'max_length',            
            max_length = MAX_LEN,
            truncation = True,
            return_attention_mask=True,
            return_token_type_ids=True
        )

        input_ids = torch.tensor(encoded['input_ids'])
        attention_mask = torch.tensor(encoded['attention_mask'])
        token_type_ids = torch.tensor(encoded['token_type_ids'])

        if self.inference_only:
            return {
                'ids': input_ids,
                'mask': attention_mask,
                'token_type_ids': token_type_ids,
            }         
        else:
            grade_level = self.grade_level[index]
            return {
                'ids': input_ids,
                'mask': attention_mask,
                'token_type_ids': token_type_ids,
                'grade_level': grade_level
            }

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()

        config = AutoConfig.from_pretrained(MODEL_PATH)
        config.update({"output_hidden_states": True, 
                       "hidden_dropout_prob": 0.0})
                    #    "layer_norm_eps": 1e-7})
        
        self.model = AutoModel.from_pretrained(MODEL_PATH, config=config)

        self.attention = nn.Sequential(            
            nn.Linear(768, 512),
            nn.Tanh(),                       
            nn.Linear(512, 1),
            nn.Softmax(dim=1)
        )

        self.regressor = nn.Sequential(
            nn.Dropout(DROP_OUT_RATE),
            nn.Linear(768, 1)                        
        )

    # https://www.kaggle.com/code/andretugan/pre-trained-roberta-solution-in-pytorch
    def forward(self, input_ids, attention_mask, token_type_ids):
        outputs = self.model(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        # return self.regressor(outputs[1]) # Pooled output [8,768]

        # Pooling Layer (https://www.kaggle.com/code/rhtsingh/utilizing-transformer-representations-efficiently)
        # There are a total of 13 layers of hidden states.
        # 1 for the embedding layer, and 12 for the 12 Roberta layers.
        # We take the hidden states from the last Roberta layer.
        # last_layer_hidden_states = model_output.hidden_states[-1] #torch.Size([8, 512, 768])

        # The number of cells is MAX_LEN.
        # The size of the hidden state of each cell is 768 (for roberta-base).
        # In order to condense hidden states of all cells to a context vector,
        # we compute a weighted average of the hidden states of all cells.
        # We compute the weight of each cell, using the attention neural network.
        weights = self.attention(outputs.last_hidden_state) # last hidden state torch.Size([8, 512, 768])
                
        # weights.shape is BATCH_SIZE x MAX_LEN x 1
        # last_layer_hidden_states.shape is BATCH_SIZE x MAX_LEN x 768        
        # Now we compute context_vector as the weighted average.
        # context_vector.shape is BATCH_SIZE x 768
        context_vector = torch.sum(weights * outputs.last_hidden_state, dim=1)

        # Reduce the context vector to the prediction score
        return self.regressor(context_vector)

def predict(model, states_list, test_dataloader):
    model.eval()

    all_preds = []
    for state in states_list:
        print(f"State: {state}")
        state_dict = torch.load(state)
        model.load_state_dict(state_dict)
        model = model.to(DEVICE)
        
        # Clean
        del state_dict
        gc.collect()
        torch.cuda.empty_cache()
        
        preds = []
        prog = tqdm(test_dataloader, total=len(test_dataloader))
        for data in prog:
            ids = data['ids'].to(DEVICE, dtype=torch.long)
            mask = data['mask'].to(DEVICE, dtype=torch.long)
            token_type_ids = data['token_type_ids'].to(DEVICE, dtype=torch.long)

            outputs = model(input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids)
            preds.append(outputs.squeeze(-1).cpu().detach().numpy())
            
        all_preds.append(np.concatenate(preds))
        
        # Clean
        gc.collect()
        
    return all_preds

def predict_reading_level(input_df, model_path):
    df = input_df.rename(columns={'Relevant content on all pages': 'sentences'})

    predict_dataset = MyDataset(df, inference_only=True)
    predict_loader = DataLoader(predict_dataset, batch_size=BATCH_SIZE, drop_last=False, shuffle=False, num_workers=NUM_WORKERS)

    model = MyModel().to(DEVICE)
    state_list = [os.path.join(model_path, x) for x in os.listdir(model_path) if x.endswith(".pt")]

    predictions = np.array(predict(model, state_list, predict_loader))
    predictions = np.transpose(predictions).flatten()
    return np.round(predictions, 3)