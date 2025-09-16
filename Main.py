import sys
import json
import os
import requests

from collections import defaultdict
from google import genai
from google.genai import types
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea, 
                             QGroupBox, QMessageBox, QComboBox, QFrame, QSizePolicy, QGridLayout,
                             QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Configuration
FASTAPI_SERVER_URL = "http://127.0.0.1:5000"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')# Replace with your actual API key

class ResumeGenerationWorker(QThread):
    """Worker thread for handling resume generation to avoid UI freezing"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_data, job_data, prompt_template):
        super().__init__()
        self.user_data = user_data
        self.job_data = job_data
        self.prompt_template = prompt_template

    def run(self):
        try:
            self.progress_updated.emit(10)
            self.status_updated.emit("Getting required skills from FastAPI server...")
            
            # Step 1: Get required skills from FastAPI server
            required_skills = self.get_required_skills()
            
            self.progress_updated.emit(30)
            self.status_updated.emit("Preparing data for Gemini API...")
            
            # Step 2: Prepare data for Gemini API
            job_requirements = {
            "job_title": self.job_data.get('job_title', ''),
            "company": self.job_data.get('company', ''),
            "required_skills": required_skills   # merging inside job_requirements
            }

            combined_data = {
                "user_profile": self.user_data,
                "job_requirements": job_requirements
            }
            
            self.progress_updated.emit(50)
            self.status_updated.emit("Generating resume with Gemini AI...")
            
            # Step 3: Generate resume using Gemini API
            resume_content = self.generate_resume_with_gemini(combined_data)
            
            self.progress_updated.emit(80)
            self.status_updated.emit("Saving generated resume...")
            
            # Step 4: Save the generated resume
            self.save_resume_and_cover_letter(resume_content)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Resume generated successfully!")
            self.finished.emit(resume_content)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

    def get_required_skills(self):
        """Get required skills from Flask server using GET method"""
        try:
            job_title = self.job_data.get('job_title', '')
            company = self.job_data.get('company', '')
            job_description = self.job_data.get('description', '')
            
            # Use GET method with query parameters for Flask server
            params = {
                'job_title': job_title,
                'company': company,
                'job_description': job_description
            }
            
            response = requests.get(f"{FASTAPI_SERVER_URL}/extract", params=params)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the response from the Flask server
            if result.get("success") and "response" in result:
                return result["response"]
            else:
                return "Skills extraction failed"
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Flask server error: {str(e)}")

    def save_resume_and_cover_letter(self, output: str):
        end_doc_str = r"\end{document}"
        end_pos = output.find(end_doc_str)
    
        if end_pos == -1:
            raise ValueError("Output format is incorrect. Expected '\\end{document}' in LaTeX resume.")
    
        # Include the end of document string in LaTeX part
        latex_part = output[:end_pos + len(end_doc_str)].strip()
        cover_letter = output[end_pos + len(end_doc_str):].strip()
    
        # Clean up LaTeX part if needed (remove possible `````` wrappers)
        latex_part = latex_part.strip("``````").strip()
    
        # Clean cover letter, e.g. remove **Cover Letter** header if present
        cover_letter = cover_letter.replace("**Cover Letter**", "").strip()
    
        #Save LaTeX resume
        with open("generated_resume.tex", "w", encoding="utf-8") as f:
            f.write(latex_part)
    
        # Save Cover Letter
        with open("cover_letter.txt", "w", encoding="utf-8") as f:
            f.write(cover_letter)
    
        print("✅ Resume saved as resume.tex")
        print("✅ Cover letter saved as cover_letter.txt")

    
    def generate_resume_with_gemini(self, data):
        """Generate resume using Gemini API"""
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Load prompt template
            prompt = self.load_prompt_template()
            
            # Format prompt with data
            formatted_prompt = (
                prompt.replace("<<USER_PROFILE>>", json.dumps(data["user_profile"], indent=2))
                      .replace("<<JOB_REQUIREMENTS>>", json.dumps(data["job_requirements"], indent=2))
            )
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=formatted_prompt)],
                )
            ]

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
            )

            return response.text
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def load_prompt_template(self):
        """Load prompt template from file"""
        try:
            with open("prompt_template.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback prompt if file doesn't exist
            return self.get_default_prompt()

    def get_default_prompt(self):
        """Default prompt template"""
        return """You are an AI assistant that edits LaTeX resumes and writes cover letters.

