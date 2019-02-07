# -*- coding: utf-8 -*-
#!/usr/bin/python

from __future__ import print_function
import os
import sys
import math
import getopt
import requests
from tqdm import *
from config import BASE_URL, PRODUCTS_ENDPOINT, URL_BOOK_TYPES_ENDPOINT, URL_BOOK_ENDPOINT
from user import User


#TODO: I should do a function that his only purpose is to request and return data

def get_books(user, offset=0, limit=10):
    """
        Request all your books, return json with info of all your books
        Params
        ...
        header : str
        offset : int
        limit : int
            how many book wanna get by request
    """
    # TODO: given x time jwt expired and should refresh the header, user.refresh_header()
    
    url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
    r = requests.get(url, headers=user.get_header())
    data = r.json().get('data', [])
    
    print("You have {} books".format(str(r.json()['count'])))
    
    for i in range(r.json()['count'] // limit):
        offset += limit
        url = BASE_URL+PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
        print(url)
        r = requests.get(url, headers=user.get_header())
        data += r.json().get('data', [])
    return data


def get_url_book(user, book_id, format="pdf"):
    """
        Return url of the book to download
    """
    
    url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book_id, format=format)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200: # success
        return r.json().get('data', "")

    elif r.status_code == 401: # jwt expired 
        user.refresh_header() # refresh token 
        get_url_book(user, book_id, format)  # call recursive 
    
    print("ERROR (please copy and paste in the issue)")
    print(r.json())
    print(r.status_code)
    return ""


def get_book_file_types(user, book_id):
    """
        Return a list with file types of a book
    """

    url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book_id)
    r = requests.get(url, headers=user.get_header())

    if  (r.status_code == 200): # success
        return r.json()['data'][0].get("fileTypes", [])
    
    elif (r.status_code == 401): # jwt expired 
        user.refresh_header() # refresh token 
        get_book_file_types(user, book_id, format)  # call recursive 
    
    print("ERROR (please copy and paste in the issue)")
    print(r.json())
    print(r.status_code)
    return []


# TODO: i'd like that this functions be async and download faster
def download_book(filename, url):
    """
        Download your book
    """
    print("Starting to download " + filename)

    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(response.content)
        else:
            total = int(total)
            # TODO: read more about tqdm
            for chunk in tqdm(r.iter_content(chunk_size=1024), total=math.ceil(total//1024), unit='KB', unit_scale=True):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
            print("Finished " + filename)


def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email = None
    password = None
    root_directory = 'media' 
    book_file_types = []  # pdf, mobi, epub, code
    errorMessage = 'Usage: downloader.py -e <email> -p <password> [-d <directory> -b <book file types>]'

    # get the command line arguments/options
    try:
        opts, args = getopt.getopt(
            argv, "e:p:d:b:", ["email=", "pass=", "directory=", "books="])
    except getopt.GetoptError:
        print(errorMessage)
        sys.exit(2)

    # hold the values of the command line options
    for opt, arg in opts:
        if opt in ('-e', '--email'):
            email = arg
        elif opt in ('-p', '--pass'):
            password = arg
        elif opt in ('-d', '--directory'):
            root_directory = os.path.expanduser(
                arg) if '~' in arg else os.path.abspath(arg)
        elif opt in ('-b', '--books'):
            book_file_types = arg.split(",")

    # do we have the minimum required info?
    if not email or not password:
        print(errorMessage)
        sys.exit(2)

    # check if not exists dir and create
    if not os.path.exists(root_directory):
        try:
            os.makedirs(root_directory)
        except Exception as e:
            print(e)
            sys.exit(2)

    # create user with his properly header
    user = User(email, password)

    # get all your books
    books = get_books(user)
    for book in books:
        # get the diferent file type of current book
        file_types = get_book_file_types(user, book['productId'])
        for file_type in file_types:
            if file_type in book_file_types:  # check if the file type entered is available by the current book
                filename = "{path}/{name}.{fformat}".format(
                    path=root_directory, name=book['productName'].replace(" ", "_"), fformat=file_type)
                # get url of the book to download
                url = get_url_book(user, book['productId'], file_type)
                download_book(filename, url)


if __name__ == "__main__":
    main(sys.argv[1:])
