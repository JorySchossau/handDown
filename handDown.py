## handDown.py by Jory Schossau
## Requires: pip install docopt urllib3 beautifulsoup4
## Assumes python >= 3.5.2 but may work python >= 3.0.0

"""
Usage:
  handDown.py [(--user=NETID | --list=FILE)] [--filter=FILTER] [--out=DIR] [--recent]
  handDown.py [-h]

Downloads files from HandIn filtering by netids and filename fuzzy matching.
Also lists by assignment who did not submit anything, and provides an
email formatted version of that list for emailing.

Options:
-h, --help          Show this message
-u, --user=NETID    Downloads files only for a single student
-l, --list=FILE     Downloads files for many students, netids in file (instead of -u)
-f, --filter=FILTER Filename filter. la,pro matches lab01.py, lab02.py, proj01.py
-o, --out=DIR       Download files to directory (default: ./downloaded)
-r, --recent        For each request, only downloads the latest version

Examples:
    handDown.py --user mynetid --filter 01 --out week1 -r
    This would download all first week ('01') files (of the latest revision)
    for the user mynetid into a directory week1.

    handDown.py --list mysec730NetIDsFile --filter lab
    This would download all labs for all students listed in the file
    mysec730NetIDsFile, and download all versions of the labs submitted.

    handDown.py --list mysec730NetIDsFile --filter pro,lab
    Same as the previous example, but downloads all projects and labs.
"""
import imp ## to test imports
import sys ## exit
import subprocess ## using pip
installCMDString = "pip install "
def testForModuleAndBuildInstallString(moduleName):
    global installCMDString
    try:
        imp.find_module(moduleName)
    except ImportError:
        installCMDString += moduleName+' '
testForModuleAndBuildInstallString('docopt')
testForModuleAndBuildInstallString('urllib3')
try:
    imp.find_module('BeautifulSoup')
except ImportError:
    try:
        imp.find_module('bs4')
    except ImportError:
        installCMDString += 'beautifulsoup4 bs4'
if (len(installCMDString)>14):
    print("It appears you need to install a few modules like so:")
    print(installCMDString)
    print("")
    choice='none'
    while(choice not in set(['yes','y','n','no',''])):
        choice = input("Should I install them with pip? [y/N]: ").lower()
        if choice in set(['yes','y']):
            subprocess.run(installCMDString, shell=True, check=True)
        sys.exit(0)

from docopt import docopt
import urllib3
import getpass
import re
import os
try: 
  from BeautifulSoup import BeautifulSoup
except ImportError:
  from bs4 import BeautifulSoup

username=''
password=''
handinURL='secure.cse.msu.edu/handin/admin/handin.php3'
handinResultsURL='http://secure.cse.msu.edu/handin/admin/handin_results.php3?Color=6699FF&AssignID=ALL_ALL&TrackID=' ## all but TrackID value (Section)
handinDownloadURL='http://secure.cse.msu.edu/handin/admin/' ## all but viewfiles.php?......etc.
http=None
sectionIDs=[] ## will hold unique identifier strings for each section (unique to handin system)
fileIDsByStudent = {} ## fileIDs for files to download organized by student NETID {NETID:{filename:[list of urls]}
targetNetIDs = [] ## will hold students about whom we'll get data
setOfFilenamesSubmitted = set() ## holds unique set of filenames submitted that match filter (used to identify lack of submissions)
setOfFilenamesLooking = set()

## crawl the main handin page to get
## section identifiers used by handin
def parseMainPage():
    global sectionIDs
    url = handinURL
    headers = urllib3.util.make_headers(basic_auth=username+':'+password)
    r = http.request('GET', url, headers=headers)
    parsed_html = BeautifulSoup(r.data, "html.parser")
    sectionIDs = [e.get('value') for e in parsed_html.body.find('select',{'name':'TrackID'}).find_all('option')]
    r.release_conn()

## crawl the results page from handin
## (the page with all the juicy data)
def parseResultsPages(): ## parses the list of students and their file DL links
    global fileIDsByStudent, targetNetIDs
    getAllStudents = False
    if (len(targetNetIDs)==0):
        getAllStudents = True
    for eachSecID in sectionIDs:
        url = handinResultsURL+eachSecID
        headers = urllib3.util.make_headers(basic_auth=username+':'+password)
        r = http.request('GET', url, headers=headers)
        parsed_html = BeautifulSoup(r.data, "html.parser")
        table = parsed_html.body.find_all('table')[1] ## get the table of data (must assume it's the second one)
        rows = table.find_all('tr')[1:] ## skip header row but get rest
        for eachRow in rows:
            cols = eachRow.find_all('td')
            netid = cols[1].contents[0]
            href = cols[6].find_all('a')[1]['href'] ## get second link's href
            filename = cols[6].a.contents[0] ## for some reason a.contents is a list
            if (netid not in fileIDsByStudent):
                fileIDsByStudent[netid] = {}
            if (filename not in fileIDsByStudent[netid]):
                fileIDsByStudent[netid][filename] = []
            fileIDsByStudent[netid][filename].append(href)
            setOfFilenamesSubmitted.add(filename)
            if (getAllStudents == True):
                targetNetIDs.append(netid)
        r.release_conn()

