import os
import re
import requests
import zipfile
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.sax.saxutils import escape
from xml.dom.minidom import parseString
import argparse
from io import BytesIO
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_latest_kape_files(source_directory):
    try:
        url = "https://github.com/mthcht/KapeFiles/archive/refs/heads/master.zip"
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(source_directory)
            logging.info(f"Downloaded and extracted latest KAPE files to {source_directory}")
        else:
            logging.error(f"Failed to download KAPE files. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error downloading KAPE files: {e}")

def move_targets_to_kape(source_directory):
    try:
        targets_dir = os.path.join(source_directory, 'KapeFiles-master', 'Targets')
        if os.path.exists(targets_dir):
            for item in os.listdir(targets_dir):
                s = os.path.join(targets_dir, item)
                d = os.path.join(source_directory, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            shutil.rmtree(os.path.join(source_directory, 'KapeFiles-master'))
            logging.info(f"Moved Targets content to {source_directory}")
        else:
            logging.warning(f"Targets directory does not exist in {source_directory}")
    except Exception as e:
        logging.error(f"Error moving Targets content: {e}")

def extract_comments(content):
    return re.findall(r'# (.+)', content)

def replace_windows_vars_with_wildcard(path):
    pattern = re.compile(r'%[^%]+%')
    return pattern.sub('*', path)

def convert_tkape_to_xml(tkape_content, filepath):
    try:
        comments = extract_comments(tkape_content)
        targets = re.findall(r"Name: (.*?)\n\s*Category: (.*?)\n\s*Path: (.*?)\n\s*(?:Recursive: (true|false)\n)?(?:\s*FileMask: '(.*?)'\n)?(?:\s*Comment: \"(.*?)\"\n)?", tkape_content)
        root = Element('getthis', {'reportall': ''})
        output = SubElement(root, 'output', {'compression': 'fast'})

        location_text = ""
        for comment in comments:
            if "--" not in comment:
                Comment_element = Comment(escape(comment))
                root.append(Comment_element)
            #else:
            #    logging.error(f"Invalid comment containing '--': {comment}")

        for name, category, path, recursive, filemask, comment in targets:
            sample_name = escape(name.replace(' ', '_'))
            sample = SubElement(root, 'sample', {'name': sample_name})
            if path == "C:\\":
                location_text = "*"
                ntfs_find = SubElement(sample, 'ntfs_find', {'name': filemask})
            else:
                path = path.replace('C:\\', '').replace('\\', '/')
                path = replace_windows_vars_with_wildcard(path)
                location_text = "%SystemDrive%\\"
                path_match = f"{path}{filemask}".replace('//', '/').replace('/', '\\')
                ntfs_find = SubElement(sample, 'ntfs_find', {'path_match': escape(path_match)})

        location = Element('location')
        location.text = location_text
        root.insert(1, location)

        rough_string = tostring(root, 'utf-8')
        reparsed = parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {e}")
        return None

def process_directory(source_directory, target_directory):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    for root, dirs, files in os.walk(source_directory):
        for file in files:
            if file.endswith('.tkape') and not file.startswith('!'):
                source_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, source_directory)
                target_path = os.path.join(target_directory, relative_path)
                if not os.path.exists(target_path):
                    os.makedirs(target_path)
                target_file_path = os.path.join(target_path, file.replace('.tkape', '_config.xml'))

                with open(source_file_path, 'r') as f:
                    tkape_content = f.read()
                xml_output = convert_tkape_to_xml(tkape_content, source_file_path)

                if xml_output:
                    with open(target_file_path, 'w') as f:
                        f.write(xml_output)
                    logging.info(f"Successfully converted {source_file_path} to {target_file_path}")
                else:
                    logging.error(f"Failed to convert {source_file_path} due to XML formatting issues.")

if __name__ == "__main__":
    ascii_art = """

██╗  ██╗ █████╗ ██████╗ ███████╗██████╗  ██████╗ ██████╗  ██████╗
██║ ██╔╝██╔══██╗██╔══██╗██╔════╝╚════██╗██╔═══██╗██╔══██╗██╔════╝
█████╔╝ ███████║██████╔╝█████╗   █████╔╝██║   ██║██████╔╝██║     
██╔═██╗ ██╔══██║██╔═══╝ ██╔══╝  ██╔═══╝ ██║   ██║██╔══██╗██║     
██║  ██╗██║  ██║██║     ███████╗███████╗╚██████╔╝██║  ██║╚██████╗
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝                                                      
by @mthcht

    """
    print(ascii_art)
    parser = argparse.ArgumentParser(description='Process TKAPE files and convert them to XML.')
    parser.add_argument('--update', action='store_true', help='Download the latest KAPE files.')
    parser.add_argument('--source', type=str, default='kape', help='Source directory for KAPE files.')
    parser.add_argument('--target', type=str, default='orc', help='Target directory for output XML files.')
    args = parser.parse_args()

    if not args.update and not os.path.exists(args.source):
        os.makedirs(args.source)
    if not args.update and not os.path.exists(args.target):
        os.makedirs(args.target)

    if args.update or not os.listdir(args.source):
        download_latest_kape_files(args.source)
        move_targets_to_kape(args.source)

    process_directory(args.source, args.target)