pip install -r /app/requirements.txt

if [[ -z "${IDS}" ]]; then
	python /app/main.py -e $EMAIL -p $PASSWORD -d /app/book -b pdf,mobi,epub,code,video -s -v
else
	python /app/main.py -e $EMAIL -p $PASSWORD -d /app/book -b pdf,mobi,epub,code,video -s -v -i $IDS
fi