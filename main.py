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
from config import BASE_URL, BASE_STATIC_URL, PRODUCTS_ENDPOINT, PRODUCT_FROM_ID_ENDPOINT, URL_BOOK_TYPES_ENDPOINT, \
    URL_BOOK_ENDPOINT
from user import User
from multiprocessing import Pool

error_message = 'Usage: main.py -e <email> -p <password> [-d <directory> -b <book file types> -i <product ids> -l -s ' \
                '-v -q] '


# TODO: I should do a function that his only purpose is to request and return data
def book_request(user, offset=0, limit=10, verbose=False):
    data = []
    url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
    if verbose:
        tqdm.write(url)
    r = requests.get(url, headers=user.get_header())
    data += r.json().get('data', [])

    return url, r, data


def book_from_id_request(book_id, verbose=False):
    url = BASE_STATIC_URL + PRODUCT_FROM_ID_ENDPOINT.format(id=book_id)
    if verbose:
        tqdm.write(url)

    r = requests.get(url)
    rjson = r.json()
    data = {'productId': book_id, 'productName': rjson.get('title')}

    return url, r, data


def get_books(user, offset=0, limit=25, is_verbose=False, is_quiet=False):
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


def get_books_from_ids(ids, is_verbose=False, is_quiet=False):
    """
        Get all boooks from id
        Params
        ...
        ids : list
    """

    data = []

    print("Getting list of books...")

    if not is_quiet:
        id_iter = tqdm(ids, unit="Pages")
    else:
        id_iter = ids

    for book_id in id_iter:
        data.append(book_from_id_request(book_id, is_verbose)[2])

    return data


def get_url_book(user, book_id, fformat='pdf'):
    """
        Return url of the book to download
    """

    url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book_id, format=fformat)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200:  # success
        return r.json().get('data', '')

    elif r.status_code == 401:  # jwt expired
        user.refresh_header()  # refresh token
        get_url_book(user, book_id, fformat)  # call recursive

    tqdm.write('ERROR (please copy and paste in the issue)')
    tqdm.write(r.json())
    tqdm.write(r.status_code)
    return ''


def get_book_file_types(user, book_id):
    """
        Return a list with file types of a book
    """

    url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book_id)
    r = requests.get(url, headers=user.get_header())

    if (r.status_code == 200):  # success
        return r.json()['data'][0].get('fileTypes', [])

    elif (r.status_code == 401):  # jwt expired
        user.refresh_header()  # refresh token
        get_book_file_types(user, book_id)  # call recursive

    tqdm.write('ERROR (please copy and paste in the issue)')
    tqdm.write(r.json())
    tqdm.write(r.status_code)
    return []


# TODO: i'd like that this functions be async and download faster
def download_file(filename, url, quiet):
    """
        Download file
    """
    if not quiet:
        tqdm.write('Starting to download ' + filename)

    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(r.content)
        else:
            total = int(total)
            progress = tqdm(
                total=math.ceil(total),
                unit='KB',
                unit_scale=True,
                mininterval=1
            )
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
                    progress.update(1024)
            progress.close()
            if not quiet:
                tqdm.write('Finished ' + filename)


def get_book_name(book, file_type):
    book_name = book['productName'].replace(' ', '_').replace('.', '_').replace(':', '_').replace('/', '')
    if file_type == 'video' or file_type == 'code':
        return book_name, book_name + '.' + 'zip'
    else:
        return book_name, book_name + '.' + file_type


def make_zip(filename):
    if filename[-4:] == 'code':
        os.replace(filename, filename[:-4] + 'zip')


def move_current_files(root, book):
    sub_dir = f'{root}/{book}'
    does_dir_exist(sub_dir)
    mask = fr"{sub_dir}.[pmezc][dopi][fbupd]*"
    for f in glob.iglob(mask):
        try:
            os.rename(f, f'{sub_dir}/{book}' + f[f.index('.'):])
        except OSError:
            os.rename(f, f'{sub_dir}/{book}' + '_1' + f[f.index('.'):])
        except ValueError as e:
            tqdm.write(e)
            tqdm.write('Skipping')