## get a list of netids from a file
## which might be delimited by several variations
def parseTargetNetIDsFile(filename):
    global targetNetIDs
    netids = None
    file = open(filename, "r")
    netids = file.readlines()
    netids = [e.rstrip() for e in netids]
    netids = '\n'.join(netids)
    netids = netids.rstrip()
    targetNetIDs = re.split(',|\n|;',netids)

## parse the user string of fuzzy matching
## assignment names ex: pro,la matches proj01.py and lab01.py
def parseFilter(filterString):
    global setOfFilenamesLooking
    setOfFilenamesLooking = set(re.split(',',filterString))

## of max assignments submitted,
## see if anyone has less than that (failure to submit)
def checkForNoSubmissions():
    for eachFilename in setOfFilenamesSubmitted:
        filenameIsInteresting = False
        for eachFilenamePiece in setOfFilenamesLooking:
            if (eachFilenamePiece in eachFilename):
                filenameIsInteresting = True
                break ## break for eachFilenamePiece in setOfFilenamesLooking:
        if (len(setOfFilenamesLooking) == 0): ## if user didn't specify anything in particular
            filenameIsInteresting = True ## then assume everything is interesting
        if (filenameIsInteresting == False):
            continue ## next eachFilename
        messageEmpty = True
        nonsubmitMsg = eachFilename+' not submitted by:\n'
        emails = '('
        for eachNetID in targetNetIDs:
            if (eachNetID not in fileIDsByStudent):
                nonsubmitMsg += '  '+eachNetID+'\n'
                emails += eachNetID+'@msu.edu,'
                messageEmpty = False
            elif (eachFilename not in fileIDsByStudent[eachNetID]):
                nonsubmitMsg += '  '+eachNetID+'\n'
                emails += eachNetID+'@msu.edu,'
                messageEmpty = False
        emails = emails[:-1]+')\n'
        if (not messageEmpty):
            print(nonsubmitMsg)
            print(emails)

## performs file downloading and writing to requested dir
## scans pre-crawled data to get file URLs
def downloadRequestedFilesFromRequestedNetIDs(recentOnly=False, outDir=None):
    if (not os.path.exists(outDir)):
        os.makedirs(outDir)
    downloadCounter = 0
    for eachNetID in fileIDsByStudent:
        for eachFilename in fileIDsByStudent[eachNetID]:
            filenameIsInteresting = False
            for eachFilenamePiece in setOfFilenamesLooking:
                if (eachFilenamePiece in eachFilename):
                    filenameIsInteresting = True
                    break ## break for eachFilenamePiece in setOfFilenamesLooking:
            if (len(setOfFilenamesLooking) == 0): ## if user didn't specify anything in particular
                filenameIsInteresting = True ## then assume everything is interesting
            if (filenameIsInteresting == False):
                continue ## next eachFilename
            if (eachNetID in targetNetIDs):
                startIndex = 0
                if (recentOnly == True):
                    startIndex = len(fileIDsByStudent[eachNetID][eachFilename])-1
                for i in range(startIndex,len(fileIDsByStudent[eachNetID][eachFilename])):
                    filename = eachFilename[:-3]+'.'+eachNetID+'.'+chr(ord('a')+i)+eachFilename[-3:]
                    url = handinDownloadURL+fileIDsByStudent[eachNetID][eachFilename][i]
                    headers = urllib3.util.make_headers(basic_auth=username+':'+password)
                    r = http.request('GET', url, headers=headers)
                    with open(os.path.join(outDir,filename),"w+b") as file:
                        file.write(r.data)
                    r.release_conn()
                    downloadCounter+=1
    print('downloaded '+str(downloadCounter)+' files into '+outDir)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='handDown 0.1')
    username=input('username: ')
    password=getpass.getpass()
    http = urllib3.PoolManager() ## init web request engine
    if (arguments['--out'] ==  None):
        arguments['--out'] = './downloaded' ## default to sane
    if (arguments['--list']!=None): ## load netid(s) from file if requested
        parseTargetNetIDsFile(arguments['--list'])
    if (arguments['--user']!=None): ## load netid from the one specified
        targetNetIDs = [arguments['--user']]
    if (arguments['--filter']!=None): ## load filters from user string (ex: "pro,la" matches "proj01.py" and "lab01.py")
        parseFilter(arguments['--filter'])
    parseMainPage() ## scrape main page for section IDs used by handin
    parseResultsPages() ## scrape student data into data structure
    downloadRequestedFilesFromRequestedNetIDs(recentOnly=arguments['--recent'], outDir=arguments['--out']) ## download and save select files
    checkForNoSubmissions() ## see if anyone didn't submit ^^^ assignments
