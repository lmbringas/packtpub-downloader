# PacktPub Downloader

Script to download all your PacktPub inspired by https://github.com/ozzieperez/packtpub-library-downloader

Since PacktPub restructure his website [packtpub-library-downloader](https://github.com/ozzieperez/packtpub-library-downloader) became obsolete because use webscraping. So i figure out that now PacktPub  use now API REST. Then i found which endpoint use to download books and made simple script. Feel free to fork and PR to inprove. Packtpub API's isn't documented :'(

## Usage:
    pip install -r requirements.txt
	python main.py -e <email> -p <password> [-d <directory> -b <book file types>]

##### Example: Download books in PDF format
	python main.py -e hello@world.com -p p@ssw0rd -d ~/Desktop/packt -b pdf,epub,mobi,code

## Commandline Options
- *-e*, *--email* = Your login email
- *-p*, *--password* = Your login password
- *-d*, *--directory* = Directory to download into. Default is "media/" in the current directory
- *-b*, *--books* = Assets to download. Options are: *pdf,mobi,epub,code*

**Book File Types**

- *pdf*: PDF format
- *mobi*: MOBI format
- *epub*: EPUB format
- *code*: Accompanying source code

I'm working on Python 3.6.0 
