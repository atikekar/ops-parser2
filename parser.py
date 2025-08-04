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


# Define the options for extraction
smart = "Smart Extract"
manual = "Manual Extract"


def find_closest_number(page_lines, energy_coordinates):
    closest_num = None
    closest_distance = float('inf')  # Initialize to a very high number
    
    for line in page_lines:
        # Look for numbers in the line
        num_match = re.match(r'^\d+', line.strip())  # Match numbers at the beginning of a line
        if num_match:
            # Get the number from the line
            number = num_match.group(0)
            # You can modify this to calculate the distance between the y-coordinates of the energy keyword and the current line
            current_coordinates = (0, 0, 0, 0)  # Replace this with the actual coordinates for the current line
            distance = abs(current_coordinates[1] - energy_coordinates[1])  # Calculate y-axis distance
            if distance < closest_distance:
                closest_distance = distance
                closest_num = number
    
    return closest_num

def remove_empty_lines(input_list):
    return [line for line in input_list if line.strip()]

def find_total_energy(page_lines, pdf_path):
    table = []
    head = []

    if "option" not in st.session_state:
        st.session_state.option = "Smart Extract"
    st.session_state.option = st.selectbox("Select extraction mode", ["Smart Extract", "Manual Extract"], index=["Smart Extract", "Manual Extract"].index(st.session_state.option))

    if st.session_state.option == "Smart Extract":

        for i, line in enumerate(page_lines):
            num_match = re.match(r'^\d', line)
            total_match = re.search(r'Total', line, re.IGNORECASE)
            header_match = re.search(r'Energy|Usage|MMBtu|Quantity|Current', line.strip(), re.IGNORECASE)
            if num_match or total_match: 
                table.append(line)
            if header_match: 
                head.append(line)

        st.write(table[-1])
        st.write(head[-1])

    else:
        st.warning("No total energy value found with Smart Extraction. Switching to Manual.")
        st.session_state.option = "Manual Extract"  # Set to manual mode after warning
        st.write(page_lines)
        energy_value = st.number_input("Enter Total Energy: ", min_value=0, value=0)
        st.write(f"Manually entered energy value: {energy_value}")
        return energy_value

    if st.session_state.option == "Manual Extract":
        st.write("Manual extraction mode selected.")
        st.write(page_lines)
        energy_value = st.number_input("Enter Total Energy: ", min_value=0, value=0)
        st.write(f"Manually entered energy value: {energy_value}")

    return 100

            
# Function to generate page data and CSV
def find_page_data(page, page_num, pdf_path):
    page_data = []
    
    month_in = find_month(page)
    year_in = find_year(page)
    name_in = find_name(page)
    total_in = find_total_energy(page, pdf_path)
    page_data.append(Page(page_num, month_in, year_in, name_in, total_in))

    return page_data

# Function to save data to CSV
def save_to_csv(page_data, output_csv_path):
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

        for i, page in enumerate(pdf.pages):
            text = page.extract_text(layout=True)
            lines = text.splitlines() if text else []
            page_num = i + 1

            progress_bar.progress(min(10 + ((i + 1) * 10), 90), f"Processing page {i + 1} of {len(pdf.pages)}")
            page_data.extend(find_page_data(lines, page_num, input_file))

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
