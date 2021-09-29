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
from config import BASE_URL, BASE_STATIC_URL, PRODUCTS_ENDPOINT, PRODUCT_FROM_ID_ENDPOINT, URL_BOOK_TYPES_ENDPOINT, URL_BOOK_ENDPOINT, AUTHOR_FROM_ID_ENDPOINT
from user import User

error_message = 'Usage: main.py -e <email> -p <password> [-d <directory> -b <book file types> -i <products id> -sR -v -q]'


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


def get_books(user, offset=0, limit=10, is_verbose=False, is_quiet=False):
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
    print("Getting list of books...")

    if not is_quiet:
        pages_list = trange(r.json()['count'] // limit, unit='Pages')
    else:
        pages_list = range(r.json()['count'] // limit)
    for i in pages_list:
        offset += limit
        data += book_request(user, offset, limit, is_verbose)[2]
    return data


def get_books_from_ids(ids, is_verbose=False, is_quiet=False):
    """
        Get all books from id
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


def get_url_book(user, book_id, file_format='pdf'):
    """
        Return url of the book to download
    """

    url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book_id, format=file_format)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200:  # success
        return r.json().get('data', '')

    elif r.status_code == 401:  # jwt expired
        user.refresh_header()  # refresh token
        get_url_book(user, book_id, file_format)  # call recursive

    tqdm.write('ERROR (please copy and paste in the issue): ' + str(r.status_code))
    for key,value in r.json().items():
        tqdm.write('  ' + key + ': ' + str(value))
    raise PermissionError('Could not download book: ' + book_id + ' in format: ' + file_format)


def get_book_file_types(user, book_id):
    """
        Return a list with file types of a book
    """

    url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book_id)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200:  # success
        return r.json()['data'][0].get('fileTypes', [])

    elif r.status_code == 401:  # jwt expired
        user.refresh_header()  # refresh token
        return get_book_file_types(user, book_id)  # call recursive

    tqdm.write('ERROR (please copy and paste in the issue): ' + str(r.status_code))
    for key, value in r.json().items():
        tqdm.write('  ' + key + ': ' + str(value))
    return []


# TODO: i'd like that this functions be async and download faster
def download_file(filename, url):
    """
        Download file
    """
    tqdm.write('Starting to download ' + filename)

    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(response.content)
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
            tqdm.write('Finished ' + filename)


def get_book_name(book, file_type):
    book_name = book['productName'].replace(' ', '_').replace('.', '_').replace(':', '_').replace('/','').replace('?','')
    if file_type == 'video' or file_type == 'code':
        return book_name, book_name + '.' + file_type + '.zip'
    else:
        return book_name, book_name + '.' + file_type


def make_zip(filename):
    if filename[-4:] == 'code':
        os.replace(filename, filename[:-4] + 'code.zip')
    elif filename[-5:] == 'video':
        os.replace(filename, filename[:-5] + 'video.zip')


def move_current_files(root, book):
    sub_dir = f'{root}/{book}'
    does_dir_exist(sub_dir)
    for f in glob.iglob(sub_dir + '.*'):
        try:
            os.rename(f, f'{sub_dir}/{book}' + f[f.index('.'):])
        except OSError:
            os.rename(f, f'{sub_dir}/{book}' + '_1' + f[f.index('.'):])
        except ValueError as e:
            tqdm.write(repr(e))
            tqdm.write('Skipping')


def download_book_by_type(user, book, file_type, separate, root_directory, verbose=False):
    book_name, book_filename = get_book_name(book, file_type)
    if separate:
        filename = f'{root_directory}/{book_name}/{book_filename}'
        move_current_files(root_directory, book_name)
    else:
        filename = f'{root_directory}/{book_filename}'

    if os.path.exists(filename):
        if verbose:
            tqdm.write(f'{filename} already exists, skipping.')
        return

    try:
        # get url of the book to download
        url = get_url_book(user, book['productId'], file_type)
        download_file(filename, url)
    except PermissionError as e:
        tqdm.write(repr(e))
        tqdm.write('Skipping')


def download_all_books(user, books, book_file_types, separate, root_directory, verbose=False, quiet=False):
    tqdm.write('Downloading books...')
    if not quiet:
        books_iter = tqdm(books, unit='Book')
    else:
        books_iter = books
    for book in books_iter:
        # get the different file type of current book
        file_types = get_book_file_types(user, book['productId'])
        for file_type in file_types:
            if file_type in book_file_types:  # check if the file type entered is available by the current book
                download_book_by_type(
                    user, book, file_type, separate, root_directory, verbose)


def does_dir_exist(directory):
    # Check if directory not exists
    if not os.path.exists(directory):
        try:
            # try making dir if not exists
            os.makedirs(directory)
        except Exception as e:
            print(e)
            sys.exit(2)

def get_author_info(author_id):
    url = BASE_STATIC_URL + AUTHOR_FROM_ID_ENDPOINT.format(id=author_id)

    r = requests.get(url)
    rjson = r.json()
    return rjson


def get_book_info(book_id):
    url = BASE_STATIC_URL + PRODUCT_FROM_ID_ENDPOINT.format(id=book_id)

    r = requests.get(url)
    rjson = r.json()
    authors = []
    

    try:
      for author in rjson.get('authors'):
        authors.append(get_author_info(author).get('author')) 
      data = {
        'title': rjson.get('title'),
        'authors': authors,
        'isbn13': rjson.get('isbn13'),
        'description': rjson.get('oneLiner'),
        'pages': rjson.get('pages'),
        'releaseDate': rjson.get('publicationDate')[:10],
        'category': rjson.get('category'),
        'homepage': f"https://subscription.packtpub.com{rjson.get('readUrl')}"
      }
    except:
      pass

    return data

# TODO: Get link to Github repository where present (see book 9781789957754)
def create_readme(path, book):
    filename = os.path.join(path, 'README.md')
    try:
      data = get_book_info(book['productId'])

      with open(filename, 'w', encoding='utf-8') as file:
          file.write(f"# {str(data['title'])}\n")
          file.write('\n')
          file.write(f"- By {', '.join(data['authors'])}\n")
          file.write(f"- Publication date: {data['releaseDate']}\n")
          file.write(f"- ISBN: {data['isbn13']}\n")
          file.write(f"- Pages: {data['pages']}\n")
          file.write('\n')
          file.write(data['description'] + '\n')
          file.write('\n')
          file.write(f"* [Book Home Page]({data['homepage']})\n")
          for k, v in book['files'].items():
              file.write(f"* [{k.upper()}]({v})\n")
          file.write('\n')
          file.write('<!-- EOF -->')
    except Exception as e:
          pass


def get_opts_args(argv):
    try:
        return getopt.getopt(
            argv,
            'e:p:d:b:i:svqR',
            [
                'email=',
                'pass=',
                'directory=',
                'books=',
                'ids=',
                'separate',
                'verbose',
                'quiet',
                'readme'
            ]
        )
    except getopt.GetoptError:
        print(error_message)
        sys.exit(2)

def check_arg(email, password, verbose, quiet):
    # Is this true?
    if verbose and quiet:
        print("Verbose and quiet cannot be used together.")
        sys.exit(2)

    # do we have the minimum required info?
    if not email or not password:
        print(error_message)
        sys.exit(2)

def parse_args(argv):
    email = None
    password = None
    root_directory = 'media'
    book_file_types = ['pdf', 'mobi', 'epub', 'code']
    separate = None
    verbose = None
    quiet = None
    download_ids = None
    readme = None

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
        elif opt in ('-s', '--separate'):
            separate = True
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-q', '--quiet'):
            quiet = True
        elif opt in ('-R', '--readme'):
            readme = True
        elif opt in ('-i', '--ids'):
            download_ids = arg.split(',')

    check_arg(email, password, verbose, quiet)

    return email, \
        password, \
        root_directory, \
        book_file_types, \
        separate, verbose, \
        quiet, \
        download_ids, \
        readme


def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email, \
        password, \
        root_directory, \
        book_file_types, \
        separate, \
        verbose, \
        quiet, \
        download_ids, \
        readme = parse_args(argv)

    # check if not exists dir and create
    does_dir_exist(root_directory)

    # create user with his properly header
    user = User(email, password)

    # get all your books
    if download_ids:
        books = get_books_from_ids(
            download_ids, is_verbose=verbose, is_quiet=quiet)
    else:
        books = get_books(user, is_verbose=verbose, is_quiet=quiet)
    tqdm.write('Downloading books...')
    if not quiet:
        books_iter = tqdm(books, unit='Book')
    else:
        books_iter = books
    for book in books_iter:
        # get the different file type of current book
        file_types = get_book_file_types(user, book['productId'])
        tqdm.write('Requested formats: ' + ','.join(book_file_types) + ' but only available: ' + ','.join(file_types))
        book_name = book['productName'].replace(' ', '_').replace('.', '_').replace(':', '_').replace('/','').replace('?','')
        book['files'] = {}
        if separate:
            filepath = f'{root_directory}/{book_name}'
            move_current_files(root_directory, book_name)
        else:
            filepath = f'{root_directory}'
        for file_type in file_types:
            if file_type in book_file_types:  # check if the file type entered is available by the current book
                filename = f'{filepath}/{book_name}.{file_type}'
                book['files'][file_type] = f'{book_name}.{file_type}'
                # implied check for pdf, epub, mobi, also avoid name collision when both code and video are available.
                if os.path.exists(filename.replace('.code', '.code.zip').replace('.video', '.video.zip')):
                    if verbose:
                        tqdm.write(f'{filename} already exists, skipping.')
                    continue

                try:
                    # get url of the book to download
                    url = get_url_book(user, book['productId'], file_type)
                    download_file(filename, url)
                    make_zip(filename)
                except PermissionError as e:
                    tqdm.write(repr(e))
                    tqdm.write('Skipping')
        if separate and readme:
            create_readme(f'{filepath}', book)


if __name__ == '__main__':
    main(sys.argv[1:])
