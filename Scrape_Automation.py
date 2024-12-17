import os
import streamlit as st
import logging
import time
import pandas as pd
from datetime import datetime

from helper_functions.link_scrapper import scrapelinksmain
from helper_functions.warc_scraper import warcscrappermain
from helper_functions.pdf_scraper import pdfscrappermain
from helper_functions.token_est import estimate_tokens_in_pdf, estimate_tokens_in_warc
from helper_functions.compress_file import compress_pdfs_to_zip, compress_warcs_to_warcgz
from helper_functions.dashboard import get_project_stats, get_detailed_project_data

# import torch
# import transformers

# ---------------------------- Logging Setup ----------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------- Streamlit App ----------------------------
st.title("Scrape Automation and Token Estimator")

# Root output directory
output_root = "output"

# Ensure the output folder exists
if not os.path.exists(output_root):
    os.makedirs(output_root)

# ---------------------------- Project Management ----------------------------
# Get list of top-level projects (directories in output)
projects = [project for project in os.listdir(output_root) if os.path.isdir(os.path.join(output_root, project))]

# ---------------------------- Sidebar for Project Management ----------------------------
with st.sidebar:
    st.header("Project Management")
    
    # Initialize session state for tracking new project/subproject creation
    if 'creating_project' not in st.session_state:
        st.session_state.creating_project = False
    if 'creating_subproject' not in st.session_state:
        st.session_state.creating_subproject = False
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_subproject' not in st.session_state:
        st.session_state.current_subproject = None

    # Project management
    project_name = st.selectbox("Select Project", ["--Select a Project--"] + projects, key="project_selector")

    # Project selection confirmation
    if project_name != "--Select a Project--":
        if st.button("Confirm Project Selection"):
            st.session_state.current_project = project_name
            st.success(f"Project '{project_name}' selected.")

    # New Project Creation
    if not st.session_state.creating_project:
        if st.button("Add New Project"):
            st.session_state.creating_project = True
    
    if st.session_state.creating_project:
        new_project_name = st.text_input("Enter New Project Name", key="new_project_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Project"):
                if new_project_name and new_project_name not in projects:
                    try:
                        project_path = os.path.join(output_root, new_project_name)
                        os.makedirs(project_path, exist_ok=True)
                        
                        st.success(f"Project '{new_project_name}' created successfully.")
                        st.session_state.creating_project = False
                        
                        # Refresh projects list
                        projects = [project for project in os.listdir(output_root) if os.path.isdir(os.path.join(output_root, project))]
                    except Exception as e:
                        st.error(f"Error creating project: {e}")
        
        with col2:
            if st.button("Cancel"):
                st.session_state.creating_project = False

    # Subproject management
    subprojects = []  # Initialize subprojects list
    if st.session_state.current_project:
        try:
            subprojects = [
                subproject for subproject in os.listdir(os.path.join(output_root, st.session_state.current_project)) 
                if os.path.isdir(os.path.join(output_root, st.session_state.current_project, subproject))
            ]
        except Exception as e:
            st.error(f"Error reading subprojects: {e}")

    # Subproject selector
    if st.session_state.current_project:
        subproject_name = st.selectbox(
            "Select Subproject", 
            ["--Select a Subproject--"] + subprojects, 
            key="subproject_selector"
        )

        # Subproject selection confirmation
        if subproject_name != "--Select a Subproject--":
            if st.button("Confirm Subproject Selection"):
                st.session_state.current_subproject = subproject_name
                st.success(f"Subproject '{subproject_name}' selected.")

        # New Subproject Creation
        if not st.session_state.creating_subproject:
            if st.button("Add New Subproject"):
                st.session_state.creating_subproject = True
        
        if st.session_state.creating_subproject:
            new_subproject_name = st.text_input("Enter New Subproject Name", key="new_subproject_input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Subproject"):
                    if new_subproject_name and new_subproject_name not in subprojects:
                        try:
                            subproject_path = os.path.join(output_root, st.session_state.current_project, new_subproject_name)
                            os.makedirs(subproject_path, exist_ok=True)
                            

                            # Create standard subdirectories ONLY for subproject
                            subdirs = ["pdfs", "links", "warcs", "tokens-counted"]
                            for subdir in subdirs:
                                os.makedirs(os.path.join(subproject_path, subdir), exist_ok=True)
                            
                            st.success(f"Subproject '{new_subproject_name}' created successfully.")
                            st.session_state.creating_subproject = False
                        except Exception as e:
                            st.error(f"Error creating subproject: {e}")
            
            with col2:
                if st.button("Cancel Subproject"):
                    st.session_state.creating_subproject = False

    # Display current selections
    st.divider()
    st.write("**Current Selections:**")
    st.write(f"Project: {st.session_state.current_project or 'None'}")
    st.write(f"Subproject: {st.session_state.current_subproject or 'None'}")

