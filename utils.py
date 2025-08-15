import os
import subprocess
import json
import shutil
from zipfile import ZipFile

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def remove_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def zip_folder(folder_path, zip_path):
    with ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file), folder_path))

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def install_dependencies(requirements_file):
    if os.path.exists(requirements_file):
        subprocess.run(['pip', 'install', '-r', requirements_file], check=True)

def list_unnecessary_dependencies(installed_packages, used_packages):
    """Returns a list of packages that are installed but not used."""
    return [pkg for pkg in installed_packages if pkg not in used_packages]
