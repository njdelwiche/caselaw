import os
import sys
import requests
import time
import pandas as pd
from datetime import datetime
import re

api_key = os.environ.get("caselaw_api")

headers = {
    "Authorization": f"Token {api_key}"
}

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python api.py cases.txt")
    try:
        with open(sys.argv[1]) as f:
            lines = f.read()
    except:
        sys.exit("Usage: requires existing text file.")
    cases = lines.splitlines()[:4]
    download_pdfs(*cases)


def download_pdfs(*args):
    '''
    Downloads as PDF the first result in any number of
    case queries. Tracks cases that did not yield results
    and exports a CSV log.  
    '''

    logging  = pd.DataFrame(columns=["Name", "Link", "Downloaded"])

    for query in args:
        url = f"https://api.case.law/v1/cases/?search={query}"
        response  = requests.get(url, headers=headers).json()
        if not response.get("results"):
            print(f"FAILED TO LOAD {query}")
            continue

        case_id = response.get("results")[0]["id"]
        uncleaned_name = response.get("results")[0]["name"]

        if not (case_id and uncleaned_name):
            logging = logging.append({"Name": query, "Link": False, "Downloaded": False}, ignore_index = True)
            print(f"FAILED TO LOAD {query}")
            continue

        case_url = f"https://api.case.law/v1/cases/{case_id}/?full_case=true&format=pdf"
        pdf = requests.get(case_url, headers=headers)
        with open(f"downloads/{clean(uncleaned_name)}.pdf", "wb") as f:
            f.write(pdf.content)
        logging = logging.append({"Name": query, "Link": response.get("results")[0]["url"], "Downloaded": True}, ignore_index = True)
        print(f"SUCCESSFULLY DOWNLOADED {query}")

    time_log = datetime.now().strftime("%Y-%m-%d-%H-%M")
    logging.to_csv(f"logs/Searchlog_{time_log}.csv")


def clean(text):
    '''
    Ensures the case title is a viable filename.
    '''

    pdf_name = re.sub(r'[\\\\/*?:"<>\'’.,|;]', "", text)
    if len(pdf_name) > 225:
        pdf_name = pdf_name[:225]
    return pdf_name


if __name__ == "__main__":
    main()