Given details:

User Profile (JSON):
{user_profile}

Job Requirements:
{job_requirements}

Required Skills (from AI analysis):
{required_skills}

Instructions:
- Update the given LaTeX resume template with the user details.
- Select **at most 2 best experiences** most relevant to the job.
- Select **at most 3 projects** most related to the job.
- Insert **skills** that match or are relevant to the job requirements.
- Select **at most 3 positions of responsibility**.
- Select **at most 2 achievements**.
- Preserve the LaTeX formatting.
- Output only valid .tex code, no explanations.

After the updated resume:
- Generate a cover letter (plain text, not LaTeX) tailored for the given job description.

Use the base resume template provided in the system and customize it with the user's information."""

    def save_resume(self, content):
        """Save the generated resume to file"""
        try:
            with open("generated_resume.tex", "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to save resume: {str(e)}")

class UserProfileApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_data_file = "user_profile.json"
        self.initUI()
        self.load_user_data()
        
    def initUI(self):
        self.setWindowTitle('📄 Professional Resume Builder with AI')
        self.setGeometry(100, 100, 1000, 850)
        
        # Set application font
        font = QFont("Segoe UI", 9)
        self.setFont(font)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_label = QLabel("Professional Resume Builder with AI")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(header_label)
        
        # Create scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
        """)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Personal Information Section
        personal_group = self.create_section("👤 Personal Information")
        personal_layout = QGridLayout()
        personal_layout.setSpacing(10)
        
        self.personal_fields = {}
        fields = [
            ("name", "Full Name", 0, 0, 1, 2),
            ("course", "Course/Program", 1, 0, 1, 1),
            ("roll", "Roll Number", 1, 1, 1, 1),
            ("phone", "Phone Number", 2, 0, 1, 1),
            ("email", "Email Address", 2, 1, 1, 1),
            ("linkedin", "LinkedIn Profile", 3, 0, 1, 1),
            ("github", "GitHub Profile", 3, 1, 1, 1)
        ]
        
        for field_id, label_text, row, col, rowspan, colspan in fields:
            label = QLabel(label_text + ":")
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter your {label_text.lower()}")
            
            personal_layout.addWidget(label, row*2, col*2, 1, 1)
            personal_layout.addWidget(input_field, row*2+1, col*2, 1, colspan*2)
            self.personal_fields[field_id] = input_field
        
        personal_group.setLayout(personal_layout)
        scroll_layout.addWidget(personal_group)
        
        # Education Section
        self.education_group = self.create_section("🎓 Education")
        self.education_layout = QVBoxLayout(self.education_group)
        self.add_education_button = self.create_add_button("Add Education Entry", "🎓")
        self.add_education_button.clicked.connect(self.add_education_entry)
        self.education_layout.addWidget(self.add_education_button)
        scroll_layout.addWidget(self.education_group)
        
        # Experience Section
        self.experience_group = self.create_section("💼 Work Experience")
        self.experience_layout = QVBoxLayout(self.experience_group)
        self.add_experience_button = self.create_add_button("Add Work Experience", "💼")
        self.add_experience_button.clicked.connect(self.add_experience_entry)
        self.experience_layout.addWidget(self.add_experience_button)
        scroll_layout.addWidget(self.experience_group)
        
        # Projects Section
        self.projects_group = self.create_section("🚀 Projects")
        self.projects_layout = QVBoxLayout(self.projects_group)
        self.add_project_button = self.create_add_button("Add Project", "🚀")
        self.add_project_button.clicked.connect(self.add_project_entry)
        self.projects_layout.addWidget(self.add_project_button)
        scroll_layout.addWidget(self.projects_group)
        
        # Skills Section
        skills_group = self.create_section("⚡ Skills")
        skills_layout = QVBoxLayout(skills_group)
        skills_label = QLabel("Enter your skills (separated by commas):")
        skills_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.skills_input = QLineEdit()
        self.skills_input.setPlaceholderText("e.g. Python, JavaScript, Machine Learning, Data Analysis")
        skills_layout.addWidget(skills_label)
        skills_layout.addWidget(self.skills_input)
        scroll_layout.addWidget(skills_group)
        
        # Positions of Responsibility Section
        self.por_group = self.create_section("🏆 Leadership & Positions of Responsibility")
        self.por_layout = QVBoxLayout(self.por_group)
        self.add_por_button = self.create_add_button("Add Leadership Position", "🏆")
        self.add_por_button.clicked.connect(self.add_por_entry)
        self.por_layout.addWidget(self.add_por_button)
        scroll_layout.addWidget(self.por_group)
        
        # Achievements Section
        achievements_group = self.create_section("🌟 Achievements & Awards")
        achievements_layout = QVBoxLayout(achievements_group)
        achievements_label = QLabel("List your achievements (one per line):")
        achievements_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.achievements_input = QTextEdit()
        self.achievements_input.setPlaceholderText("e.g.\nFirst Prize in National Coding Competition\nDean's List for Academic Excellence\nPublished Research Paper in IEEE")
        self.achievements_input.setMaximumHeight(120)
        achievements_layout.addWidget(achievements_label)
        achievements_layout.addWidget(self.achievements_input)
        scroll_layout.addWidget(achievements_group)
        
        # Job Application Section
        job_group = self.create_section("📋 Target Job Information")
        job_layout = QGridLayout()
        job_layout.setSpacing(10)
        
        job_fields = [
            ("job_title", "Job Title", "Software Engineer Intern"),
            ("company", "Company Name", "Google"),
        ]
        
        self.job_fields = {}
        for i, (field_id, label_text, placeholder) in enumerate(job_fields):
            label = QLabel(label_text + ":")
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            job_layout.addWidget(label, i, 0)
            job_layout.addWidget(input_field, i, 1)
            self.job_fields[field_id] = input_field
        
        # Job description
        desc_label = QLabel("Job Description:")
        desc_label.setStyleSheet("font-weight: bold; color: #34495e;")
        self.job_fields["job_description"] = QTextEdit()
        self.job_fields["job_description"].setPlaceholderText("Paste the job description here...")
        self.job_fields["job_description"].setMaximumHeight(100)
        job_layout.addWidget(desc_label, 2, 0)
        job_layout.addWidget(self.job_fields["job_description"], 2, 1)
        
        job_group.setLayout(job_layout)
        scroll_layout.addWidget(job_group)
        
        # Set the scroll content
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Progress section (initially hidden)
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Preparing...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        self.progress_frame.setVisible(False)
        main_layout.addWidget(self.progress_frame)
        
        # Buttons at the bottom
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 2px solid #e9ecef;
                padding: 10px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(15)
        
        self.reset_button = self.create_action_button("🗑️ Reset All Data", "#e74c3c")
        self.reset_button.clicked.connect(self.reset_info)
        
        self.generate_button = self.create_action_button("🤖 Generate AI Resume", "#27ae60")
        self.generate_button.clicked.connect(self.generate_ai_resume)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)
        
        main_layout.addWidget(button_frame)
        
        # Set global styles
        self.apply_styles()
        
        # Create prompt template file if it doesn't exist
        self.create_prompt_template_file()
    
    def create_prompt_template_file(self):
        """Create the prompt template file if it doesn't exist"""
        if not os.path.exists("prompt_template.txt"):
            template_content = """You are an AI assistant that edits LaTeX resumes and writes cover letters.

Given details:

User Profile (JSON):
{user_profile}

Job Requirements:
{job_requirements}

Required Skills (from AI analysis):
{required_skills}

Instructions:
- Update the given LaTeX resume template with the user details.
- Select **at most 2 best experiences** most relevant to the job.
- Select **at most 3 projects** most related to the job.
- Insert **skills** that match or are relevant to the job requirements.
- Select **at most 3 positions of responsibility**.
- Select **at most 2 achievements**.
- Preserve the LaTeX formatting.
- Output only valid .tex code, no explanations.

After the updated resume:
- Generate a cover letter (plain text, not LaTeX) tailored for the given job description.

Base Resume Template (.tex):
[Include the base template here - the same template from your original document]

Please generate the customized resume and cover letter based on the provided information."""
            
            try:
                with open("prompt_template.txt", "w", encoding="utf-8") as f:
                    f.write(template_content)
            except Exception as e:
                print(f"Warning: Could not create prompt template file: {e}")
    
    def create_section(self, title):
        """Create a styled section group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
        """)
        return group
    
    def create_add_button(self, text, icon):
        """Create a styled add button"""
        button = QPushButton(f"{icon} {text}")
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #74b9ff, stop:1 #0984e3);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #0984e3, stop:1 #74b9ff);
            }
            QPushButton:pressed {
                background: #0570c9;
            }
        """)
        return button
    
    def create_action_button(self, text, color):
        """Create a styled action button"""
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
                border: 2px solid {self.darken_color(color, 0.7)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
                padding: 13px 25px 11px 23px;
            }}
        """)
        return button
    
    def darken_color(self, color, factor=0.9):
        """Darken a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def create_entry_widget(self, fields_config, remove_callback):
        """Create a styled entry widget with proper labels"""
        entry_frame = QFrame()
        entry_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QGridLayout(entry_frame)
        layout.setSpacing(8)
        entry_data = {}
        
        for i, (field_key, label_text, placeholder) in enumerate(fields_config):
            label = QLabel(label_text + ":")
            label.setStyleSheet("font-weight: bold; color: #495057; font-size: 11px;")
            
            if field_key == "description":
                input_field = QTextEdit()
                input_field.setMaximumHeight(60)
                input_field.setPlaceholderText(placeholder)
            else:
                input_field = QLineEdit()
                input_field.setPlaceholderText(placeholder)
            
            row = i // 2
            col = (i % 2) * 2
            
            layout.addWidget(label, row * 2, col, 1, 1)
            layout.addWidget(input_field, row * 2 + 1, col, 1, 1)
            entry_data[field_key] = input_field
        
        # Remove button
        remove_button = QPushButton("🗑️ Remove")
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_button.clicked.connect(remove_callback)
        
        # Add remove button to the last position
        total_fields = len(fields_config)
        last_row = ((total_fields - 1) // 2) * 2 + 1
        layout.addWidget(remove_button, last_row + 1, 0, 1, 4)
        
        return entry_frame, entry_data
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f1f3f4;
            }
            QLineEdit, QTextEdit {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QLabel {
                color: #495057;
            }
            QScrollArea {
                background-color: transparent;
            }
        """)
        
    def add_education_entry(self, data=None):
        fields_config = [
            ("degree", "Degree/Program", "e.g., B.Tech Computer Science"),
            ("institute", "Institute/University", "e.g., IIT Delhi"),
            ("cgpa", "CGPA/Percentage", "e.g., 8.5/10 or 85%"),
            ("year", "Year of Completion", "e.g., 2024")
        ]
        
        entry_widget, entry_data = self.create_entry_widget(
            fields_config, 
            lambda: self.remove_entry(entry_widget, self.education_layout)
        )
        
        # Load existing data if provided
        if data:
            for field_key, input_field in entry_data.items():
                if field_key in data:
                    input_field.setText(data[field_key])
        
        self.education_layout.insertWidget(self.education_layout.count() - 1, entry_widget)
        
    def add_experience_entry(self, data=None):
        fields_config = [
            ("company", "Company Name", "e.g., Google Inc."),
            ("role", "Job Role", "e.g., Software Engineer Intern"),
            ("duration", "Duration", "e.g., June 2023 - Aug 2023"),
            ("description", "Description", "Describe your key responsibilities and achievements...")
        ]
        
        entry_widget, entry_data = self.create_entry_widget(
            fields_config, 
            lambda: self.remove_entry(entry_widget, self.experience_layout)
        )
        
        # Load existing data if provided
        if data:
            for field_key, input_field in entry_data.items():
                if field_key in data:
                    if isinstance(input_field, QTextEdit):
                        input_field.setText(data[field_key])
                    else:
                        input_field.setText(data[field_key])
        
        self.experience_layout.insertWidget(self.experience_layout.count() - 1, entry_widget)
        
    def add_project_entry(self, data=None):
        fields_config = [
            ("title", "Project Title", "e.g., E-commerce Website"),
            ("description", "Project Description", "Describe your project, technologies used, and key features...")
        ]
        
        entry_widget, entry_data = self.create_entry_widget(
            fields_config, 
            lambda: self.remove_entry(entry_widget, self.projects_layout)
        )
        
        # Load existing data if provided
        if data:
            for field_key, input_field in entry_data.items():
                if field_key in data:
                    if isinstance(input_field, QTextEdit):
                        input_field.setText(data[field_key])
                    else:
                        input_field.setText(data[field_key])
        
        self.projects_layout.insertWidget(self.projects_layout.count() - 1, entry_widget)
        
    def add_por_entry(self, data=None):
        fields_config = [
            ("title", "Position Title", "e.g., Team Lead"),
            ("org", "Organization", "e.g., Student Council"),
            ("duration", "Duration", "e.g., Jan 2023 - Dec 2023")
        ]
        
        entry_widget, entry_data = self.create_entry_widget(
            fields_config, 
            lambda: self.remove_entry(entry_widget, self.por_layout)
        )
        
        # Load existing data if provided
        if data:
            for field_key, input_field in entry_data.items():
                if field_key in data:
                    input_field.setText(data[field_key])
        
        self.por_layout.insertWidget(self.por_layout.count() - 1, entry_widget)
        
    def remove_entry(self, widget, layout):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == widget:
                layout.removeItem(item)
                widget.deleteLater()
                break
                
    def load_user_data(self):
        if os.path.exists(self.user_data_file):
            try:
                with open(self.user_data_file, 'r') as f:
                    data = json.load(f)
                    
                # Load personal info
                for field_id, field in self.personal_fields.items():
                    if field_id in data:
                        field.setText(data[field_id])
                
                # Load education
                if 'education' in data:
                    for edu in data['education']:
                        self.add_education_entry(edu)
                
                # Load experience
                if 'experience' in data:
                    for exp in data['experience']:
                        self.add_experience_entry(exp)
                
                # Load projects
                if 'projects' in data:
                    for proj in data['projects']:
                        self.add_project_entry(proj)
                
                # Load skills
                if 'skills' in data:
                    self.skills_input.setText(", ".join(data['skills']))
                
                # Load POR
                if 'por' in data:
                    for por in data['por']:
                        self.add_por_entry(por)
                
                # Load achievements
                if 'achievements' in data:
                    self.achievements_input.setText("\n".join(data['achievements']))
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load user data: {str(e)}")
                
    def save_user_data(self):
        data = {}
        
        # Save personal info
        for field_id, field in self.personal_fields.items():
            data[field_id] = field.text().strip()
        
        # Save education
        data['education'] = []
        for i in range(self.education_layout.count()):
            item = self.education_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame):
                widget = item.widget()
                inputs = widget.findChildren(QLineEdit)
                if len(inputs) >= 4:
                    data['education'].append({
                        'degree': inputs[0].text().strip(),
                        'institute': inputs[1].text().strip(),
                        'cgpa': inputs[2].text().strip(),
                        'year': inputs[3].text().strip()
                    })
        
        # Save experience
        data['experience'] = []
        for i in range(self.experience_layout.count()):
            item = self.experience_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame):
                widget = item.widget()
                line_edits = widget.findChildren(QLineEdit)
                text_edits = widget.findChildren(QTextEdit)
                if len(line_edits) >= 3 and len(text_edits) >= 1:
                    data['experience'].append({
                        'company': line_edits[0].text().strip(),
                        'role': line_edits[1].text().strip(),
                        'duration': line_edits[2].text().strip(),
                        'description': text_edits[0].toPlainText().strip()
                    })
        
        # Save projects
        data['projects'] = []
        for i in range(self.projects_layout.count()):
            item = self.projects_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame):
                widget = item.widget()
                line_edits = widget.findChildren(QLineEdit)
                text_edits = widget.findChildren(QTextEdit)
                if len(line_edits) >= 1 and len(text_edits) >= 1:
                    data['projects'].append({
                        'title': line_edits[0].text().strip(),
                        'description': text_edits[0].toPlainText().strip()
                    })
        
        # Save skills
        skills_text = self.skills_input.text().strip()
        data['skills'] = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
        
        # Save POR
        data['por'] = []
        for i in range(self.por_layout.count()):
            item = self.por_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame):
                widget = item.widget()
                inputs = widget.findChildren(QLineEdit)
                if len(inputs) >= 3:
                    data['por'].append({
                        'title': inputs[0].text().strip(),
                        'org': inputs[1].text().strip(),
                        'duration': inputs[2].text().strip()
                    })
        
        # Save achievements
        achievements_text = self.achievements_input.toPlainText().strip()
        data['achievements'] = [ach.strip() for ach in achievements_text.split('\n') if ach.strip()]
        
        # Save to file
        try:
            with open(self.user_data_file, 'w') as f:
                json.dump(data, f, indent=2)
            return data
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save user data: {str(e)}")
            return None
    
    def get_job_data(self):
        """Get job application data"""
        return {
            'job_title': self.job_fields['job_title'].text().strip(),
            'company': self.job_fields['company'].text().strip(),
            'description': self.job_fields['job_description'].toPlainText().strip()
        }
    
    def validate_inputs(self):
        """Validate user inputs before processing"""
        # Check if basic personal info is filled
        if not self.personal_fields['name'].text().strip():
            return False, "Please enter your full name."
        
        if not self.personal_fields['email'].text().strip():
            return False, "Please enter your email address."
        
        # Check if job info is filled
        job_data = self.get_job_data()
        if not all(job_data.values()):
            return False, "Please fill in all job information fields (Job Title, Company, and Description)."
        
        return True, ""
    
    def generate_ai_resume(self):
        """Generate resume using AI integration"""
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Incomplete Information")
            msg.setText(error_msg)
            msg.exec_()
            return
        
        # Save user data
        user_data = self.save_user_data()
        if user_data is None:
            return
        
        # Get job data
        job_data = self.get_job_data()
        
        # Show progress section
        self.progress_frame.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Preparing...")
        
        # Disable generate button
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        
        # Create and start worker thread
        self.worker = ResumeGenerationWorker(user_data, job_data, None)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.status_updated.connect(self.progress_label.setText)
        self.worker.finished.connect(self.on_resume_generated)
        self.worker.error_occurred.connect(self.on_generation_error)
        self.worker.start()
    
    def on_resume_generated(self, resume_content):
        """Handle successful resume generation"""
        self.progress_frame.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🤖 Generate AI Resume")
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Success! 🎉")
        msg.setText("Your AI-powered resume has been generated successfully!")
        msg.setInformativeText("The customized resume has been saved as 'generated_resume.tex'. You can now compile it to PDF using LaTeX.")
        msg.setDetailedText(f"Preview of generated content:\n{resume_content[:500]}...")
        msg.exec_()
    
    def on_generation_error(self, error_message):
        """Handle resume generation errors"""
        self.progress_frame.setVisible(False)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🤖 Generate AI Resume")
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Generation Failed")
        msg.setText("Failed to generate resume using AI.")
        msg.setInformativeText("Please check your internet connection and API configurations.")
        msg.setDetailedText(f"Error details:\n{error_message}")
        msg.exec_()
            
    def reset_info(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Confirm Reset")
        msg.setText("Are you sure you want to reset all information?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        if msg.exec_() == QMessageBox.Yes:
            # Clear personal fields
            for field in self.personal_fields.values():
                field.clear()
            
            # Clear all dynamic entries
            self.clear_layout_entries(self.education_layout)
            self.clear_layout_entries(self.experience_layout)
            self.clear_layout_entries(self.projects_layout)
            self.clear_layout_entries(self.por_layout)
            
            # Clear other fields
            self.skills_input.clear()
            self.achievements_input.clear()
            
            # Clear job fields
            for field in self.job_fields.values():
                if isinstance(field, QLineEdit):
                    field.clear()
                else:
                    field.clear()
            
            # Remove the JSON file if it exists
            if os.path.exists(self.user_data_file):
                os.remove(self.user_data_file)
            
            success_msg = QMessageBox(self)
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowTitle("Reset Complete")
            success_msg.setText("All information has been successfully reset!")
            success_msg.exec_()
            
    def clear_layout_entries(self, layout):
        # Remove all widgets except the last one (which is the add button)
        while layout.count() > 1:
            item = layout.itemAt(0)
            widget = item.widget()
            if widget:
                layout.removeWidget(widget)
                widget.deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set color palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, QColor(33, 37, 41))
    app.setPalette(palette)
    
    window = UserProfileApp()
    window.show()
    sys.exit(app.exec_())