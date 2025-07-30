import streamlit as st
import pdfplumber
import pandas as pd
import re

# Define the Page class
class Page:
    def __init__(self, page_in, month_in, year_in, name_in, total_in):
        self.page = page_in
        self.month = month_in
        self.year = year_in
        self.name = name_in
        self.total = total_in

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

# Function to search for the "Energy" column index
def search_energy_col(table):
    for row in table:
        for idx, cell in enumerate(row):
            if re.search(r'Energy|Usage|MMBtu', cell, re.IGNORECASE):
                st.write(f"Energy column found at index: {idx}")
                return idx
    return -1  # Return -1 if no Energy column is found

# Function to extract all energy values from the "Energy" column
def find_total_energy(table):
    index = search_energy_col(table)
    
    if index == -1:
        st.write("Energy column not found.")
        return []

    energy_values = []
    # Extract energy values from the rows
    for row in table[1:]:  # Skip the header row
        try:
            energy_value = float(row[index])  # Extract the value from the Energy column
            energy_values.append(energy_value)
        except ValueError:
            continue  # In case there is an invalid value, just skip the row

    running_total = 0
    for item in energy_values:
        running_total += item  # Calculate the total energy

    return running_total

# Function to generate page data and CSV
def find_page_data(table, page_num):
    page_data = []

    # For month, year, and name we still need to rely on the text
    month_in = find_month(table)
    st.write("MONTH:", month_in)
    year_in = find_year(table)
    st.write("YEAR:", year_in)
    name_in = find_name(table)
    st.write("NAME:", name_in)
    
    total_in = find_total_energy(table)
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
    
    if input_file is None:
        return "No file uploaded. Please upload a PDF file to proceed."
    
    progress_bar = st.progress(0)
    page_data = []

    #----------------------------------------------------------------

    with pdfplumber.open(input_file) as pdf:
        if not pdf.pages:
            st.error("The PDF file is empty or has no pages.")
            return
        
        progress_bar.progress(10, "PDF opened successfully.")
        st.write(f"Total pages in PDF: {len(pdf.pages)}")

        # Loop through all the pages in the PDF
        for i in range(len(pdf.pages)):
            table = pdf.pages[i].extract_table()

            if table:
                st.write(f"Page {i + 1} Table:")
                st.write(table)  # Display the extracted table
            else:
                st.write(f"Page {i + 1} contains no extractable table.")

            page_num = i + 1
            progress_bar.progress(min(10 + ((i + 1) * 10), 90), f"Processing page {i + 1} of {len(pdf.pages)}")
            page_data.append(find_page_data(table, page_num))

    #----------------------------------------------------------------

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

# Execute the app
execute()
