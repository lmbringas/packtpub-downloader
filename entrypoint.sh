pip install -r /app/requirements.txt

if [[ -z "${IDS}" ]]; then
#	python /app/main.py -e $EMAIL -p $PASSWORD -d /app/book -b pdf,mobi,epub,code,video -s -v
	python /app/main.py -e $EMAIL -p $PASSWORD -d /app/book -b pdf,mobi,epub -s -v -R
else
	python /app/main.py -e $EMAIL -p $PASSWORD -d /app/book -b pdf,mobi,epub,code,video -s -v -R -i $IDS
fi