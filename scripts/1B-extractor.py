#!/usr/bin/env python3
import zipfile
import os
import logging
from config import EXTRACTED_LOCATION
from config import ZIPPED_LOCATION


print (EXTRACTED_LOCATION)
print (ZIPPED_LOCATION)

REQUIRED_CONTENTS = ['files/', 'images/', 'LICENSE.txt', 'README.txt']

# --- Logging Configuration ---
logging.basicConfig(
    filename='extractor.log',
    filemode='a',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)

def zipread(dirpathtozip):
    try:
        with zipfile.ZipFile(dirpathtozip) as exampleZip:
            ziplist = exampleZip.namelist()
            print("\nZIP FILE CONTENTS:")
            for i in ziplist:
                print(i)
            return ziplist
    except Exception as e:
        print (e)
        logging.error(f"Failed to read zip file {dirpathtozip}: {e}")
        raise

def has_required_contents(ziplist):
    zip_contents = set(ziplist)
    required = set(REQUIRED_CONTENTS)
    return required.issubset(zip_contents)

def zipextract(dirpathtozip, filenameofzip):
    dirtomake = ((filenameofzip.split('.zip'))[0]).replace(" ", "_")
    destination = os.path.join(EXTRACTED_LOCATION, dirtomake)

    if os.path.exists(destination):
        logging.info(f"Destination {destination} already exists. Skipping extraction.")
        print(f"Destination already exists: {destination}. Skipping.")
        return

    try:
        with zipfile.ZipFile(dirpathtozip) as exampleZip:
            os.makedirs(destination, exist_ok=True)
            exampleZip.extractall(destination)
            logging.info(f"Successfully extracted {filenameofzip} to {destination}")
            print(f"Extracted to: {destination}")
    except Exception as e:
        print (e)
        logging.error(f"Failed to extract {filenameofzip} to {destination}: {e}")
        raise

# --- Main Execution ---
def main():
    print(EXTRACTED_LOCATION)
    print(ZIPPED_LOCATION)
    for folderName, subfolders, filenames in os.walk(ZIPPED_LOCATION):
        print('FOLDER: ' + folderName)
        for subfolder in subfolders:
            print('Subfolder of ' + folderName + ': ' + subfolder)
        for filename in filenames:
            print('FILE INSIDE: ' + folderName + ' : ' + filename)
            if filename.endswith('.zip'):
                dirpath = os.path.join(ZIPPED_LOCATION, filename)
                try:
                    zip_contents = zipread(dirpath)
                    if has_required_contents(zip_contents):
                        print("All required contents found. Extracting...")
                        try:
                            zipextract(dirpath, filename)
                        except Exception as e:
                            print(f"Extraction error: {e}")
                    else:
                        print("Required contents missing. Skipping extraction.")
                        logging.warning(f"Zip file {filename} skipped due to missing required contents.")
                except Exception as e:
                    print(f"Zip read error: {e}")
        print(" ")

if __name__ == "__main__":
    main()