def set_book_type(book, file_type, separate, root_directory, first=True):
    name_append = True
    book_name, book_filename = get_book_name(book, file_type)
    if separate:
        filename = f'{root_directory}/{book_name}/{book_filename}'
        if os.path.exists(filename) or os.path.exists(filename.replace('.code', '.zip')):
            name_append = False
        elif first:
            move_current_files(root_directory, book_name)
    else:
        filename = f'{root_directory}/{book_filename}'
    return filename, name_append


def download_all_books(user, books, book_file_types, parallel, separate, root_directory, quiet=False):
    if not quiet:
        print('\nChecking books...')
        books_iter = tqdm(books, unit='Book')
    else:
        books_iter = books
    filenames, urls = enumerate_book_file_types(books_iter, book_file_types, root_directory, separate, user)
    if len(filenames):
        quiet_list = [quiet] * len(urls)
        if not quiet:
            print('Downloading files...')
        names_and_urls = zip(filenames, urls, quiet_list)
        if parallel:
            # Asynchronously download books 10 at a time
            p = Pool(10)
            p.starmap(download_file, names_and_urls)
            p.imap(make_zip, filenames, chunksize=5)
        else:
            # Sequential download
            for name, url, q in names_and_urls:
                download_file(name, url, q)
        if not quiet:
            print('\nDone!')
    else:
        if not quiet:
            print('\nAll books are already downloaded!')


def does_dir_exist(directory):
    # Check if directory doesn't exist
    if not os.path.exists(directory):
        try:
            # try making directory if it doesn't exist
            os.makedirs(directory)
        except Exception as e:
            print(e)
            sys.exit(2)


def enumerate_book_file_types(books_iter, book_file_types, root_directory, separate, user, verbose=False):
    filenames = []
    urls = []
    for book in books_iter:
        # get the different file type of current book
        file_types = get_book_file_types(user, book['productId'])
        first_file = True
        for file_type in file_types:
            if file_type in book_file_types:  # check if the file type entered is available by the current book
                file_name, append = set_book_type(book, file_type, separate, root_directory, first_file)
                if append:
                    filenames.append(file_name)
                    # get url of the book to download
                    urls.append(get_url_book(user, book['productId'], file_type))
                first_file = False
    return filenames, urls


def get_opts_args(argv):
    try:
        return getopt.getopt(
            argv,
            'e:p:d:b:i:lsvq',
            [
                'email=',
                'pass=',
                'directory=',
                'books=',
                'ids=',
                'parallel',
                'separate',
                'verbose',
                'quiet'
            ]
        )
    except getopt.GetoptError:
        print(error_message)
        sys.exit(2)


def check_arg(email, password):
    # do we have the minimum required info?
    if not email or not password:
        print(error_message)
        sys.exit(2)


def parse_args(argv):
    email = None
    password = None
    root_directory = 'media'
    book_file_types = ['pdf', 'mobi', 'epub', 'code']
    parallel = None
    separate = None
    verbose = None
    quiet = None
    download_ids = None

    # get all options from argument
    opts, args = get_opts_args(argv)

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
        elif opt in ('-i', '--ids'):
            download_ids = arg.split(',')

    check_arg(email, password)

    return email, \
        password, \
        root_directory, \
        book_file_types, \
        parallel, \
        separate, verbose, \
        quiet, \
        download_ids


def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email, \
        password, \
        root_directory, \
        book_file_types, \
        parallel, \
        separate, \
        verbose, \
        quiet, \
        download_ids = parse_args(argv)

    # check if not exists dir and create
    does_dir_exist(root_directory)

    # create user with his properly header
    user = User(email, password)

    # get all your books
    if (download_ids):
        books = get_books_from_ids(
            download_ids, is_verbose=verbose, is_quiet=quiet)
    else:
        books = get_books(user, is_verbose=verbose, is_quiet=quiet)

    # downloading all books
    download_all_books(user, books, book_file_types, parallel,
                       separate, root_directory, quiet)


if __name__ == '__main__':
    main(sys.argv[1:])
