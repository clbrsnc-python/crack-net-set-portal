import re

def parse_txt_questions(content_str: str, subject: str, unit: str) -> list:
    """
    Parses plain text formatted questions into structured records.
    """
    questions = []
    blocks = re.split(r'\n\s*\n', content_str.strip())
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        q_data = {"subject": subject, "unit": unit, "explanation": "No explanation provided."}
        
        for line in lines:
            if line.startswith("Q:"):
                q_data["question_text"] = line[2:].strip()
            elif line.startswith("A)"):
                q_data["option_a"] = line[2:].strip()
            elif line.startswith("B)"):
                q_data["option_b"] = line[2:].strip()
            elif line.startswith("C)"):
                q_data["option_c"] = line[2:].strip()
            elif line.startswith("D)"):
                q_data["option_d"] = line[2:].strip()
            elif line.startswith("ANS:"):
                q_data["correct_option"] = line[4:].strip().upper()
            elif line.startswith("EXP:"):
                q_data["explanation"] = line[4:].strip()
                
        if len(q_data) >= 8 and "question_text" in q_data:
            questions.append(q_data)
            
    return questions