import os
import shutil
from contextlib import contextmanager

# Declare some constants
URL = 'https://github.com/'
REPO_SUFFIX = '/blob/master/'
ZIP_POSTFIX = '/archive/master.zip'
TMP_FOLDER = 'tmp'
EXTRACT_DESTINATION = 'extracted'
RESULT_FILE = 'result'


def get_extensions(language):
    """
    Get code file extensions for specific programming language
    """
    file_extensions = {
                        'c': ['.c'], 'c++': ['.cpp', '.cxx', '.c'], 'java': ['.java'],
                        'c#': ['.cs'], 'javascript': ['.js', '.jsx'],
                        'js': ['.js', '.jsx'], 'python': ['.py'], 'php': ['.php']
                        }
    return file_extensions.get(language.lower())


def append_report(reports_file, report):
    """
    Append single report to the common file
    """
    with open(reports_file, 'a') as f:
        f.write(report)


def build_file_url(repo, file):
    repo_paths = file.split(os.sep)[2:]
    filtered_chunks = (chunk for chunk in repo_paths if '-master' not in chunk)
    return URL + repo + REPO_SUFFIX + '/'.join(filtered_chunks)


def get_download_url(repo):
    return URL + repo + ZIP_POSTFIX


@contextmanager
def create_folder(folder):
    os.makedirs(folder, exist_ok=True)
    yield
    shutil.rmtree(folder)
