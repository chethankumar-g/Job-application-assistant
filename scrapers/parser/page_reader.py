from bs4 import BeautifulSoup
import json

class FormParser:
    def __init__(self):
        pass

    def parse_html_to_fields(self, html_content):
        """
        Takes raw HTML, strips the junk, and returns a clean list of form fields
        that the AI can easily read without blowing up the VRAM.
        """
        print("[*] BeautifulSoup: Parsing raw HTML for form elements...")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # We will store actionable fields here
        form_fields = []

        # Find all inputs, selects, and textareas
        elements = soup.find_all(['input', 'select', 'textarea'])

        for elem in elements:
            tag_name = elem.name
            elem_id = elem.get('id', '')
            elem_type = elem.get('type', 'text')
            
            # Skip hidden fields, submit buttons, and files (we handle files separately)
            if elem_type in ['hidden', 'submit', 'file', 'button']:
                continue

            # 1. Try to find the associated label by 'for' attribute
            label_text = ""
            if elem_id:
                label = soup.find('label', attrs={'for': elem_id})
                if label:
                    label_text = label.get_text(strip=True)

            # 2. Fallback: check aria-label (Workday uses this heavily)
            if not label_text:
                label_text = elem.get('aria-label', '')

            # 3. Fallback: check placeholder
            if not label_text:
                label_text = elem.get('placeholder', '')

            # If we couldn't figure out what this field is asking, skip it to save AI confusion
            if not label_text:
                continue

            field_data = {
                "element_tag": tag_name,
                "input_type": elem_type,
                "selector_id": elem_id,
                "css_name": elem.get('name', ''),
                "question_asked": label_text
            }

            # If it's a dropdown, grab the options so the AI knows what to choose
            if tag_name == 'select':
                options = [opt.get_text(strip=True) for opt in elem.find_all('option') if opt.get_text(strip=True)]
                field_data["available_options"] = options

            form_fields.append(field_data)

        print(f"[+] Found {len(form_fields)} actionable form fields.")
        return form_fields

if __name__ == "__main__":
    # Quick test
    sample_html = '<label for="fname">First Name</label><input type="text" id="fname" name="fname">'
    parser = FormParser()
    print(json.dumps(parser.parse_html_to_fields(sample_html), indent=2))