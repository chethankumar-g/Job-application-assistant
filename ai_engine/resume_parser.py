import sys
from pathlib import Path

# Add project root to sys.path if run directly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import fitz  # PyMuPDF
import requests
from typing import List, Optional
from pydantic import BaseModel, Field

from config import config

# --- Define Pydantic Schemas for the Output ---
class PersonalInfo(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = Field(None, description="LinkedIn URL/username")
    github: Optional[str] = Field(None, description="GitHub URL/username")
    portfolio: Optional[str] = Field(None, description="Portfolio URL")

class Education(BaseModel):
    degree: str
    institution: str
    year: str

class Experience(BaseModel):
    job_title: str
    company: str
    duration: str
    description: str

class Project(BaseModel):
    project_title: str
    description: str

class Certification(BaseModel):
    certificate_name: str
    description: str

class Language(BaseModel):
    language_name: Optional[str] = None
    proficiency: Optional[str] = None

class ResumeSchema(BaseModel):
    personal_info: PersonalInfo
    experience_summary: Optional[str] = None
    skills: List[str]
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    certification: List[Certification]
    language: List[Language]

class ResumeParser:
    def __init__(self):
        self.ollama_url = config.OLLAMA_BASE_URL
        self.model = config.DEFAULT_MODEL

    def extract_text_from_pdf(self, pdf_path):
        """Extracts raw text from the provided PDF file."""
        print(f"[*] Reading PDF: {pdf_path}")
        text = ""
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except Exception as e:
            print(f"[!] Error reading PDF: {e}")
            return None

    def _call_ollama(self, prompt, schema_class):
        """Calls the local Ollama instance with structured output."""
        print(f"[*] Sending text to local AI ({self.model}) at {self.ollama_url} for extraction...")
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            # Pass the Pydantic schema as a JSON schema parameter
            "format": schema_class.model_json_schema() 
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            ai_response = response.json().get("response", "{}")
            return ai_response
        except requests.exceptions.RequestException as e:
            print(f"[!] Ollama API Error: {e}")
            return "{}"

    def parse_resume(self, text):
        """Constructs the prompt and extracts structured data using AI."""
        prompt = f"""
        You are an expert HR data extraction AI. Read the following resume text and extract the information.
        If a specific piece of information is missing from the resume, you MUST set its value to null.
        
        Resume Text:
        {text}
        """
        
        raw_json = self._call_ollama(prompt, ResumeSchema)
        
        try:
            parsed_data = json.loads(raw_json)
            # Optional: Validate via Pydantic model
            # validated_obj = ResumeSchema(**parsed_data)
            return parsed_data
        except json.JSONDecodeError:
            print("[!] AI failed to return valid JSON.")
            return {}
        except Exception as e:
            print(f"[!] Validation Error: {e}")
            return {}

    def log_missing_fields(self, data, parent_key=""):
        """Recursively checks for null or empty fields and logs them."""
        missing_fields = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                if value is None or value == "" or value == [] or value == "null":
                    missing_fields.append(full_key)
                else:
                    missing_fields.extend(self.log_missing_fields(value, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                missing_fields.extend(self.log_missing_fields(item, f"{parent_key}[{i}]"))
                
        return missing_fields

    def process_pdf(self, resume_name):
        """Main pipeline to convert a PDF to a saved Profile JSON."""
        
        pdf_path = config.RESUME_DIR / f"{resume_name}.pdf"
        output_path = config.PROFILES_DIR / f"profile_{resume_name}.json"

        if not pdf_path.exists():
            print(f"[!] Resume not found at {pdf_path}")
            return

        # 1. Extract Text
        text = self.extract_text_from_pdf(pdf_path)
        if not text: return

        # 2. Extract Data via AI
        profile_data = self.parse_resume(text)
        if not profile_data: return

        # 3. Identify and Log Missing Fields
        missing_fields = self.log_missing_fields(profile_data)
        if missing_fields:
            print("\n[!] The following fields were missing from the resume and require manual input:")
            for field in missing_fields:
                print(f"    - {field}")
        else:
            print("\n[+] All schema fields were successfully extracted!")

        # 4. Save to JSON
        with open(output_path, "w") as f:
            json.dump(profile_data, f, indent=4)
            
        print(f"\n[+] Profile saved to: {output_path}")

if __name__ == "__main__":
    parser = ResumeParser()
    parser.process_pdf(input("Enter Resume Name (without .pdf): "))