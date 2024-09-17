#!/usr/bin/env python3

''' miles.py - Web crawler to download files in parallel. '''

from typing import Iterator, Optional

import os
import concurrent.futures
import itertools
import re
import sys
import tempfile
import time
import urllib.parse

import requests

# Constants

FILE_REGEX = {
    'jpg': [r'<i.*src="?([^\" ]+.jpg)', r'<a.*href="?([^\" ]+.jpg)'],  # TODO
    'mp3': [r'<a.*src="?([^\" ]+.mp3)', r'<a.*href="?([^\" ]+.mp3)'],  # TODO
    'pdf': [r'<a.*href="?([^\" ]+.pdf)'],  # TODO
    'png': [r'<i.*src="?([^\" ]+.png)', r'<a.*href="?([^\" ]+.png)'],  # TODO
}

MEGABYTES   = 1<<20
DESTINATION = '.'
CPUS        = 1

# Functions

def usage(exit_status: int=0) -> None:
    ''' Print usage message and exit. '''
    print(f'''Usage: miles.py [-d DESTINATION -n CPUS -f FILETYPES] URL

Crawl the given URL for the specified FILETYPES and download the files to the
DESTINATION folder using CPUS cores in parallel.

    -d DESTINATION      Save the files to this folder (default: {DESTINATION})
    -n CPUS             Number of CPU cores to use (default: {CPUS})
    -f FILETYPES        List of file types: jpg, mp3, pdf, png (default: all)

Multiple FILETYPES can be specified in the following manner:

    -f jpg,png
    -f jpg -f png''', file=sys.stderr)
    sys.exit(exit_status)

def resolve_url(base: str, url: str) -> str:
    ''' Resolve absolute url from base url and possibly relative url.

    >>> base = 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/'
    >>> resolve_url(base, 'static/img/ostep.jpg')
    'https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/static/img/ostep.jpg'

    >>> resolve_url(base, 'https://automatetheboringstuff.com/')
    'https://automatetheboringstuff.com/'
    '''
    
    if "://" in url:
        absolute = url
    else:
        absolute = urllib.parse.urljoin(base, url)
    
    return absolute

def extract_urls(url: str, file_types: list[str]) -> Iterator[str]:
    ''' Extract urls of specified file_types from url.

    >>> url = 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/'
    >>> extract_urls(url, ['jpg']) # doctest: +ELLIPSIS
    <generator object extract_urls at ...>

    >>> len(list(extract_urls(url, ['jpg'])))
    2
    '''
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return
    
    for ftype in file_types:
        patterns = FILE_REGEX.get(ftype, [])
        for pattern in patterns:
            tmatches = re.findall(pattern, response.text)
            for tmatch in tmatches:
                yield resolve_url(url, tmatch)

def download_url(url: str, destination: str=DESTINATION) -> Optional[str]:
    ''' Download url to destination folder.

    >>> url = 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/static/img/ostep.jpg'
    >>> destination = tempfile.TemporaryDirectory()

    >>> path = download_url(url, destination.name)
    Downloading https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/static/img/ostep.jpg...

    >>> path # doctest: +ELLIPSIS
    '/tmp/.../ostep.jpg'

    >>> os.stat(path).st_size
    53696

    >>> destination.cleanup()
    '''
    print(f"Downloading {url}...")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    name = os.path.basename(url)
    npath = os.path.join(destination, name)

    try:
        with open(npath, "wb") as destfile:
            destfile.write(response.content)
    except Exception as e:
        return None

    return npath

def crawl(url: str, file_types: list[str], destination: str=DESTINATION, cpus: int=CPUS) -> None:
    ''' Crawl the url for the specified file type(s) and download all found
    files to destination folder.

    >>> url = 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/'
    >>> destination = tempfile.TemporaryDirectory()
    >>> crawl(url, ['jpg'], destination.name) # doctest: +ELLIPSIS
    Files Downloaded: 2
    Bytes Downloaded: 0.07 MB
    Elapsed Time:     ... s
    Bandwidth:        0... MB/s

    >>> destination.cleanup()
    '''
    if not file_types:
        file_types.extend(['jpg', 'mp3', 'png', 'pdf'])
    
    start_time = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpus) as executor:
        urls    = extract_urls(url, file_types)
        dsts    = itertools.repeat(destination)
        files   = [f for f in executor.map(download_url, urls, dsts) if f]

    dfiles      = len(files)
    dbytes      = sum(os.stat(path).st_size for path in files)

    elapsed_time = time.time() - start_time
    print(f'Files Downloaded: {dfiles}')
    print(f'Bytes Downloaded: {dbytes / MEGABYTES:.02f} MB')
    print(f'Elapsed Time:     {elapsed_time:.02f} s')
    print(f'Bandwidth:        {(dbytes / MEGABYTES) / elapsed_time:.02f} MB/s')


# Main Execution

def main(arguments=sys.argv[1:]) -> None:
    ''' Process command line arguments, crawl URL for specified FILETYPES,
    download files to DESTINATION folder using CPUS cores.

    >>> url = 'https://www3.nd.edu/~pbui/teaching/cse.20289.sp24/'
    >>> destination = tempfile.TemporaryDirectory()
    >>> main(f'-d {destination.name} -f jpg {url}'.split()) # doctest: +ELLIPSIS
    Files Downloaded: 2
    Bytes Downloaded: 0.07 MB
    Elapsed Time:     0... s
    Bandwidth:        0... MB/s

    >>> destination.cleanup()
    '''
    file_types  = []
    destination = DESTINATION
    cpus        = CPUS
    url         = ""

    while arguments:
        argument = arguments.pop(0)
        if   argument == '-h':
            usage(0)
        elif argument == '-d':
            destination = arguments.pop(0)
        elif argument == '-n':
            cpus = int(arguments.pop(0))
        elif argument == '-f':
            ftype = arguments.pop(0)
            if ',' in ftype:
                file_types.extend(ftype.split(','))
            else:
                file_types.append(ftype)
        elif argument.startswith('-'):
            usage(1)
        else:
            url = argument

    if not os.path.exists(destination):
        os.makedirs(destination)

    if len(url) == 0:
        usage(1)

    crawl(url, file_types, destination, cpus)
    
if __name__ == '__main__':
    main()
