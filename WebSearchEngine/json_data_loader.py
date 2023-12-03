import gzip
import json
import os
from glob import glob
   

def delete_file(file_path):
    """Delete a file."""
    print(f"Deleting {file_path}")
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"Error: {file_path} : {e.strerror}")

def delete_directory_if_empty(directory):
    """Delete a directory only if it is empty."""
    try:
        os.rmdir(directory)
    except OSError as e:
        # Directory not empty or other error
        pass

def load_data_to_index(index, info_parser, dir_path):
    """Load data from json.gz files to the index and delete the files after processing."""
    # Iterate over all the subdirectories in the given directory
    for chunk_dir in glob(os.path.join(dir_path, 'DATA_CHUNK_*')):
        for folder_dir in glob(os.path.join(chunk_dir, 'DATA_FOLDER_*')):
            # Find all json.gz files in the current folder
            for file_path in glob(os.path.join(folder_dir, '*.json.gz')):
                # Decompress and read the file
                with gzip.open(file_path, 'rt', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Process each URL and HTML content in the file
                for url, html in data.items():
                    print(f"Processing {url}")
                    info = info_parser.get_info_from_html(url, html)
                    index.add(**info)

                # Delete the processed file
                delete_file(file_path)

            # Attempt to delete the folder if it is empty
            delete_directory_if_empty(folder_dir)

        # Attempt to delete the chunk directory if it is empty
        delete_directory_if_empty(chunk_dir)


# def find_json_gz_files(root_dir):
#     """Find all json.gz files in the given root directory and its subdirectories."""
#     file_paths = []
#     for subdir, dirs, files in os.walk(root_dir):
#         for file in files:
#             if file.endswith('.json.gz'):
#                 file_paths.append(os.path.join(subdir, file))
#     return file_paths

# def load_data_to_index(index, info_parser, dir_path):
#     """Load data from json.gz files to the index."""
#     file_paths = find_json_gz_files(dir_path)
#     for file_path in file_paths:
#         with gzip.open(file_path, 'rt', encoding='utf-8') as file:
#             data = json.load(file)
#         for url, html in data.items():
#             info = info_parser.get_info_from_html(url, html)
#             index.add(**info)
#         delete_file(file_path)


if __name__ == "__main__":
    # from .index import WebIndex
    # from .infoparser import InfoParser

    # index = WebIndex("./Search_indecies/test_index", name="whtever")
    # info_parser = InfoParser()
    # load_data_to_index(index=index, info_parser=info_parser, dir_path="/home/martin/Uni/semester05/AI_and_the_web/search_engine_ai-web/crawler_content")
    
    pass
