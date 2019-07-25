# -*- coding: utf-8 -*-
#!/usr/bin/python

from __future__ import print_function
import os
import sys
import glob
import math
import getopt
import requests
from tqdm import tqdm, trange
from config import BASE_URL, PRODUCTS_ENDPOINT, URL_BOOK_TYPES_ENDPOINT, URL_BOOK_ENDPOINT
from user import User
from multiprocessing import Pool


#TODO: I should do a function that his only purpose is to request and return data
def book_request(user, offset=0, limit=10, verbose=False):
    data = []
    url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
    r = requests.get(url, headers=user.get_header())
    data += r.json().get('data', [])

    return url, r, data


def get_books(user, offset=0, limit=25, is_verbose=False, is_quiet=False):
    '''
        Request all your books, return json with info of all your books
        Params
        ...
        header : str
        offset : int
        limit : int
            how many book wanna get by request
    '''
    # TODO: given x time jwt expired and should refresh the header, user.refresh_header()

    url, r, data = book_request(user, offset, limit)

    print(f'You have {str(r.json()["count"])} books')
    tqdm.write("Getting list of books...")

    if not is_quiet:
        pages_list = trange(r.json()['count'] // limit, unit='Pages')
    else:
        pages_list = range(r.json()['count'] // limit)
    for _ in pages_list:
        offset += limit
        data += book_request(user, offset, limit, is_verbose)[2]
    return data


def get_url_book(user, book_id, fformat='pdf'):
    '''
        Return url of the book to download
    '''

    url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book_id, format=fformat)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200: # success
        return r.json().get('data', '')

    elif r.status_code == 401: # jwt expired
        user.refresh_header() # refresh token
        get_url_book(user, book_id, fformat)  # call recursive

    print('ERROR (please copy and paste in the issue)')
    print(r.json())
    print(r.status_code)
    return ''


def get_book_file_types(user, book_id):
    '''
        Return a list with file types of a book
    '''

    url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book_id)
    r = requests.get(url, headers=user.get_header())

    if  (r.status_code == 200): # success
        return r.json()['data'][0].get('fileTypes', [])

    elif (r.status_code == 401): # jwt expired
        user.refresh_header() # refresh token
        get_book_file_types(user, book_id)  # call recursive

    print('ERROR (please copy and paste in the issue)')
    print(r.json())
    print(r.status_code)
    return []


# TODO: i'd like that this functions be async and download faster
def download_book(filename, url):
    '''
        Download your book
    '''
    tqdm.write('Starting to download ' + filename)

    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(r.content)
        else:
            total = int(total)
            # TODO: read more about tqdm
            for chunk in tqdm(r.iter_content(chunk_size=1024), total=math.ceil(total//1024), unit='KB', unit_scale=True):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
            print('Finished ' + filename)


def make_zip(filename):
    if filename[-4:] == 'code':
        os.replace(filename, filename[:-4] + 'zip')


def move_current_files(root, book, first=True):
    if first:
        sub_dir = f'{root}/{book}'
        does_dir_exist(sub_dir)
        mask = fr"{sub_dir}.[pmezc][dopi][fbupd]*"
        for f in glob.iglob(mask):
            try:
                os.rename(f, f'{sub_dir}/{book}' + f[f.index('.'):])
            except OSError:
                os.rename(f, f'{sub_dir}/{book}' + '_1' + f[f.index('.'):])
            except ValueError as e:
                print(e)
                print('Skipping')


def does_dir_exist(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(e)
            sys.exit(2)


def enumerate_book_file_types(books_iter, book_file_types, root_directory, separate, user):
    filenames = []
    urls = []
    for book in books_iter:
        # get the different file type of current book
        file_types = get_book_file_types(user, book['productId'])
        first_file_ext = True
        for file_type in file_types:
            if file_type in book_file_types:  # check if the file type entered is available by the current book
                book_name = book['productName'].replace(' ', '_').replace('.', '_').replace(':', '_').replace('/', '')
                if separate:
                    file_name = f'{root_directory}/{book_name}/{book_name}.{file_type}'
                    if os.path.exists(file_name) or os.path.exists(file_name.replace('.code', '.zip')):
                        continue
                    filenames.append(file_name)
                    move_current_files(root_directory, book_name, first_file_ext)
                    first_file_ext = False
                else:
                    file_name = f'{root_directory}/{book_name}.{file_type}'
                    filenames.append(file_name)
                # get url of the book to download
                urls.append(get_url_book(user, book['productId'], file_type))
    return filenames, urls


def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email = None
    password = None
    root_directory = 'media'
    book_file_types = ['pdf', 'mobi', 'epub', 'code']
    parallel = None
    separate = None
    verbose = None
    quiet = None
    errorMessage = 'Usage: main.py -e <email> -p <password> [-d <directory> -b <book file types> -l -s -v -q]'

    # get the command line arguments/options
    try:
        opts, args = getopt.getopt(
            argv, 'e:p:d:b:lsvq', ['email=', 'pass=', 'directory=', 'books=', 'parallel', 'separate', 'verbose', 'quiet'])
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
            book_file_types = arg.split(',')
        elif opt in ('-l', '--parallel'):
            parallel = True
            quiet = True
        elif opt in ('-s', '--separate'):
            separate = True
        elif opt in ('-v', '--verbose'):
            verbose = True
            quiet = False
        elif opt in ('-q', '--quiet'):
            quiet = True
            verbose = False

    # do we have the minimum required info?
    if not email or not password:
        print(errorMessage)
        sys.exit(2)

    # check if not exists dir and create
    does_dir_exist(root_directory)

    # create user with his properly header
    user = User(email, password)

    # get all your books
    books = get_books(user, is_verbose=verbose, is_quiet=quiet)
    print('\nChecking books...')
    if not quiet:
        books_iter = tqdm(books, unit='Book')
    else:
        books_iter = books
    filenames, urls = enumerate_book_file_types(books_iter, book_file_types, root_directory, separate, user)
    if len(filenames):
        if not quiet:
            print('Downloading files...')
        names_and_urls = zip(filenames, urls)
        if parallel:
            # Asynchronously download books 10 at a time
            p = Pool(10)
            p.starmap(download_book, names_and_urls)
            p.imap(make_zip, filenames, chunksize=5)
        else:
            # Sequential download
            for name, url in names_and_urls:
                download_book(name, url)
        if not quiet:
            print('\nDone!')
    else:
        if not quiet:
            print('\nAll books are already downloaded!')


if __name__ == '__main__':
    main(sys.argv[1:])
