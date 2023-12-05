import os
import random
import gc

from tqdm import tqdm

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader

from transformers import AutoTokenizer, AutoModel, AutoConfig
from transformers import get_cosine_schedule_with_warmup

from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

gc.enable()

SEED = 42
NUM_WORKERS = 7
NUM_FOLDS = 5
NUM_EPOCHS = 8
BATCH_SIZE = 8
MAX_LEN = 512
LR = 1e-4
DROP_OUT_RATE = 0.1

ROBERTA = 'roberta-base'
BIOBERT = 'dmis-lab/biobert-base-cased-v1.2'
SCIBERT = 'allenai/scibert_scivocab_cased'
BIOMED_ROBERTA = 'allenai/biomed_roberta_base'
CLINICAL_BERT = 'emilyalsentzer/Bio_ClinicalBERT'

MODEL_PATH = BIOMED_ROBERTA
TOKENIZER_PATH = BIOMED_ROBERTA
SAVED_MODEL_DIR = './saved_models'
DEVICE = "mps" if torch.backends.mps.is_available() and torch.backends.mps.is_built() else "cpu"
# conda env config vars set PYTORCH_ENABLE_MPS_FALLBACK=1
# Ref: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#setting-environment-variables

TRAIN_DATA_PATH = './newsela_all.csv'

if not os.path.exists(SAVED_MODEL_DIR):
    os.makedirs(SAVED_MODEL_DIR)

dataset_df = pd.read_csv(TRAIN_DATA_PATH)
train_df, test_df = train_test_split(dataset_df, test_size=0.2, random_state=42, shuffle=False)

# Remove incomplete entries if any.
# train_df.drop(train_df[(train_df.target == 0) & (train_df.standard_error == 0)].index, inplace=True)
# train_df.reset_index(drop=True, inplace=True)

def set_random_seed(random_seed):
    random.seed(random_seed)
    np.random.seed(random_seed)
    os.environ["PYTHONHASHSEED"] = str(random_seed)
    torch.manual_seed(random_seed)

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
        

class Trainer:
    def __init__(self, model, optimizer, scheduler, train_dataloader, valid_dataloader):
        self.model = model
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.train_data = train_dataloader
        self.valid_data = valid_dataloader

    def yield_loss(self, outputs, targets):
        return torch.sqrt(nn.MSELoss()(outputs, targets))

    def train_one_epoch(self):
        self.model.train()

        prog_bar = tqdm(self.train_data, total=len(self.train_data))
        for inputs in prog_bar:
            ids = inputs['ids'].to(DEVICE, dtype=torch.long)
            mask = inputs['mask'].to(DEVICE, dtype=torch.long)
            token_type_ids = inputs['token_type_ids'].to(DEVICE, dtype=torch.long)
            grade_level = inputs['grade_level'].to(DEVICE, dtype=torch.float)

            self.optimizer.zero_grad()
            
            outputs = self.model(input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids).view(-1)

            loss = self.yield_loss(outputs, grade_level)
            loss.backward()
            prog_bar.set_description('loss: {:.2f}'.format(loss.item()))

            self.optimizer.step()
            self.scheduler.step()

    def valid_one_epoch(self):
        self.model.eval()
        all_targets = []
        all_predictions = []
        with torch.no_grad():
            prog_bar = tqdm(self.valid_data, total=len(self.valid_data))
            for inputs in prog_bar:
                ids = inputs['ids'].to(DEVICE, dtype=torch.long)
                mask = inputs['mask'].to(DEVICE, dtype=torch.long)
                token_type_ids = inputs['token_type_ids'].to(DEVICE, dtype=torch.long)
                targets = inputs['grade_level'].to(DEVICE, dtype=torch.float)

                outputs = self.model(input_ids=ids, attention_mask=mask, token_type_ids=token_type_ids).view(-1)
                all_targets.extend(targets.cpu().detach().numpy().tolist())
                all_predictions.extend(outputs.cpu().detach().numpy().tolist())

        rmse_loss = np.sqrt(mean_squared_error(all_targets, all_predictions))
        print('Validation RMSE: {:.2f}'.format(rmse_loss))
        
        return rmse_loss
    
    def get_model(self):
        return self.model

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

