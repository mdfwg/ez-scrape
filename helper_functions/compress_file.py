import os
import zipfile
import shutil
import logging

def compress_pdfs_to_zip(pdf_dir, description, output_dir):
    """
    Compress PDFs from the specified directory into a ZIP archive.
    
    Parameters:
    - pdf_dir: Directory containing the PDF files.
    - description: User-provided description for the ZIP archive name.
    - output_dir: Directory where the ZIP archive will be saved.

    Returns:
    - zip_path: Path to the created ZIP file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate ZIP file name
        zip_file_name = f"Zeus_{description}_pdf_files.zip"
        zip_path = os.path.join(output_dir, zip_file_name)
        
        # Create the ZIP file and add PDFs
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pdf_file in os.listdir(pdf_dir):
                if pdf_file.endswith(".pdf"):
                    pdf_path = os.path.join(pdf_dir, pdf_file)
                    zipf.write(pdf_path, arcname=pdf_file)  # Add file to ZIP with relative name
                    logging.info(f"Added {pdf_file} to the ZIP archive.")
        
        logging.info(f"ZIP archive created at: {zip_path}")
        return zip_path
    except Exception as e:
        logging.error(f"Error creating ZIP archive: {e}")
        return None

def compress_warcs_to_warcgz(warc_dir, description, output_dir):
    """
    Compress WARCs from the specified directory into a single .warc.gz file.
    
    Parameters:
    - warc_dir: Directory containing the WARC files.
    - description: User-provided description for the output WARC.GZ file name.
    - output_dir: Directory where the WARC.GZ archive will be saved.

    Returns:
    - gz_path: Path to the created WARC.GZ file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate output file name
        gz_file_name = f"Zeus_{description}_warc_combined.warc.gz"
        gz_path = os.path.join(output_dir, gz_file_name)

        with open(gz_path, 'wb') as output_file:
            for warc_file in os.listdir(warc_dir):
                if warc_file.endswith(".warc"):
                    warc_path = os.path.join(warc_dir, warc_file)
                    with open(warc_path, 'rb') as input_file:
                        shutil.copyfileobj(input_file, output_file)
                    logging.info(f"Added {warc_file} to the WARC.GZ archive.")
        
        logging.info(f"Combined WARC.GZ file created at: {gz_path}")
        return gz_path
    except Exception as e:
        logging.error(f"Error creating WARC.GZ file: {e}")
        return None
