import streamlit as st
import pandas as pd
import re
from io import BytesIO
import pdfplumber
import base64
import numpy as np
import os
from calendar import month_name

# Define the Page class
class Page:
    def __init__(self, page_in, month_in, year_in, name_in, total_in):
        self.page = page_in
        self.month = month_in
        self.year = year_in
        self.name = name_in
        self.total = total_in

# Function to display PDF preview in Streamlit
def display_pdf_preview(input_file):
    # Convert PDF to base64 for embedding
    pdf_bytes = input_file.read()
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"

    # Embed the PDF in the Streamlit app using an iframe
    st.components.v1.html(f'<iframe src="{pdf_data_uri}" width="700" height="500"></iframe>', height=600)

# Extract month from text
def find_month(lines):
    matches = []
    for line in lines:
        month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        match = re.search(month_pattern, line, re.IGNORECASE)
        if match:
            month = match.group(0).capitalize()
            matches.append(month)
        numeric_month_pattern = r'\b(\d{1,2})[/-]\d{1,2}[/-]\d{4}\b'
        match = re.search(numeric_month_pattern, line)
        if match:
            month_number = match.group(1)
            month_name_found = month_name[int(month_number)]  # Get month name from month_number
            matches.append(month_name_found)
    if matches:
        return max(set(matches), key=matches.count)
    return None

# Extract year from text
def find_year(lines):
    matches = []

    for line in lines:
        year_pattern = r'\b(20)\d{2}\b'
        match = re.search(year_pattern, line)
        if match:
            matches.append(int(match.group(0)))
    if matches:
        return max(set(matches), key=matches.count)
    return None

# Extract name from text or fallback to PDF title
def find_name(lines):
    matches = []
    for line in lines:
        match = re.search(r'(Name:|Operator:|Facility)[^a-zA-Z0-9]*[:\s-]?\s*(.*)', line, re.IGNORECASE)
        if match:
            name = line.split(':')[-1].strip()
            matches.append(name)
    if not matches:
        st.write("No name found in the text")
        st.text_input("Enter the name manually:", key="name_input")
        pdf_title = st.session_state.get("name_input", "Unknown Name")
        return pdf_title
    else:
        return matches[0]
    
def extract_table(lines):
    table_start = 0
    extracted_table = []
    # Find the header row 
    for i, line in enumerate(lines):
        # If the first element in the line is a date format, start the table extraction
        if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}', line) or re.match(r'^\d{1,2}[-/]\d{1,2}', line):
            if table_start == 0: table_start = i
            extracted_table.append(lines[i])

    # Append the header row to the extracted table
    if table_start > 0:
        extracted_table.append(lines[table_start])  # assuming the header is right after the first date entry
    return extracted_table

# Function to search for the "Energy" column index
def search_energy_col(table): 
    header_row = table[0] if table else []
    if re.search(r'Energy|Usage|MMBtu', header_row, re.IGNORECASE):
        energy_index = header_row.index(re.search(r'Energy', header_row, re.IGNORECASE).group(0))
        st.write(f"Energy column found at index: {energy_index}")
        return energy_index
    return -1  # Return -1 if no Energy column is found

# Function to extract all energy values from the "Energy" column
def find_total_energy(text):
    table = extract_table(text)

    index = search_energy_col(table)
    
    if index == -1:
        st.write("Energy column not found.")
        return []

    energy_values = []
    # Start from row 1 (the data rows) and extract energy values
    for row in table[1:]:
        # Assuming the energy values are in a numerical format in the "Energy" column
        try:
            energy_value = float(row.split()[index])  # Extract the value from the index
            energy_values.append(energy_value)
        except ValueError:
            continue  # In case there is an invalid value, just skip the row

    running_total = 0

    for items in energy_values:
        if running_total != items:
            running_total += items
        else: 
            return running_total

# Function to generate page data and CSV
def find_page_data(page, text, page_num):
    page_data = []

    month_in = find_month(page)
    st.write("MONTH:", month_in)
    year_in = find_year(page)
    st.write("YEAR:", year_in)
    name_in = find_name(page)  # Pass the file_bytes to find_name
    st.write("NAME:", name_in)
    total_in = find_total_energy(text)
    st.write("TOTAL ENERGY:", total_in)
    page_data.append(Page(page_num, month_in, year_in, name_in, total_in))

    return page_data

# Function to save data to CSV
def save_to_csv(page_data, output_csv_path):
    csv_data = []
    for i, page in enumerate(page_data):
        csv_data.append({
            "Page": i + 1,
            "Month": page.month,
            "Year": page.year,
            "Name": page.name,
            "Total Energy": page.total
        })
    df = pd.DataFrame(csv_data)
    df.to_csv(output_csv_path, index=False)
    df.to_csv("extracted_data.csv", index=False)


# Main function to execute the Streamlit app
def execute():

    st.title("Sustainable Gas Ops Document Parser")
    st.write("This application processes PDF files to extract relevant data and convert it into a CSV file.")

    st.set_page_config(page_title="Sustainable Gas Ops Document Parser", layout="wide")
    input_file = st.file_uploader("Upload a PDF file", type=["pdf"], key="pdf_uploader")
    input_file_name = str(input_file.name) if input_file else "extracted_data.pdf"
    #input_path = './sample1.pdf'
    #input_file = open(input_path, "rb")

    if input_file is None: return "No file uploaded. Please upload a PDF file to proceed."
    progress_bar = st.progress(0, "Converting PDF to images...")
    page_data = []

    with pdfplumber.open(input_file) as pdf:
        if not pdf.pages:
            st.error("The PDF file is empty or has no pages.")
            return
        
        progress_bar.progress(10, "PDF opened successfully.")
        st.write(f"Total pages in PDF: {len(pdf.pages)}")

        for i, page in enumerate(pdf.pages):
            text = page.extract_text_lines(layout=True)
            st.write(text)

            lines = text.splitlines() if text else []
            page_num = i + 1

            progress_bar.progress(min(10 + ((i + 1) * 10), 90), f"Processing page {i + 1} of {len(pdf.pages)}")
            page_data.append(find_page_data(lines, text, page_num))

    input_file_name = input_file.name if input_file.name else "extracted_data.pdf"
    csv_name = input_file_name.replace('.pdf', '_data.csv')

    output_csv_path = "/tmp/extracted_data.csv"
    save_to_csv(page_data, output_csv_path)
    
    progress_bar.progress(100, "CSV file created successfully.")
    st.download_button(
        label="Download CSV File",
        data=open(output_csv_path, 'rb').read(),
        file_name=csv_name,
        mime='text/csv'
    )

execute()