****************************************************
Sustainable Gas Operations Document Parser
****************************************************

This is a Python-based tool created for Constellation Energy Group to automate the extraction of invoice data from PDF documents. The application processes a table with columns containing specific keywords (Energy, MMBtu, Usage, Scheduled, Rounded) to extract the total value from the relevant column.

****************************************************
Features
****************************************************

- **Smart Extraction Mode**: Automatically identifies the correct column based on the header keywords and extracts the total energy value.
- **Manual Extraction Mode**: Allows users to manually enter the total energy value when automated extraction fails or is unavailable.
- **Month, Year, and Name Extraction**: Extracts the month, year, and name (Operator, Facility, or Name) from the page text using regular expressions.
- **Month Number Mapping**: Converts month names to corresponding numerical values (e.g., January = 1, February = 2) for easier processing and analysis.
- **Data Table Preview**: Displays the extracted data as a result table on the Streamlit UI, allowing users to review the data before saving it to CSV.

****************************************************
Prerequisites
****************************************************

Ensure you have the following libraries installed:

- **streamlit** - for the user interface.
- **re** - for regular expressions.
- **pandas** - for data manipulation and CSV export.
- **pdfplumber** - for PDF text extraction.
- **calendar** - for month name utilities.

You can install these dependencies using pip: pip install -r requirements.txt


****************************************************
How It Works
****************************************************

1. **Input**: The user uploads a PDF file containing the gas operations invoice.
2. **Keyword Search**: The program looks for columns containing the following keywords:
   - **'Energy'**
   - **'MMBtu'**
   - **'Usage'**
   - **'Scheduled'**
   - **'Rounded'**
3. **Extraction**: The program extracts the total energy value from the identified column in either **Smart Extraction** mode or **Manual Extraction** mode.
4. **Output**: The extracted data is displayed in a table and saved as a CSV file. The user can then download the CSV file.

****************************************************
Functions Overview
****************************************************

- **find_month(lines, page_num)**: Extracts the month from the PDF lines using regex. It supports both named months (e.g., "January") and numeric representations (e.g., "01/01/2021"). In case of an error, the user is prompted to manually input the month.
  
- **find_year(lines, page_num)**: Extracts the year from the PDF lines using regex. It looks for a 4-digit year in the text (e.g., 2021). If the year is not found, the user is prompted to manually enter the year.
  
- **find_name(lines, page_num)**: Identifies the name of the facility or operator. It looks for lines containing **Name**, **Operator**, or **Facility**. If no name is found, the user can manually enter the name.
  
- **find_total_energy(page_lines, extract_mode, page_num)**: Extracts the total energy value based on the selected extraction mode. In **Smart Extract** mode, the program searches the header for keywords and tries to extract the value. In **Manual Extract** mode, the user is prompted to manually enter the value.
  
- **translate_month(month_in)**: Converts the month name (e.g., "January") to its corresponding integer (e.g., 1 for January). It uses a dictionary to map month names to integers.
  
- **find_page_data(page, page_num, extract_mode)**: Collects data from each page, including month, year, name, and total energy value. This data is stored in an instance of the `Page` class.
  
- **save_to_csv(page_data, output_csv_path)**: Saves the extracted data into a CSV file, which includes the page number, month name, month number, year, name, and total energy.

- **execute()**: Main function that powers the Streamlit app. It loads the PDF, processes each page, and saves the extracted data into a CSV file. Users can download the CSV once the process is complete.

****************************************************
Example Usage
****************************************************

### Run the app:
Launch the Streamlit app by running:

