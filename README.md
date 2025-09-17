# AI-Powered Resume Tailoring Agent

## What is this project?
Students often struggle when applying to jobs:  
- Job descriptions are long, vague, or filled with jargon.  
- Manually customizing resumes and cover letters for every role is time-consuming.  

This project introduces an **AI agent** that simplifies the process.  
It reads job descriptions, understands the key requirements, and automatically tailors the student’s resume and cover letter to fit the role.  

---
## The Reports for SDE Role and Data Science Role are in [SDE-Doc](https://github.com/JaswanthPalla149/AI_Powered_Resume_Cover_Letter_Generator/blob/main/SDE.md), [DataScience-Doc](https://github.com/JaswanthPalla149/AI_Powered_Resume_Cover_Letter_Generator/blob/main/DataScience.md) respectively
## Demo vedio avaialable - [IBY-Demo.mp4](https://github.com/JaswanthPalla149/AI_Powered_Resume_Cover_Letter_Generator/blob/main/IBY-Demo.mp4)
---
## How does it work?
1. **Input**:  
   - A student’s baseline resume (with core details saved).  
   - A job description (which may be long, unclear, or complex, or just too small).  

2. **Processing**:  
   - The AI agent extracts the important details from the job description.
   - Gets the output from Flask server in the form of json:
```
{
  "Core Responsibilities": "N/A",
  "Required Skills": ["SQL", "Python", "Data visualization tools (Tableau or PowerBI)"],
  "Educational Requirements": ["Bachelor's degree"],
  "Experience Level": "2+ years",
  "Preferred Qualifications": "N/A",
  "Compensation and Benefits": {
    "Compensation": "$60,000 - $80,000 per year",
    "Benefits": "N/A"
  }
}
```  
   - Matches these with the student’s background, skills, and experiences.
   - Keeps only 3 of the most suited projects and position of responsibilities, best 2 of the experiences.  
   - Plans how the resume and cover letter should be tailored.  

3. **Output**:  
   - A **role-specific resume** (no need to manually edit for each job).  
   - A **customized cover letter** aligned with the posting.  
<img width="797" height="720" alt="Screenshot 2025-09-17 105851" src="https://github.com/user-attachments/assets/eda54789-04e5-4844-a97b-e697636ec6be" />

---

## Under the Hood
- **Fine-Tuned Model**:  
  We fine-tuned **Mistral-7B-Instruct** with LoRA to specialize in understanding job descriptions and outputting structured data.  
  - Keeps hallucination low.  
  - Ensures consistent extraction of relevant skills, responsibilities, and qualifications.  

- **Pipeline**:  
  - A **Flask API** wraps the model with endpoints like `/extract` and `/generate`.
    <img width="1302" height="364" alt="Screenshot 2025-09-16 205446" src="https://github.com/user-attachments/assets/6d9b1be6-c20b-4cc7-ac01-9bc5a6064cad" />
  - Resume details are saved once, so the student doesn’t need to re-enter everything every time.  
  - Tailoring is automated with one click. Gemini API is called for this task.
    <img width="983" height="868" alt="Screenshot 2025-09-16 205034" src="https://github.com/user-attachments/assets/add6bcea-2b84-4318-bccb-d73f13e76ea6" />
    <img width="993" height="870" alt="Screenshot 2025-09-16 205059" src="https://github.com/user-attachments/assets/66beff35-ebcf-4e67-893b-b8f9761f78b8" />

---

## User-Facing Features
- **Resume Reset & Reuse**  
  Store a baseline resume once → reuse it across all applications.  

- **One-Click Resume Tailoring**  
  Automatically generate a job-specific version of your resume.  

- **Cover Letter Automation**  
  The system writes a draft personalized to the role.  

- **Clarity from Complexity**  
  Long or unclear job descriptions are distilled into actionable insights that directly shape the application.  

- **Consistency**  
  All outputs follow a clean, structured style, reducing the risk of errors or mismatches.  
<img width="991" height="881" alt="Screenshot 2025-09-16 201307" src="https://github.com/user-attachments/assets/7af08f24-6f26-48dc-959f-38b88247353a" />

---

## Why this matters
This tool removes the most **tedious and stressful part of job applications** for students.  
Instead of spending hours rewriting resumes and cover letters for every role, they can:  

Upload the job description → Click Generate → Get a tailored resume + cover letter instantly.  

It’s fast, reliable, and keeps the focus on what matters: **applying confidently to more opportunities.**
