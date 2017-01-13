# handDown
Downloads files from HandIn filtering by netids and filename fuzzy matching. Also lists by assignment who did not submit anything.

Usage:
```raw
handDown.py [(--user=NETID | --list=FILE)] [--filter=FILTER] [--out=DIR] [--recent]
handDown.py [-h]
```

Downloads files from HandIn filtering by netids and filename lazy matching.
Also lists by assignment who did not submit anything, and provides an
email formatted version of that list for emailing.

Options:
```raw
-h, --help          Show this message
-u, --user=NETID    Downloads files only for a single student
-l, --list=FILE     Downloads files for many students, netids in file (instead of -u)
-f, --filter=FILTER Filename filter. la,pro matches lab01.py, lab02.py, proj01.py
-o, --out=DIR       Download files to directory (default: ./downloaded)
-r, --recent        For each request, only downloads the latest version
```

Examples:

```bash
handDown.py --user mynetid --filter 01 --out week1 -r
```    
This would download all first week ('01') files (of the latest revision)
for the user mynetid into a directory week1.

```bash
handDown.py --list mysec730NetIDsFile --filter lab
```
This would download all labs for all students listed in the file
mysec730NetIDsFile, and download all versions of the labs submitted.

```bash
handDown.py --list mysec730NetIDsFile --filter pro,lab
```
Same as the previous example, but downloads all projects and labs.
