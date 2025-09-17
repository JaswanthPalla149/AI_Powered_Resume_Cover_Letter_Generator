System Design Document
1. Project Overview
Project Name: AI Agent for Structured Job Information Extraction and Resume Generation

Objective:
To build an AI-powered desktop application that automates resume and cover letter generation tailored to any given job description by extracting structured job information from unstructured inputs.

Problem:
Manually tailoring resumes and cover letters for multiple job applications is time-consuming and error-prone, especially when job descriptions are unstructured free text.

Solution:
An integrated system combining:

A fine-tuned large language model that extracts structured job information (skills, responsibilities, qualifications, etc.) from unstructured job descriptions.

An AI resume and cover letter generator that personalizes content based on extracted job data plus user profile input.

A user-friendly PyQt5 desktop GUI for user data input, job application input, and managing resume generation and output.

2. Architecture Overview
text
+------------------------------+           +-----------------------------+
|     User Profile Application  |           |      Job Extractor API      |
|  (PyQt5 Desktop GUI +        +---------->+  (Flask + Fine-tuned Mistral)|
|   Resume Generation Worker)   |           |                             |
+--------------+---------------+           +--------------+--------------+
               |                                           |
       User Data JSON + Job Description                    |
               |                                           |
               +--------------------------+                |
                                          |               |
                                          v               v
                +-------------------------------------------+
                |        Gemini API (Pre-trained LLM)        |
                |  Resume and Cover Letter Content Generation|
                +-------------------------------------------+
                                          |
                                Customized Resume + Cover Letter
                                          |
                                          v
                         Saved to files (.tex, .txt) for compilation/display
3. Component Breakdown
A. UserProfileApp (PyQt5 Desktop Application)
Purpose: Graphical frontend for data entry (personal, education, experience, skills, job details).

Features:

Persistent data storage in JSON files.

Dynamic adding/removal of education, projects, leadership, experience sections.

Job information input form (title, company, description).

Controls to trigger AI resume generation workflow.

Responsibilities: Collect user/job data → save/load from disk → invoke background worker for resume generation → display progress and results.

B. ResumeGenerationWorker (QThread)
Purpose: Runs resume generation asynchronously to keep UI responsive.

Workflow:

Calls /extract endpoint on Job Extractor API to extract required skills from job description.

Prepares combined user profile + job requirements payload.

Calls Gemini API with prompt template for generating customized resume (LaTeX) and cover letter (plain text).

Saves outputs to generated_resume.tex and cover_letter.txt.

Signals UI on progress, completion, or error.

C. Job Extractor API (Flask Server)
Purpose: Host fine-tuned Mistral-7B LLM to extract structured JSON information from job descriptions.

Features:

Loads quantized and LoRA fine-tuned Mistral model on start-up.

Provides /extract GET endpoint accepting job_title, company, job_description as query params.

Generates structured JSON output with the specified schema keys using LLM prompt.

Health-check endpoint /health for monitoring.

Responsibilities: Parse input query, prompt fine-tuned model, return json extraction output.

D. Gemini API (Google’s generative AI platform)
Purpose: Generate customized resume and cover letters from structured user and job data.

Features:

Receives prompt with combined data and instruction template.

Produces LaTeX formatted resume and plain text cover letter.

Handles detailed formatting and content tailoring.

4. Data Design
User Profile Data (JSON)
Personal information (name, contact, links)

Education history (degree, institute, year)

Work experience (company, role, description)

Projects (title, description)

Skills (list)

Positions of responsibility

Achievements (list)

Job Application Data (JSON)
Job title

Company name

Full job description text

Extracted Job Info (JSON Schema)
json
{
  "Core Responsibilities": "...",
  "Required Skills": "...",
  "Educational Requirements": "...",
  "Experience Level": "...",
  "Preferred Qualifications": "...",
  "Compensation and Benefits": "..."
}
5. Chosen Technologies and Reasons
Component	Technology	Reason for Choice
Desktop GUI	PyQt5	Robust, feature-rich, supports complex form designs and threading
Background Worker	QThread	Prevents UI freezing during network/AI calls
Model Serving API	Flask	Lightweight, easy to deploy REST API server for model inference
LLM Model (Extractor)	Mistral-7B Instruct + LoRA	Small VRAM (4GB quantized), lower hallucination, good instruction following
Model Optimization	BitsAndBytes 4-bit Quant	Enables training/inference on consumer GPUs
Fine-tuning Method	PEFT LoRA	Efficient adapter-based fine-tuning reducing compute requirements
Resume Content Gen AI	Google Gemini API	Powerful pre-trained LLM for text generation and formatting
HTTP Communication	requests library	Reliable Python HTTP client for REST interaction
Environment & Config	dotenv	Secure management of API keys and config
6. Design Decisions and Trade-Offs
Modularity: Separation of job info extraction and resume generation components increases flexibility and easier updates.

Resource Efficiency: Using LoRA fine-tuning and quantization allows model deployment on consumer-grade GPUs and reduces cost.

Focused Fine-tuning: Targeted fine-tuning on structured JSON extraction improves reliability versus full fine-tuning or zero-shot models.

User Experience: Desktop application with progress UI and asynchronous processing enhances usability.

Security: API keys managed by environment variables, model served locally to avoid dependency on external compute.

This concise system design document presents a strong foundation from architectural, data, component, and technology standpoints suitable for software engineering evaluation and further development.