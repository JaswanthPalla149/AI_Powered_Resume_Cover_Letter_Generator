# AI-Powered Resume Tailoring Agent

## 📌 What is this project?
Students often struggle when applying to jobs:  
- Job descriptions are long, vague, or filled with jargon.  
- Manually customizing resumes and cover letters for every role is time-consuming.  

This project introduces an **AI agent** that simplifies the process.  
It reads job descriptions, understands the key requirements, and automatically tailors the student’s resume and cover letter to fit the role.  

---

## ⚙️ How does it work?
1. **Input**:  
   - A student’s baseline resume (with core details saved).  
   - A job description (which may be long, unclear, or complex).  

2. **Processing**:  
   - The AI agent extracts the important details from the job description.  
   - Matches these with the student’s background, skills, and experiences.  
   - Plans how the resume and cover letter should be tailored.  

3. **Output**:  
   - A **role-specific resume** (no need to manually edit for each job).  
   - A **customized cover letter** aligned with the posting.  

---

## 🔑 Under the Hood
- **Fine-Tuned Model**:  
  We fine-tuned **Mistral-7B-Instruct** with LoRA to specialize in understanding job descriptions and outputting structured data.  
  - Keeps hallucination low.  
  - Ensures consistent extraction of relevant skills, responsibilities, and qualifications.  

- **Pipeline**:  
  - A **Flask API** wraps the model with endpoints like `/extract` and `/generate`.  
  - Resume details are saved once, so the student doesn’t need to re-enter everything every time.  
  - Tailoring is automated with one click.  

---

## 🚀 User-Facing Features
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

---

## 🎯 Why this matters
This tool removes the most **tedious and stressful part of job applications** for students.  
Instead of spending hours rewriting resumes and cover letters for every role, they can:  

👉 Upload the job description → Click Generate → Get a tailored resume + cover letter instantly.  

It’s fast, reliable, and keeps the focus on what matters: **applying confidently to more opportunities.**
