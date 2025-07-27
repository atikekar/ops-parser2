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
def find_month(text):
    matches = []
    lines = text.split('\n')
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
def find_year(text):
    matches = []
    lines = text.split('\n')
    for line in lines:
        year_pattern = r'\b(20)\d{2}\b'
        match = re.search(year_pattern, line)
        if match:
            matches.append(int(match.group(0)))
    if matches:
        return max(set(matches), key=matches.count)
    return None

# Extract name from text or fallback to PDF title
def find_name(text):
    matches = []
    lines = text.split('\n')
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

# Extract total energy from the "Energy" column in the table
def find_total_energy(extracted_data):
    total_energy = []
    # Loop through all rows in the extracted table
    for row in extracted_data:
        st.write(f"Processing row: {row}")  # Debugging line to see the row content
        # Look for "Energy" in the table header and extract the column index
        if "Energy" in row:
            energy_index = row.index("Energy")  # Find the column of interest
            continue
        # Check if the row has numeric values (energy values)
        if len(row) > energy_index and row[energy_index].replace('.', '', 1).isdigit():
            total_energy.append(row[energy_index])  # Append energy value

    return total_energy  # Return the list of energy values

# Function to generate page data and CSV
def find_page_data(extracted_text):
    page_data = []

    st.write(f"Total pages in PDF: {len(extracted_text)}")

    for i, page in enumerate(extracted_text):
        month_in = find_month(page)
        st.write(month_in)
        year_in = find_year(page)
        st.write(year_in)
        name_in = find_name(page)  # Pass the file_bytes to find_name
        st.write(name_in)
        total_in = find_total_energy(page)
        st.write(total_in)
        page_data.append(Page(i + 1, month_in, year_in, name_in, total_in))

    return page_data

# Function to save data to CSV
def save_to_csv(page_data, output_csv_path):
    csv_data = []
    for page in page_data:
        csv_data.append({
            "Page": page.page,
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

    extracted_text = []

    with pdfplumber.open(input_file) as pdf:
        if not pdf.pages:
            st.error("The PDF file is empty or has no pages.")
            return
        
        progress_bar.progress(10, "PDF opened successfully.")

        for i, page in enumerate(pdf.pages):
            lines = page.extract_text_lines()
            st.write(lines)
            extracted_text.append(lines)
            progress_bar.progress((10 + ((i + 1) * 10)), "Processing page {i + 1}")
    
    progress_bar.progress(50, "Extracting data from file.")
    page_data = find_page_data(extracted_text)

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

st.write("## PDF Processing Application")
execute()