# ---------------------------- Tabs ----------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Link Scraper", "PDF Scraper", "WARC Scraper", "Token Estimator", "Compress", "Sahabat-AI", "Dashboard"])

# ---------------------------- Link Scraper Tab ----------------------------
with tab1:
    st.header("Link Scraper")
    
    base_url = st.text_input("Base URL", "", key="link_scraper_base_url", placeholder="https://example.com")
    link_selector = st.text_input("Link Selector (CSS)", "", key="link_scraper_link_selector", placeholder="a.link-class")
    pagination_url = st.text_input("Pagination URL (optional)", "", key="link_scraper_pagination_url", placeholder="https://example.com/page={page_number}")
    next_button_selector = st.text_input("Next Button Selector (optional)", "", key="link_scraper_next_button", placeholder="button.next")
    max_pages = st.number_input("Max Pages", min_value=1, value=1, key="link_scraper_max_pages")
    
    # New Options for Scroll/Load More
    scroll_to_load_more = st.checkbox("Scroll to Load More Content", key="scroll_to_load_more")
    load_more_button_selector = st.text_input("Load More Button Selector (optional)", "", key="load_more_button_selector", placeholder="button.load-more")
    
    # Ensure the correct 'links' folder path exists within the selected project and subproject
    if st.session_state.current_project and st.session_state.current_subproject:
        links_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "links")
    
    if st.button("Run Link Scraper", key="run_link_scraper"):
        # Running the scraper with the correct path and static filename
        scrapelinksmain(
            project_folder=links_folder,  # Use the existing 'links' folder
            base_url=base_url,
            link_selector=link_selector,
            pagination_url=pagination_url,
            next_button_selector=next_button_selector,
            max_pages=max_pages,
            scroll_to_load_more=scroll_to_load_more,
            load_more_button_selector=load_more_button_selector
        )
        
        # Static filename for links.csv (since you're using a fixed filename)
        save_path = os.path.join(links_folder, "links.csv")
        st.success(f"Links scraped and saved to: {save_path}")

# ---------------------------- PDF Scraper Tab ----------------------------
with tab2:
    st.header("PDF Scraper")
    
    # Automatically use the links folder of the selected project/subproject
    if st.session_state.current_project and st.session_state.current_subproject:
        # Path to the links folder in the current project/subproject
        links_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "links")
        
        # List available CSV files in the links folder
        available_csv_files = [f for f in os.listdir(links_folder) if f.endswith('.csv')]
        
        # If CSV files exist, allow selection
        if available_csv_files:
            selected_csv = st.selectbox("Select CSV File", available_csv_files, key="pdf_scraper_csv_select")
            
            # Set the output folder for PDFs
            pdf_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "pdfs")
        
            if st.button("Run PDF Downloader", key="run_pdf_scraper"):
                # Full path to the selected CSV
                csv_path = os.path.join(links_folder, selected_csv)
                
                # Run PDF scraper
                pdfscrappermain(csv_path, pdf_folder)
                st.success("PDF scraping completed.")
        else:
            st.warning("No CSV files found in the links folder. Please scrape links first.")
    else:
        st.warning("Please select a project and subproject first.")

