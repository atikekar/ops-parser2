# Sustainable Gas Operations Document Parser

This is a Python-based tool created for Constellation Energy Group to automate the extraction of invoice data from PDF documents. The application processes a table with columns containing specific keywords (Energy, MMBtu, Usage, Scheduled, Rounded) to extract the total value from the relevant column.

## Features

- **Smart Extraction Mode**: Automatically identifies the correct column based on the header keywords and extracts the total energy value.
- **Manual Extraction Mode**: Allows users to manually enter the total energy value when automated extraction fails or is unavailable.
- **Month, Year, and Name Extraction**: Extracts the month, year, and name (Operator, Facility, or Name) from the page text using regular expressions.

## Prerequisites

Ensure you have the following libraries installed:

- `streamlit` - for the user interface.
- `re` - for regular expressions.
- `pandas` - for data manipulation and CSV export.
- `pdfplumber` - for PDF text extraction.

You can install these dependencies using pip:

bash

'pip install -r requirements.txt'

## How It Works
- Input: The user uploads a PDF file containing the gas operations invoice.

**Keyword Search**: The program looks for the columns containing one of the following keywords:

- 'Energy'

- 'MMBtu'

- 'Usage'

- 'Scheduled'

- 'Rounded'

**Extraction**: The program extracts the total value from the identified column in either Smart or Manual mode.

**Output**: The extracted data is saved to a CSV file and made available for download.

## Functions Overview

- find_month(lines)
Extracts the month from the PDF lines using regex. It supports both named months (e.g., "January") and numeric representations (e.g., "01/01/2021").

- find_year(lines)
Extracts the year from the PDF lines using regex. It looks for a 4-digit year in the text (e.g., 2021).

- find_name(lines)
Identifies the name of the facility or operator. It looks for lines containing Name:, Operator:, or Facility.

- find_total_energy(page_lines, extract_mode)
Extracts the total energy value based on the selected extraction mode. In Smart Extract mode, it searches the header for keywords and tries to extract the value. In Manual Extract mode, the user is prompted to manually enter the value.

- find_page_data(page, page_num, extract_mode)
Collects data from each page: month, year, name, and total energy value. This data is stored in an instance of the Page class.

- save_to_csv(page_data, output_csv_path)
Saves the extracted data into a CSV file. The CSV file includes columns for the page number, month, year, name, and total energy.

- execute()
Main function that powers the Streamlit app. It loads the PDF, processes each page, and saves the extracted data into a CSV file. Users can download the CSV once the process is complete.

## Example Usage

Run the app:
Launch the Streamlit app by running:

bash
Copy
streamlit run app.py
Upload the PDF:
Once the app is running, upload the PDF containing the invoice data.

Choose Extraction Mode:
Select the Smart Extract mode for automated extraction or Manual Extract for manual input.

Download the CSV:
After the data is processed, download the CSV file with the extracted data.

File Output
The extracted data is saved as a CSV file with the following columns:

- 'Page': The page number.

- 'Month': The month extracted from the page.

- 'Year': The year extracted from the page.

- 'Name': The name of the operator or facility.

Total Energy: The extracted total energy value.

Sample CSV Output
Page	Month	Year	Name	Total Energy
1	January	2021	Facility ABC	4500
2	February	2021	Facility XYZ	7000

Contributing
Feel free to fork this repository, open issues, and submit pull requests. Contributions are welcome!

License
This project is licensed under the MIT License - see the LICENSE file for details.
