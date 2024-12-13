import os
import fitz 
from tqdm import tqdm
import logging
from warcio.archiveiterator import ArchiveIterator
from bs4 import BeautifulSoup
from langdetect import detect
import re
import os
import time

def count_tokens_in_pdf(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
        total_characters = 0
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text()
            total_characters += len(text) 
        
        pdf_document.close()
        
        tokens = total_characters / 4
        return total_characters, tokens
    except Exception as e:
        raise e

def estimate_tokens_in_pdf(folder_path):
    total_tokens = 0
    error_count = 0
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    logging.info(f"Found {len(pdf_files)} PDF files")

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs", leave=True):
        file_path = os.path.join(folder_path, pdf_file)
        try:
            _, token_count = count_tokens_in_pdf(file_path)
            total_tokens += token_count
        except Exception:
            error_count += 1

    return total_tokens, len(pdf_files)


def count_tokens(text):
    cleaned_text = re.sub(r'\s+', '', text)
    token_count = len(cleaned_text) // 4
    return token_count

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ')
    return text

def estimate_tokens_in_warc(output_folder):
    total_token_count = 0

    warc_files = [file for file in os.listdir(output_folder) if file.endswith('.warc')]
    logging.info(f'Found {len(warc_files)} WARC files')

    for processed_files, warc_file in enumerate(warc_files, start=1):
        warc_file_path = os.path.join(output_folder, warc_file)

        with open(warc_file_path, 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == 'response':
                    content = record.content_stream().read().decode('utf-8', errors='ignore')

                    text_content = extract_text_from_html(content)

                    try:
                        language = detect(text_content)
                    except:
                        language = 'unknown'

                    if language == 'id':
                        token_count = count_tokens(text_content)
                        total_token_count += token_count

        logging.info(f'Processed {processed_files}/{len(warc_files)} files. Token count in {warc_file}: {token_count}')

    return total_token_count, len(warc_files)