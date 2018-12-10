Small program, that finds snippets with requested class/function usage on github and put them in the result file

Examples of usage:
python3 parser.py javascript react -f filter
python3 parser.py python django -c ListView -l 10 -e 5

You can always see information about usage by typing "python3 parser -h"


P.S. You should have python version > 3.5 and modules 'aiohttp', 'ujson' and 'async_timeout' installed to use this program
