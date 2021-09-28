# PacktPub Downloader

Script to download all your PacktPub books inspired by https://github.com/ozzieperez/packtpub-library-downloader

Since PacktPub restructured their website [packtpub-library-downloader](https://github.com/ozzieperez/packtpub-library-downloader) became obsolete because the downloader used webscraping. So I figured out that now PacktPub uses a REST API. Then I found which endpoint to use for downloading books and made a simple script. Feel free to fork and PR to improve. Packtpub's API isn't documented :'(

## Usage:

    pip install -r requirements.txt
    python main.py -e <email> -p <password> [-d <directory> -b <book file types> -s -v -q] [-i <bookids>]

##### Example: Download books in PDF format

    python main.py -e hello@world.com -p p@ssw0rd -d ~/Desktop/packt -b pdf,epub,mobi,code

## Docker integration

You must put your data in the `.env` file.

```
mv data.env-sample data.env
```

and replace the sample data with your login credentials.

```
docker-compose up
```

After the execution, you can see the content in the `book` directory.

## Commandline Options

-   _-e_, _--email_ = Your login email
-   _-p_, _--password_ = Your login password
-   _-d_, _--directory_ = Directory to download into. Default is "media/" in the current directory
-   _-b_, _--books_ = Assets to download. Options are: _pdf,mobi,epub,code,video_
-   _-s_, _--separate_ = Create a separate directory for each book
-   _-v_, _--verbose_ = Show more detailed information
-   _-q_, _--quiet_ = Don't show information or progress bars
-   _-i_, _--ids_ = Products to download by id (If it is not specified, it will download all products that you have purchased)
-   _-R_, _--readme_ = Create a README.md file with info of the book (_--separate_ option required)

**Book File Types**

-   _pdf_: PDF format
-   _mobi_: MOBI format
-   _epub_: EPUB format
-   _code_: Accompanying source code, saved as .zip files
-   _video_: Some courses are in video format

I'm working on Python 3.6.0