def kfold_cross_validation():
    model = MyModel().to(DEVICE)
    optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=1e-2)                

    kfold = StratifiedKFold(n_splits=NUM_FOLDS, random_state=SEED, shuffle=True)

    for fold, (train_indices, valid_indices) in enumerate(kfold.split(train_df['sentences'], train_df['grade_level'])):    
        print(f"\nFold {fold + 1}/{NUM_FOLDS}")

        set_random_seed(SEED + fold)

        train_dataset = MyDataset(train_df.loc[train_indices])    
        valid_dataset = MyDataset(train_df.loc[valid_indices])    
            
        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, drop_last=True, shuffle=True, num_workers=NUM_WORKERS)    
        valid_loader = DataLoader(valid_dataset, batch_size=BATCH_SIZE, drop_last=False, shuffle=False, num_workers=NUM_WORKERS)    

        scheduler = get_cosine_schedule_with_warmup(optimizer, num_training_steps=NUM_EPOCHS * len(train_loader), num_warmup_steps=50)    
        trainer = Trainer(model, optimizer, scheduler, train_loader, valid_loader)

        best_loss = np.inf
        for epoch in range(NUM_EPOCHS):
            print(f"--- Epoch {epoch} ---")

            trainer.train_one_epoch()
            current_loss = trainer.valid_one_epoch()

            if current_loss < best_loss:
                print(f"Saving best model in this fold: {current_loss:.4f}")
                torch.save(trainer.get_model().state_dict(), os.path.join(SAVED_MODEL_DIR, f"fold_{fold + 1}.pt"))
                best_loss = current_loss

        print(f"Best RMSE in fold: {fold} was: {best_loss:.4f}")
        print(f"Final RMSE in fold: {fold} was: {current_loss:.4f}")

def train_model():
    model = MyModel().to(DEVICE)
    optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=1e-2)                

    set_random_seed(SEED)

    train_dataset = MyDataset(dataset_df)
        
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, drop_last=True, shuffle=True, num_workers=NUM_WORKERS)    

    scheduler = get_cosine_schedule_with_warmup(optimizer, num_training_steps=NUM_EPOCHS * len(train_loader), num_warmup_steps=50)    
    trainer = Trainer(model, optimizer, scheduler, train_loader, None)

    for epoch in range(NUM_EPOCHS):
        print(f"--- Epoch {epoch} ---")
        trainer.train_one_epoch()

    torch.save(trainer.get_model().state_dict(), os.path.join(SAVED_MODEL_DIR, f"final.pt"))

def score_model(test_list, predict_list):
    mse = mean_squared_error(test_list, predict_list)
    print(f"MSE={mse}")
    rmse = mean_squared_error(test_list, predict_list, squared=False)
    print(f"RMSE={rmse}")
    mae = mean_absolute_error(test_list, predict_list)
    print(f"MAE={mae}")
    r2 = r2_score(test_list, predict_list, force_finite=False)
    print(f"R2={r2}")

def test_model():
    test_dataset = MyDataset(test_df, inference_only=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, drop_last=False, shuffle=False, num_workers=NUM_WORKERS)

    model = MyModel().to(DEVICE)
    state_list = [os.path.join(SAVED_MODEL_DIR, x) for x in os.listdir(SAVED_MODEL_DIR) if x.endswith(".pt")]

    predictions = np.array(predict(model, state_list, test_loader))
    predictions = np.transpose(predictions).flatten()

    # Scoring
    score_model(test_df['grade_level'].tolist(), predictions)

    test_df['prediction'] = predictions
    test_df.to_csv("prediction.csv", index=False)

def train_test_model():
    train_model()
    test_model()

def QMOHItest():    
    qmohi_result_df = pd.read_csv('Reading_level_of_content.csv')
    qmohi_result_df.rename(columns={'Relevant content on all pages': 'sentences'}, inplace=True)

    test_dataset = MyDataset(qmohi_result_df, inference_only=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, drop_last=False, shuffle=False, num_workers=NUM_WORKERS)

    model = MyModel().to(DEVICE)
    state_list = [os.path.join(SAVED_MODEL_DIR, x) for x in os.listdir(SAVED_MODEL_DIR) if x.endswith(".pt")]

    predictions = np.array(predict(model, state_list, test_loader))
    predictions = np.transpose(predictions).flatten()

    # Scoring
    # score_model(qmohi_result_df['grade_level'].tolist(), predictions)

    qmohi_result_df['prediction'] = predictions
    qmohi_result_df.to_csv("QMOHI_prediction.csv", index=False)

if __name__ ==  '__main__':
    # kfold_cross_validation()
    # train_test_model()
    QMOHItest()