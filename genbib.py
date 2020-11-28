# Generate a bibliography from each cite in an asciidoc source document
import json
import sys
import re
import requests

# The output file to be included in the corresponding section of the source document
biblioFile = "bibliography.adoc"

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

# Ask Zotero for the formatted bibliography item
def find_citekey(citekey):

    # Replace the citekey in the template, to build the actual request
    payload = payloadTemplate.replace("citekey", citekey)
    print(payload)

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


# Check if we have received the name of the source file
# Otherwise print usage
if len(sys.argv) < 2:
    print("Need name of asciidoc file")
    exit(1)

inputFile = sys.argv[1]

# Read the input file in memory (should not be a problem with normal documents)
with open(inputFile, encoding='utf-8-sig') as f:
    sourceDocument = f.read()

# Compile the regex string search with the format of the citekey: <<citekey>>
p = re.compile('<<(.+?)>>')

# Find all citeKeys in the source document
# Some of them will be figures or tables, but it does not matter
citeKeys = p.findall(sourceDocument)

# Open the result file
with open(biblioFile, "w", encoding='utf-8-sig') as f:

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
        biblio_item = biblio_item.replace("[1]", "")

        # Write the line to the file
        f.write(prefix + biblio_item)



