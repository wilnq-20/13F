import re   # library for regular expressions operations
from bs4 import BeautifulSoup as yum
import requests # the de facto standard for making http requests in python
import sys # used for reading command line arguments
import pandas as pd
# installed bs4 lxml for parsing xml


def main():
    # Get requested firm CIK from command line
    if len(sys.argv) > 2:
        print('Invalid number of parameters. Only enter 1 cik') # should only accept program name and company cik
        sys.exit() # exits python

    # store cik to search for in SEC EDGAR
    cik = sys.argv[1]

    # stores the search page extracted and searched by BS
    comp_soup = findfund(cik)
    #print(comp_soup.prettify()) # checking to make sure it works (can comment out)

    # start with URL of comp filing page
    # from the filings page - get the URL for the 13F documents (grabs tags for all 'documentsbutton')
    # using BS methods for searching parse trees
    comp_filing_url = 'http://www.sec.gov' + comp_soup.find('a', {'id': 'documentsbutton'})['href']

    # http request to url to get server response in r1 object
    r1 = requests.get(comp_filing_url)

    filings_soup = yum(r1.content, 'html5lib')

    # using another BS defined method and regular expression library
    file_url = ('http://www.sec.gov' + filings_soup.find('a', text=re.compile(r".*\.txt$"))['href'])

    r2 = requests.get(file_url)
    file_soup = yum(r2.content, 'lxml') # extracts .txt xml soup

    file_col = pullColumn(file_soup)
    file_rows = pullRows(file_soup, file_col)

    # combine into a data frame using python pandas
    dframe = pd.DataFrame(data = file_rows, columns = file_col)

    # convert into csv file
    dframe.to_csv(cik, index = False)
    print("File Extraction Complete")

# Search SEC database for fund 13F documents if they exist
def findfund(cik):
    # specify url of web page you want to scrape (will need to concatenate link and cik)
    comp_url = ('http://www.sec.gov/cgi-bin/browse-edgar?action='
                'getcompany&CIK=' + cik + '&type=13F&dateb=&owner=exclude&count=40')
    # send a http request to the specified url & save response from server in a response object called r
    r = requests.get(comp_url)

    # we create a beautiful soup object by passing in two args
    find_soup = yum(r.content, 'html5lib')

    # validate that company has 13f on file (is this even necessary)

    # return parsed sec search page for fund specified cik
    return find_soup

# accepts soup of txt and returns list of each column header and row
def pullColumn(text):
    all_dlabel = []
    info_array = text.find_all('infotable')

    # should we check for available info
    for info in info_array:
        dlabel = []
        for item in info.findChildren(): #findChildren() extracts a list of Tag objects that match the given criteria
            if (item.name is not None and item.string is not None):
                dlabel.append(item.name)
        if (len(dlabel) > len(all_dlabel)):
            all_dlabel = dlabel
        return all_dlabel


def pullRows(file_soup, dlabel):
    rows = []

    for row in file_soup.find_all('infoTable'): #iterate through and build list for row
        curr = []
        for column in dlabel:
            if (row.find(column) is None):
                curr.append('NA')  #no val for column, so label NA
            else:
                curr.append(row.find(column).string)
        rows.append(curr)
    return rows



if __name__ == '__main__':
    main()
