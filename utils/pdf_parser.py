import pdfplumber
import re

def parse_pdf_mock_test(pdf_file, subject: str, unit: str) -> list:
    """
    Extracts text from PDF and parses questions assuming the last page contains the answer key.
    """
    questions = []
    full_text = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages[:num_pages-1]:
            extracted = page.extract_text()
            if extracted:
                full_text += extracted + "\n"
        
        last_page_text = pdf.pages[-1].extract_text() if num_pages > 0 else ""
    
    answer_keys = {}
    if last_page_text:
        matches = re.findall(r'(\d+)[\.\s:\-]+\s*([A-Da-d])', last_page_text)
        for q_num, ans in matches:
            answer_keys[int(q_num)] = ans.upper()
        
    return questions
