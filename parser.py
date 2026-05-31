import os
import PyPDF2

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file.

    Parameters:
        file_path (str): The path to the PDF resume file.

    Returns:
        str: The extracted text as a string.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: The file '{file_path}' does not exist.")

    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"Error: The file '{file_path}' is not a PDF file.")

    text_content = []
    try:
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
                    
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error: Failed to read the PDF file. It might be corrupted. Details: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while parsing the PDF: {e}")
        raise

    return "\n".join(text_content)

if __name__ == "__main__":
    # Test example
    print("--- Running PDF Parser Test ---")
    
    # Define a test file path (adjust this to your local environment as needed)
    test_pdf_path = "Project Documentation.pdf"
    
    if os.path.exists(test_pdf_path):
        print(f"Attempting to extract text from: {test_pdf_path}")
        try:
            extracted_text = extract_text_from_pdf(test_pdf_path)
            print("\nSuccessfully extracted text! Preview (first 500 characters):")
            print("-" * 50)
            print(extracted_text[:500])
            print("-" * 50)
            print(f"Total character count: {len(extracted_text)}")
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        # Fallback test with a non-existent file to demonstrate error handling
        print(f"Test file '{test_pdf_path}' not found.")
        print("Testing error handling with a non-existent file path:")
        try:
            extract_text_from_pdf("non_existent_file.pdf")
        except Exception as e:
            print(f"Caught expected exception: {e}")
