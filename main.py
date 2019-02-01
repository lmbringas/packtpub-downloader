# -*- coding: utf-8 -*-
#!/usr/bin/python

from __future__ import print_function
import os
import sys
import getopt
import requests
from config import BASE_URL, PRODUCTS_ENDPOINT, URL_BOOK_ENDPOINT
from user import User


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
    url = BASE_URL+PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
    r = requests.get(url, headers=user.get_header())
    data = r.json()['data']
    print("You have {} books".format(str(r.json()['count'])))
    for i in range(r.json()['count'] // limit):
        offset += limit
        url = BASE_URL+PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
        print(url)
        r = requests.get(url, headers=user.get_header())
        data += r.json()['data']
    return data


def get_url_book(user, book_id, format="pdf"):
    """
        Return url of the book to download
    """
    # TODO: i should check if exists that format, i think there is an endpoint that return formats
    # TODO: given x time jwt expired and should refresh the header, user.refresh_header()
    url = BASE_URL+URL_BOOK_ENDPOINT.format(book_id=book_id, format=format)
    r = requests.get(url, headers=user.get_header())
    try:
        return r.json()['data']
    except Exception as e: # i think this could happend if jwt expired but i should test more 
        print("Error {}".format(e))
        r = requests.get(url, headers=user.refresh_header())
        return r.json()['data']

# TODO: i'd like that this functions be async and download faster
def download_book(filename, url):
    """
        Download your book
    """
    print("Starting to download " + filename)
    # thanks to https://sumit-ghosh.com/articles/python-download-progress-bar/
    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            # i don't like how progress bar works so i should search another solution
            for chunk in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                if chunk:  # filter out keep-alive new chunks
                    downloaded += len(chunk)
                    f.write(chunk)
                    f.flush()
                    done = int(50*downloaded/total)
                    sys.stdout.write('\r[{}{}]'.format(
                        '█' * done, '.' * (50-done)))
                    sys.stdout.flush()
            sys.stdout.write('\n')
            print("Finished " + filename)


def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email = None
    password = None
    root_directory = 'media'
    book_assets = "pdf"  # pdf or mobi or epub or cover or code
    errorMessage = 'Usage: downloader.py -e <email> -p <password> [-d <directory> -b <book assets>]'

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
            book_assets = arg
    
    # do we have the minimum required info?
    if not email or not password:
        print(errorMessage)
        sys.exit(2)

    # create user with his properly header
    user = User(email, password)

    # get all your books
    books = get_books(user)
    for book in books:
        filename = "{path}/{name}.{fformat}".format(
            path=root_directory, name=book['productName'].replace(" ", "_"), fformat=book_assets)
        # get url of the book to download
        url = get_url_book(user, book['productId'], book_assets)
        download_book(filename, url)


if __name__ == "__main__":
    main(sys.argv[1:])
