import os
import argparse

# Recursively get all XML files in a directory, excluding the "!Disabled" directory
def get_all_xml_files(directory):
    xml_files = []
    for root, dirs, files in os.walk(directory):
        # Exclude "!Disabled" directory
        if "!Disabled" in dirs:
            dirs.remove("!Disabled")
        print(f"Checking directory: {root}")  # Debugging output
        for file in files:
            print(f"Found file: {file}")  # Debugging output
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    return xml_files

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate DFIR-ORC XML configuration.")
parser.add_argument("-d", "--directory", type=str, default="orc", help="Path to the directory containing XML files.")
args = parser.parse_args()

# Get the directory containing the XML files
config_directory = args.directory
xml_files = get_all_xml_files(config_directory)

# Check if any XML files are found
if not xml_files:
    print("No XML files found in the specified directory.")
else:
    print(f"Found {len(xml_files)} XML files.")
    for xml_file in xml_files:
        print(f"XML file: {xml_file}")

# Extract the directory name for use in the keyword
directory_name = os.path.basename(config_directory)

# Start of the XML content
xml_content = '<archive name="DFIR-ORC_{SystemType}_{FullComputerName}_Kape_Artefacts.7z" keyword="Kape_configurations" concurrency="2" repeat="Once" compression="fast" optional="yes">\n'

# Generate commands for each XML file
for xml_file in xml_files:
    # Extract the file name without the extension
    file_name = os.path.splitext(os.path.basename(xml_file))[0]
    # Create the command keyword
    keyword = f"GET_{directory_name}_{file_name}"
    
    # Generate the command
    command = f'    <command keyword="{keyword}">\n'
    command += f'        <execute name="Orc.exe" run="self:#GetThis" />\n'
    command += f'        <argument>/config={xml_file}</argument>\n'
    command += f'        <output name="{keyword}.7z" source="File" argument="/out={{FileName}}" />\n'
    command += f'        <output name="{keyword}.log" source="StdOutErr" />\n'
    xml_content += command

# End of the XML content
xml_content += '</archive>\n'

# Write the XML content to a file
with open("add_this_to_your_dfir-orc_config.xml", "w") as xml_file:
    xml_file.write(xml_content)

print("XML file 'add_this_to_your_dfir-orc_config.xml' has been created.")
