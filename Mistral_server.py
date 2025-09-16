from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline
from peft import PeftModel
import torch
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables to store the model and tokenizer
generator = None

def load_model():
    """Load the model and tokenizer once when the server starts"""
    global generator
    
    base_model_path = "./Mistral-7B-Instruct-v0.2"
    lora_model_path = "./mistral-job-extractor/checkpoint-200"
    
    try:
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        tokenizer.pad_token = tokenizer.eos_token
        
        # Quantization configuration
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        # Load base model with quantization
        logger.info("Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Load adapter weights
        logger.info("Loading adapter weights...")
        model = PeftModel.from_pretrained(base_model, lora_model_path)
        
        # Merge adapter with base model
        logger.info("Merging adapter with base model...")
        model = model.merge_and_unload()
        
        # Create pipeline
        logger.info("Creating pipeline...")
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.2,
        )
        
        logger.info("Model loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise e

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": generator is not None
    })

@app.route('/extract', methods=['GET'])
def extract_job_info():
    """Extract job information from job description"""
    try:
        # Check if model is loaded
        if generator is None:
            return jsonify({
                "error": "Model not loaded. Please wait for the server to initialize."
            }), 503
        
        # Get parameters from query string
        job_title = request.args.get('job_title', '')
        company = request.args.get('company', '')
        job_description = request.args.get('job_description', '')
        
        # Validate input
        if not job_description.strip():
            return jsonify({
                "error": "job_description parameter is required"
            }), 400
        
        # Create the prompt
        prompt = f"""### Instruction:
Extract the following information from the job description in a structured JSON format.
The JSON should have exactly these keys: "Core Responsibilities", "Required Skills", "Educational Requirements", "Experience Level", "Preferred Qualifications", "Compensation and Benefits".
If information for a key is not present, use "N/A".

Job Title: {job_title}
Company: {company}
Job Description:
{job_description}
"""
        
        logger.info("Processing job extraction request...")
        
        # Generate response
        response = generator(prompt)[0]["generated_text"]
        
        logger.info("Job extraction completed successfully")
        
        return jsonify({
            "success": True,
            "prompt": prompt,
            "response": response,
            "job_title": job_title,
            "company": company
        })
        
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}")
        return jsonify({
            "error": f"An error occurred during extraction: {str(e)}"
        }), 500



@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage instructions"""
    return jsonify({
        "message": "Job Information Extractor API"
    })

if __name__ == '__main__':
    logger.info("Starting Job Extractor Server...")
    
    # Load model before starting the server
    try:
        load_model()
    except Exception as e:
        logger.error("Failed to load model. Server will start but /extract endpoint will not work.")
    
    logger.info("Starting Flask server on localhost:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)