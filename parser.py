import streamlit as st
import re
import pandas as pd
from io import BytesIO
import pdfplumber
from calendar import month_name

class Page:
    def __init__(self, page_in, month_in, year_in, name_in, total_in):
        self.page = page_in
        self.month = month_in
        self.year = year_in
        self.name = name_in
        self.total = total_in

def find_month(lines, page_num):
    matches = []
    try:
        for line in lines:
            if not isinstance(line, str):
                continue
            month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)'
            match = re.search(month_pattern, line, re.IGNORECASE)
            if match:
                month = match.group(0).capitalize()
                matches.append(month)
            numeric_month_pattern = r'\b(\d{1,2})[/-]\d{1,2}[/-]\d{4}\b'
            match = re.search(numeric_month_pattern, line)
            if match:
                month_number = match.group(1)
                month_name_found = month_name[int(month_number)]
                matches.append(month_name_found)
        if matches:
            return max(set(matches), key=matches.count)
    except Exception as e:
        st.error(f"Couldn't Find Month")
        error_month = st.number_input(f"Enter Month For Page {page_num}: ", min_value=0.0, key=f"month_{page_num}")
        return error_month

def find_year(lines, page_num):
    matches = []
    try:
        for line in lines:
            if not isinstance(line, str):
                continue
            year_pattern = r'\b(20)\d{2}\b'
            match = re.search(year_pattern, line)
            if match:
                matches.append(int(match.group(0)))
        if matches:
            return max(set(matches), key=matches.count)
    except Exception as e:
        st.error(f"Couldn't Find Year")
        error_year = st.number_input(f"Enter Year For Page {page_num}: ", min_value=0.0, key=f"year_{page_num}")
        return error_year

def find_name(lines, page_num):
    matches = []
    try:
        for line in lines:
            if not isinstance(line, str):
                continue
            match = re.search(r'(Name:|Operator:|Facility)[^a-zA-Z0-9]*[:\s-]?\s*(.*)', line, re.IGNORECASE)
            if match:
                name = line.split(':')[-1].strip()
                matches.append(name)

        if not matches:
            for i, line in enumerate(lines):
                match_2 = re.search(r'Account Name', line, re.IGNORECASE)
                if match_2:
                    if i + 1 < len(lines):
                        name = lines[i + 1]
                        span = match_2.span()
                        pdf_title = name[span[0] - 5: span[1] + 5]
                        return pdf_title
            st.write("No name found in the text")
            st.text_input("Enter the name manually:", key="name_input")
            pdf_title = st.session_state.get("name_input", "Unknown Name")
            return pdf_title
        else:
            names = matches[0].split("      ")
            return names[0]
    except Exception as e:
        st.error(f"Couldn't Find Name")
        error_name = st.number_input(f"Enter Name For Page {page_num}: ", min_value=0.0, key=f"name_{page_num}")
        return error_name

def find_total_energy(page_lines, extract_mode, page_num):
    table = []
    head = []
    try:
        if extract_mode == "Smart Extract":
            for i, line in enumerate(page_lines):
                if not isinstance(line, str):
                    continue
                num_match = re.match(r'^\s*\d+', line)
                total_match = re.search(r'Total', line, re.IGNORECASE)
                header_match = re.search(r'Energy|Usage|MMBtu|Quantity|Current', line, re.IGNORECASE)

                if num_match or total_match:
                    table.append(line)
                if header_match:
                    head.append(line)

            keywords = ["Energy", "Usage", "MMBtu", "Rounded", "Current"]
            positions = [match.start() for match in re.finditer(r'\S+', head[-1])]

            keyword_index = None
            for keyword in keywords:
                if keyword in head[-1]:
                    keyword_index = head[-1].find(keyword)
                    break
            if keyword_index is not None:
                line2_value = table[-1][keyword_index - 2:].split()[0]
                return line2_value
            else:
                st.warning("Could not find the correct keyword in the header.")
                st.session_state.extract_mode = "Manual Extract"

        elif extract_mode == "Manual Extract":
            stripped_lines = [line for line in page_lines if line.strip() != '']
            st.write(stripped_lines)
            energy_value = st.number_input(f"Enter Total Energy For Page {page_num}: ", min_value=0.0, key=f"energy_input_{page_num}")
            return energy_value
    except Exception as e:
        st.error(f"Error in Smart Extraction, try Manual Extraction")
    return None


def find_page_data(page, page_num, extract_mode):
    page_data = []
    try:
        month_in = find_month(page)
        year_in = find_year(page)
        name_in = find_name(page)
        total_in = find_total_energy(page, extract_mode, page_num)
        page_data.append(Page(page_num, month_in, year_in, name_in, total_in))
    except Exception as e:
        st.error(f"Error in find_page_data: {str(e)}")
    return page_data


def save_to_csv(page_data, output_csv_path):
    try:
        csv_data = []
        page_num = 1
        for page in page_data:
            csv_data.append({
                "Page": page_num,
                "Month": page.month,
                "Year": page.year,
                "Name": page.name,
                "Total Energy": page.total
            })
            page_num += 1
        df = pd.DataFrame(csv_data)
        df.to_csv(output_csv_path, index=False)
        df.to_csv("extracted_data.csv", index=False)
    except Exception as e:
        st.error(f"Error in save_to_csv: {str(e)}")


def execute():
    try:
        st.image('./logo.jpg', use_container_width=True)
        st.title("Sustainable Gas Ops Document Parser")

        st.set_page_config(page_title="Sustainable Gas Ops Document Parser", layout="wide")
        input_file = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdf_uploader")
        input_file_name = str(input_file.name) if input_file else "extracted_data.pdf"

        if input_file is None:
            return "No file uploaded. Please upload a PDF file to proceed."

        extract_mode = st.selectbox("Select extraction mode", ["Smart Extract", "Manual Extract"], key="extract_mode")

        page_data = []

        with pdfplumber.open(input_file) as pdf:
            if not pdf.pages:
                st.error("The PDF file is empty or has no pages.")
                return

            for i, page in enumerate(pdf.pages):
                text = page.extract_text(layout=True)
                lines = text.splitlines() if text else []
                page_num = i + 1
                page_data.extend(find_page_data(lines, page_num, extract_mode))

        input_file_name = input_file.name if input_file.name else "extracted_data.pdf"
        csv_name = input_file_name.replace('.pdf', '_data.csv')
        output_csv_path = "/tmp/extracted_data.csv"
        save_to_csv(page_data, output_csv_path)

        st.download_button(
            label="Download CSV File",
            data=open(output_csv_path, 'rb').read(),
            file_name=csv_name,
            mime='text/csv'
        )
    except Exception as e:
        st.error(f"Error in execute function: {str(e)}")

execute()