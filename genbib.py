# Generate a bibliography from each cite in an asciidoc source document
import json
import sys
import shutil
import re
import requests
from collections import OrderedDict

# The output file to be included in the corresponding section of the source document
biblioFile = "bibliography.adoc"

# Markers for bibliography section
bibBegin = "//JRMBIB-BEGIN"
bibEnd = "//JRMBIB-END"

# The headers for the API call to Zotero
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# The payload as a template where "citekey" should be replaced by the actual citekey
payloadTemplate = """{
    "jsonrpc": "2.0",
    "method": "item.bibliography",
    "params": [
        ["citekey"],
        {"id": "http://www.zotero.org/styles/ieee"}
    ]
}"""

# Get all unique citekeys from a file
def get_all_citekeys(inputFile):

    # Read the input file in memory (should not be a problem with normal documents)
    with open(inputFile, encoding='utf-8-sig') as f:
        sourceDocument = f.read()

    # Compile the regex string search with the format of the citekey: <<citekey>>
    p = re.compile('<<(.+?)>>')

    # Find all citeKeys in the source document
    # Some of them will be figures or tables, but it does not matter
    citeKeys = p.findall(sourceDocument)
    citeKeys = list(OrderedDict.fromkeys(citeKeys))

    return citeKeys


# Ask Zotero for the formatted bibliography item
def find_citekey(citekey):

    # Replace the citekey in the template, to build the actual request
    payload = payloadTemplate.replace("citekey", citekey)

    # Ask Zotero via the local web API. Zotero must be running in the local machine
    r = requests.post('http://127.0.0.1:23119/better-bibtex/json-rpc',
        data = payload,
        headers = headers)

    # Check if we found anything
    if not r.ok:
        return None

    # Return the result field inside the JSON-RPC reply
    result = r.json()["result"]

    return result

def generate_bibliography_lines(citeKeys):

    # Initialize the bibliography list
    biblio_lines = []

    # Process each key
    for citeKey in citeKeys:

        # Get the bibliography item
        biblio_item = find_citekey(citeKey)
        if biblio_item is None:
            print(f"{citeKey}: No data available")
            continue

        # Build the prefix for Asciidoc bibliography
        prefix = f"- [[[{citeKey}]]] "

        # Strip the standard prefix from the IEE format: [1]
        biblio_item = prefix + biblio_item.replace("[1]", "")

        # Append the line
        biblio_lines.append(biblio_item)

    return biblio_lines




# Check if we have received the name of the source file
# Otherwise print usage
if len(sys.argv) < 2:
    print("Need name of asciidoc file")
    exit(1)

inputFileName = sys.argv[1]
# Check that the filename ends in "-source.asc"
if not inputFileName.endswith("-source.asc"):
    print("Name should end in -source.asc")
    exit(1)

outputFileName = inputFileName.replace("-source", "")

citeKeys = get_all_citekeys(inputFileName)
bibLines = generate_bibliography_lines(citeKeys)

insideBibSection = False

# Open input and output files
with open(outputFileName, "w", encoding='utf-8-sig') as outFile:
    with open(inputFileName, encoding='utf-8-sig') as inFile:

        # Process each line of the input file
        for line in inFile:

            # Write the line if not inside the bibliography section
            if not insideBibSection:
                outFile.write(line)

            # Check if we are entering the bibliography section
            if line.startswith(bibBegin):
                insideBibSection = True
                continue

            # Check if we are exiting the bibliography section
            if line.startswith(bibEnd):

                # Write the new bibliography lines
                for bl in bibLines:
                    outFile.write(bl)

                # Write the marker
                outFile.write(line)

                # Mark that we are exiting
                insideBibSection = False