# ---------------------------- WARC Scraper Tab ----------------------------
with tab3:
    st.header("WARC Scraper")
    
    # Automatically use the links folder of the selected project/subproject
    if st.session_state.current_project and st.session_state.current_subproject:
        # Path to the links folder in the current project/subproject
        links_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "links")
        
        # List available CSV files in the links folder
        available_csv_files = [f for f in os.listdir(links_folder) if f.endswith('.csv')]
        
        # If CSV files exist, allow selection
        if available_csv_files:
            selected_csv = st.selectbox("Select CSV File", available_csv_files, key="warc_scraper_csv_select")
            
            # Set the output folder for WARCs
            warc_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "warcs")
        
            if st.button("Run WARC Downloader", key="run_warc_scraper"):
                # Full path to the selected CSV
                csv_path = os.path.join(links_folder, selected_csv)
                
                # Run WARC scraper
                warcscrappermain(csv_path, warc_folder)
                st.success("WARC scraping completed.")
        else:
            st.warning("No CSV files found in the links folder. Please scrape links first.")
    else:
        st.warning("Please select a project and subproject first.")

# ---------------------------- Token Estimator Tab ----------------------------
with tab4:
    st.header("Token Estimator")
    
    # Check if the current project and subproject are selected
    if st.session_state.current_project and st.session_state.current_subproject:
        # Path to the PDFs and WARCs folder in the current project/subproject
        pdf_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "pdfs", "scraped-pdfs")
        warc_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "warcs", "scraped-warcs")
        
        # Check if PDF and WARC folders exist and contain files
        pdf_files_exist = os.path.exists(pdf_folder) and any(f.endswith(".pdf") for f in os.listdir(pdf_folder))
        warc_files_exist = os.path.exists(warc_folder) and any(f.endswith(".warc") for f in os.listdir(warc_folder))
        
        if pdf_files_exist or warc_files_exist:
            # File Type Selection (PDF or WARC)
            file_type = st.selectbox("Select File Type for Token Estimation", ["PDF", "WARC"], key="token_est_file_type")
            
            if file_type == "PDF" and pdf_files_exist:
                if st.button("Estimate Tokens for PDFs", key="estimate_pdf_tokens"):
                    # Estimate tokens for PDF files in the "scraped-pdfs" folder
                    total_tokens, num_files = estimate_tokens_in_pdf(pdf_folder)
                    st.success(f"Total tokens in PDF files: {total_tokens}. Estimated from {num_files} PDF files.")
                
            elif file_type == "WARC" and warc_files_exist:
                if st.button("Estimate Tokens for WARCs", key="estimate_warc_tokens"):
                    # Estimate tokens for WARC files in the "scraped-warcs" folder
                    total_tokens, num_files = estimate_tokens_in_warc(warc_folder)
                    st.success(f"Total tokens in WARC files: {total_tokens}. Estimated from {num_files} WARC files.")
                
            if not pdf_files_exist and file_type == "PDF":
                st.warning(f"No PDFs found in {pdf_folder}. Please scrape PDFs first.")
            
            if not warc_files_exist and file_type == "WARC":
                st.warning(f"No WARC files found in {warc_folder}. Please scrape WARCs first.")
            
        else:
            st.warning("No PDF or WARC files found. Please scrape data first.")
    else:
        st.warning("Please select a project and subproject first.")

