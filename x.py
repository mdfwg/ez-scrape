import os
import streamlit as st
import logging
import pandas as pd

from helper_functions.link_scrapper import scrapelinksmain
from helper_functions.warc_scraper import warcscrappermain
from helper_functions.pdf_scraper import pdfscrappermain
from helper_functions.token_est import estimate_tokens_in_pdf, estimate_tokens_in_warc
from helper_functions.compress_file import compress_pdfs_to_zip, compress_warcs_to_warcgz
from helper_functions.dashboard import get_project_stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.title("Scrape Automation and Token Estimator")

output_root = "output"
os.makedirs(output_root, exist_ok=True)

projects = [project for project in os.listdir(output_root) if os.path.isdir(os.path.join(output_root, project))]

with st.sidebar:
    st.header("Project Management")

    if 'creating_project' not in st.session_state:
        st.session_state.creating_project = False
    if 'creating_subproject' not in st.session_state:
        st.session_state.creating_subproject = False
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'current_subproject' not in st.session_state:
        st.session_state.current_subproject = None

    project_name = st.selectbox("Select Project", ["--Select a Project--"] + projects)

    if project_name != "--Select a Project--":
        if st.button("Confirm Project Selection"):
            st.session_state.current_project = project_name
            st.success(f"Project '{project_name}' selected.")

    if not st.session_state.creating_project:
        if st.button("Add New Project"):
            st.session_state.creating_project = True

    if st.session_state.creating_project:
        new_project_name = st.text_input("Enter New Project Name")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Project"):
                if new_project_name and new_project_name not in projects:
                    try:
                        os.makedirs(os.path.join(output_root, new_project_name), exist_ok=True)
                        st.success(f"Project '{new_project_name}' created successfully.")
                        st.session_state.creating_project = False
                        projects = [project for project in os.listdir(output_root) if os.path.isdir(os.path.join(output_root, project))]
                    except Exception as e:
                        st.error(f"Error creating project: {e}")
        with col2:
            if st.button("Cancel"):
                st.session_state.creating_project = False

    subprojects = []
    if st.session_state.current_project:
        try:
            subprojects = [subproject for subproject in os.listdir(os.path.join(output_root, st.session_state.current_project)) if os.path.isdir(os.path.join(output_root, st.session_state.current_project, subproject))]
        except Exception as e:
            st.error(f"Error reading subprojects: {e}")

    if st.session_state.current_project:
        subproject_name = st.selectbox("Select Subproject", ["--Select a Subproject--"] + subprojects)

        if subproject_name != "--Select a Subproject--":
            if st.button("Confirm Subproject Selection"):
                st.session_state.current_subproject = subproject_name
                st.success(f"Subproject '{subproject_name}' selected.")

        if not st.session_state.creating_subproject:
            if st.button("Add New Subproject"):
                st.session_state.creating_subproject = True

        if st.session_state.creating_subproject:
            new_subproject_name = st.text_input("Enter New Subproject Name")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Subproject"):
                    if new_subproject_name and new_subproject_name not in subprojects:
                        try:
                            subproject_path = os.path.join(output_root, st.session_state.current_project, new_subproject_name)
                            os.makedirs(subproject_path, exist_ok=True)
                            for subdir in ["pdfs", "links", "warcs", "tokens-counted"]:
                                os.makedirs(os.path.join(subproject_path, subdir), exist_ok=True)
                            st.success(f"Subproject '{new_subproject_name}' created successfully.")
                            st.session_state.creating_subproject = False
                        except Exception as e:
                            st.error(f"Error creating subproject: {e}")
            with col2:
                if st.button("Cancel Subproject"):
                    st.session_state.creating_subproject = False

    st.divider()
    st.write("**Current Selections:**")
    st.write(f"Project: {st.session_state.current_project or 'None'}")
    st.write(f"Subproject: {st.session_state.current_subproject or 'None'}")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Link Scraper", "PDF Scraper", "WARC Scraper", "Token Estimator", "Compress", "Sahabat-AI", "Dashboard"])

with tab1:
    st.header("Link Scraper")
    base_url = st.text_input("Base URL", "")
    link_selector = st.text_input("Link Selector (CSS)", "")
    pagination_url = st.text_input("Pagination URL (optional)", "")
    next_button_selector = st.text_input("Next Button Selector (optional)", "")
    max_pages = st.number_input("Max Pages", min_value=1, value=1)

    if st.session_state.current_project and st.session_state.current_subproject:
        links_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "links")

    if st.button("Run Link Scraper"):
        scrapelinksmain(
            project_folder=links_folder,
            base_url=base_url,
            link_selector=link_selector,
            pagination_url=pagination_url,
            next_button_selector=next_button_selector,
            max_pages=max_pages,
        )
        save_path = os.path.join(links_folder, "links.csv")
        st.success(f"Links scraped and saved to: {save_path}")

with tab2:
    st.header("PDF Scraper")
    if st.session_state.current_project and st.session_state.current_subproject:
        links_folder = "links"
        pdfs_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "pdfs")

    if st.button("Run PDF Scraper"):
        if os.path.exists(os.path.join(links_folder, "links.csv")):
            pdfscrappermain(links_folder=links_folder, pdfs_folder=pdfs_folder)
            st.success(f"PDFs downloaded to: {pdfs_folder}")
        else:
            st.error("Links file not found. Please run the Link Scraper first.")

with tab3:
    st.header("WARC Scraper")
    warc_url = st.text_input("WARC URL", "")
    if st.session_state.current_project and st.session_state.current_subproject:
        warc_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "warcs")

    if st.button("Run WARC Scraper"):
        if warc_url:
            warcscrappermain(warc_folder=warc_folder, warc_url=warc_url)
            st.success(f"WARCs downloaded to: {warc_folder}")
        else:
            st.error("Please enter a WARC URL.")

with tab4:
    st.header("Token Estimator")

    if st.session_state.current_project and st.session_state.current_subproject:
        pdfs_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "pdfs")
        warcs_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "warcs")
        tokens_folder = os.path.join(output_root, st.session_state.current_project, st.session_state.current_subproject, "tokens-counted")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Estimate Tokens in PDFs"):
            pdf_token_count = estimate_tokens_in_pdf(pdfs_folder, tokens_folder)
            st.success(f"Token estimation completed for PDFs. Results saved in: {tokens_folder}")

    with col2:
        if st.button("Estimate Tokens in WARCs"):
            warc_token_count = estimate_tokens_in_warc(warcs_folder, tokens_folder)
            st.success(f"Token estimation completed for WARCs. Results saved in: {tokens_folder}")

with tab5:
    st.header("Compress Files")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Compress PDFs"):
            compressed_pdf_path = compress_pdfs_to_zip(pdfs_folder)
            st.success(f"PDFs compressed into: {compressed_pdf_path}")

    with col2:
        if st.button("Compress WARCs"):
            compressed_warc_path = compress_warcs_to_warcgz(warcs_folder)
            st.success(f"WARCs compressed into: {compressed_warc_path}")

with tab6:
    st.header("Sahabat-AI")
    st.write("Future feature for integration.")

with tab7:
    st.header("Dashboard")

    if st.session_state.current_project and st.session_state.current_subproject:
        stats = get_project_stats(output_root, st.session_state.current_project, st.session_state.current_subproject)
        st.write("### Project Statistics")
        st.table(pd.DataFrame(stats))



