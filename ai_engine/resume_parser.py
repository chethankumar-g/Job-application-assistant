import os
import json
import fitz  # PyMuPDF
import requests
from pathlib import Path

import time
from functools import wraps

def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"Execution time for {func.__name__}: {end - start:.6f} seconds")
        return result
    return wrapper


class ResumeParser:
    def __init__(self, ollama_url="http://localhost:11434", model="qwen2.5:1.5b"):
        self.ollama_url = ollama_url
        self.model = model
        self.schema = {
            "personal_info": {
                "first_name": "string or null",
                "last_name": "string or null",
                "email": "string or null",
                "phone": "string or null",
                "linkedin": "string or null",
                "github": "string or null",
                "portfolio": "string or null"
            },
            "experience_summary": "string or null",
            "skills": ["array of strings"],
            "education": [{"degree": "string", "institution": "string", "year": "string"}],
            "experience": [{"job_title": "string", "company": "string", "duration": "string", "description": "string"}],
            "projects" : [{"project_title": "string", "description": "string"}],
            "Certification" : [{"certificate_name": "string", "description": "string"}]
        }

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
    @time_it
    def _call_ollama(self, prompt):
        """Calls the local Ollama instance and forces JSON output."""
        print(f"[*] Sending text to local AI ({self.model}) for extraction...")
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json" # CRITICAL: Forces the model to return valid JSON
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "{}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Ollama API Error: {e}")
            return "{}"

    @time_it
    def parse_resume(self, text):
        """Constructs the prompt and extracts structured data using AI."""
        prompt = f"""
        You are a highly accurate HR data extraction AI. Your task is to parse resume text and convert all relevant information into a structured JSON object that strictly follows the provided schema.

        Instructions:
        1. Extract information only from the provided resume text.
        2. Populate every field defined in the schema.
        3. If a field is not present in the resume, set its value to null.
        4. Do not infer or fabricate information that is not explicitly stated.
        5. Preserve the schema structure exactly (keys, nesting, and data types).
        6. Lists in the schema must always be returned as arrays (even if they contain only one item).
        7. Dates should be returned exactly as written in the resume unless the schema specifies a format.
        8. Remove extra whitespace and normalize text where appropriate.
        9. Return ONLY valid JSON. Do not include explanations, comments, markdown, or additional text.

        JSON Schema:
        {json.dumps(self.schema, indent=2)}

        Resume Text:
        {text}

        Output:
        Return a single valid JSON object that strictly matches the schema above.
        """
        
        raw_json = self._call_ollama(prompt)
        
        try:
            parsed_data = json.loads(raw_json)
            return parsed_data
        except json.JSONDecodeError:
            print("[!] AI failed to return valid JSON.")
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
        # Setup paths based on standard structure
        base_dir = Path(__file__).parent.parent
        pdf_path = base_dir / "assets" / "resume" / f"{resume_name}.pdf"
        output_path = base_dir / "assets" / "profiles" / f"profile_{resume_name}.json"

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
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(profile_data, f, indent=4)
            
        print(f"\n[+] Profile saved to: {output_path}")

if __name__ == "__main__":
    parser = ResumeParser()
    parser.process_pdf(input("Enter Resume Name: "))