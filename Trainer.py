# Install required packages
!pip install -q -U transformers datasets accelerate peft bitsandbytes trl huggingface_hub torch

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import Dataset
import os

# Check GPU availability
print(f"GPU available: {torch.cuda.is_available()}")
print(f"GPU name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9 if torch.cuda.is_available() else 0} GB")


# Load your training data
def load_training_data(file_path):
    """Load the training data from text file"""
    examples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    raw_examples = content.split('\n\n')
    
    for example in raw_examples:
        if example.strip():  
            examples.append({'text': example.strip()})
    
    return examples

train_data_path = "./mistral_training_data.txt" 

training_examples = load_training_data(train_data_path)
print(f"Loaded {len(training_examples)} training examples")

dataset = Dataset.from_list(training_examples)
print(f"Dataset structure: {dataset}")

model_name = "mistralai/Mistral-7B-Instruct-v0.2"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           
    bnb_4bit_compute_dtype=torch.bfloat16, 
    bnb_4bit_use_double_quant=True,      
)

print("Loading quantized model and tokenizer...")
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    low_cpu_mem_usage=True,
)

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = prepare_model_for_kbit_training(model)

peft_config = LoraConfig(
    lora_alpha=32,          
    lora_dropout=0.05,      
    r=16,                   
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ]
)

model = get_peft_model(model, peft_config)

model.print_trainable_parameters()
training_arguments = TrainingArguments(
    output_dir="./mistral-job-extractor",
    num_train_epochs=3,
    per_device_train_batch_size=2,          
    gradient_accumulation_steps=4,          
    optim="paged_adamw_8bit",               
    save_steps=100,
    logging_steps=25,
    learning_rate=1e-4,                    
    weight_decay=0.01,
    fp16=False,                            
    bf16=False,
    max_grad_norm=0.3,
    warmup_ratio=0.05,
    group_by_length=True,
    lr_scheduler_type="cosine",
    report_to="none",
    eval_strategy="no",                     
    save_strategy="steps",                 
    dataloader_pin_memory=False,            
    remove_unused_columns=False,           
)
def formatting_func(example):
    return example["text"]

tokenizer.model_max_length = 1024

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    args=training_arguments,
    formatting_func=formatting_func,
)

print("Starting quantized training...")
trainer.train()

# Save the fine-tuned model (adapter weights only)
print("Saving model...")
trainer.model.save_pretrained("./mistral-job-extractor-final")

# Save tokenizer
tokenizer.save_pretrained("./mistral-job-extractor-final")
