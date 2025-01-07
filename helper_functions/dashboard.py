import os

# Function to get the project statistics
def get_project_stats(output_root):
    stats = {
        "total_projects": 0,
        "total_subprojects": 0,
        "pdf_count": 0,
        "pdf_size": 0.0,
        "warc_count": 0,
        "warc_size": 0.0,
        "link_count": 0,
        "token_count": 0,
        "total_size": 0.0
    }

    # Loop through each project in the output directory
    for project in os.listdir(output_root):
        project_path = os.path.join(output_root, project)
        if os.path.isdir(project_path):
            stats["total_projects"] += 1

            # Loop through each subproject in the project
            for subproject in os.listdir(project_path):
                subproject_path = os.path.join(project_path, subproject)
                if os.path.isdir(subproject_path):
                    stats["total_subprojects"] += 1

                    # Count PDF files and their sizes
                    pdf_folder = os.path.join(subproject_path, "pdfs", "scraped-pdfs")
                    if os.path.exists(pdf_folder):
                        for pdf_file in os.listdir(pdf_folder):
                            if pdf_file.endswith(".pdf"):
                                stats["pdf_count"] += 1
                                stats["pdf_size"] += os.path.getsize(os.path.join(pdf_folder, pdf_file))

                    # Count WARC files and their sizes
                    warc_folder = os.path.join(subproject_path, "warcs", "scraped-warcs")
                    if os.path.exists(warc_folder):
                        for warc_file in os.listdir(warc_folder):
                            if warc_file.endswith(".warc"):
                                stats["warc_count"] += 1
                                stats["warc_size"] += os.path.getsize(os.path.join(warc_folder, warc_file))

                    # Count Links (CSV files) and Tokens (Text files)
                    links_folder = os.path.join(subproject_path, "links")
                    if os.path.exists(links_folder):
                        for link_file in os.listdir(links_folder):
                            if link_file.endswith(".csv"):
                                stats["link_count"] += 1

                    tokens_folder = os.path.join(subproject_path, "tokens-counted")
                    if os.path.exists(tokens_folder):
                        for token_file in os.listdir(tokens_folder):
                            if token_file.endswith(".txt"):
                                stats["token_count"] += 1

    # Convert sizes from bytes to MB or GB
    stats["pdf_size"] = stats["pdf_size"] / (1024 ** 2)  # MB
    stats["warc_size"] = stats["warc_size"] / (1024 ** 2)  # MB
    stats["total_size"] = stats["pdf_size"] + stats["warc_size"]

    return stats

# Function to get detailed project and subproject data for the table
def get_detailed_project_data(output_root):
    table_data = []

    # Loop through each project and subproject to gather details
    for project in os.listdir(output_root):
        project_path = os.path.join(output_root, project)
        if os.path.isdir(project_path):
            total_pdf_tokens = 0
            total_warc_tokens = 0
            total_size = 0.0

            # Track subproject for each project
            for subproject in os.listdir(project_path):
                subproject_path = os.path.join(project_path, subproject)
                if os.path.isdir(subproject_path):
                    pdf_folder = os.path.join(subproject_path, "pdfs", "scraped-pdfs")
                    warc_folder = os.path.join(subproject_path, "warcs", "scraped-warcs")
                    tokens_folder = os.path.join(subproject_path, "tokens-counted")

                    # Get PDF details
                    pdf_files = 0
                    pdf_size = 0.0
                    pdf_tokens = 0

                    if os.path.exists(pdf_folder):
                        for pdf_file in os.listdir(pdf_folder):
                            if pdf_file.endswith(".pdf"):
                                pdf_files += 1
                                pdf_size += os.path.getsize(os.path.join(pdf_folder, pdf_file))

                    # Get WARC details
                    warc_files = 0
                    warc_size = 0.0
                    warc_tokens = 0

                    if os.path.exists(warc_folder):
                        for warc_file in os.listdir(warc_folder):
                            if warc_file.endswith(".warc"):
                                warc_files += 1
                                warc_size += os.path.getsize(os.path.join(warc_folder, warc_file))

                    # Get token details
                    pdf_token_count = 0
                    warc_token_count = 0

                    if os.path.exists(tokens_folder):
                        for token_file in os.listdir(tokens_folder):
                            if token_file.endswith(".txt"):
                                with open(os.path.join(tokens_folder, token_file), 'r') as f:
                                    tokens = f.read().split()
                                    if "pdf" in token_file:
                                        pdf_token_count += len(tokens)
                                    elif "warc" in token_file:
                                        warc_token_count += len(tokens)

                    # Prepare data for the table
                    total_size += pdf_size + warc_size
                    total_pdf_tokens += pdf_token_count
                    total_warc_tokens += warc_token_count

                    # Add a row for PDFs if any PDF files are present
                    if pdf_files > 0:
                        table_data.append([project, subproject, "PDF", pdf_size / (1024 ** 2), pdf_token_count])

                    # Add a row for WARCs if any WARC files are present
                    if warc_files > 0:
                        table_data.append([project, subproject, "WARC", warc_size / (1024 ** 2), warc_token_count])

            # After processing subprojects, add a row with combined values for the project
            table_data.append([project, "Total", "Both", total_size / (1024 ** 2), total_pdf_tokens + total_warc_tokens])

    return table_data