# ---------------------------- Compress Tab ----------------------------
with tab5:
    st.header("Compress Files")
    
    # Automatically use the output folders of the selected project/subproject
    if st.session_state.current_project and st.session_state.current_subproject:
        # Paths to the PDFs, WARCs, and compressed folder in the current project/subproject
        pdf_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "pdfs", "scraped-pdfs")
        warc_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "warcs", "scraped-warcs")
        compressed_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "compressed")
        
        # Check if PDF and WARC folders exist and contain files
        pdf_files_exist = os.path.exists(pdf_folder) and any(f.endswith(".pdf") for f in os.listdir(pdf_folder))
        warc_files_exist = os.path.exists(warc_folder) and any(f.endswith(".warc") for f in os.listdir(warc_folder))
        
        if pdf_files_exist or warc_files_exist:
            # File Type Selection (PDF or WARC)
            file_type = st.selectbox("Select File Type for Compression", ["PDF", "WARC"], key="compress_file_type")
            
            if file_type == "PDF" and pdf_files_exist:
                description = st.text_input("Enter Description for PDF ZIP", "")
                if st.button("Compress PDFs to ZIP"):
                    if description:
                        # Compress PDFs to ZIP
                        zip_path = compress_pdfs_to_zip(pdf_folder, description, compressed_folder)
                        st.success(f"ZIP archive created at: {zip_path}")
                    else:
                        st.warning("Please enter a description for the ZIP file.")
            
            elif file_type == "WARC" and warc_files_exist:
                description = st.text_input("Enter Description for WARC.GZ File", "")
                if st.button("Compress WARCs to WARC.GZ"):
                    if description:
                        # Compress WARCs to WARC.GZ
                        gz_path = compress_warcs_to_warcgz(warc_folder, description, compressed_folder)
                        st.success(f"Combined WARC.GZ file created at: {gz_path}")
                    else:
                        st.warning("Please enter a description for the WARC file.")
                
            if not pdf_files_exist and file_type == "PDF":
                st.warning("No PDFs found in the folder. Please scrape PDFs first.")
            
            if not warc_files_exist and file_type == "WARC":
                st.warning("No WARCs found in the folder. Please scrape WARCs first.")
                
        else:
            st.warning("No PDF or WARC files found. Please scrape data first.")
    else:
        st.warning("Please select a project and subproject first.")

# # ---------------------------- Hugging Face Model Tab ----------------------------
with tab6:
    st.header("https://huggingface.co/spaces/gmonsoon/gemma2-9b-cpt-sahabatai-v1-instruct")

# ---------------------------- Dashboard Tab ----------------------------
with tab7:
    st.header("Dashboard - Project Insights")

    output_root = "output"

    # Get project statistics
    stats = get_project_stats(output_root)

    # Section: Project Overview
    st.subheader("Project Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Projects", stats["total_projects"])
    with col2:
        st.metric("Total Subprojects", stats["total_subprojects"])

    # Section: File Counts and Sizes
    st.subheader("File Counts and Sizes")
    
    col3, col4 = st.columns(2)
    with col3:
        st.metric("PDF Files", f"{stats['pdf_count']} files")
        st.metric("WARC Files", f"{stats['warc_count']} files")
    with col4:
        st.metric("Links (CSV Files)", f"{stats['link_count']} files")
        st.metric("Token Files", f"{stats['token_count']} files")
    
    col5, col6 = st.columns(2)
    with col5:
        st.metric("PDF Size", f"{stats['pdf_size']:.2f} MB")
    with col6:
        st.metric("WARC Size", f"{stats['warc_size']:.2f} MB")

    st.write(f"**Total Data Size**: {stats['total_size']:.2f} MB")

    # Section: Detailed Table for Projects and Subprojects
    st.subheader("Project and Subproject Details")

    # Get detailed project and subproject data for the table
    table_data = get_detailed_project_data(output_root)

    # Convert the table data into a DataFrame
    columns = [
        "Project Name", "Subproject Name", "File Type", 
        "Total Size (MB)", "Token Count"
    ]
    
    df = pd.DataFrame(table_data, columns=columns)

    # Set the project as the index
    df.set_index(["Project Name", "Subproject Name"], inplace=True)

    # Display the table
    st.table(df)