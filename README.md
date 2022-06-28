# WikiData-Integration
WikiData integration

This repo uses:

- pywikibot to interact with Wikimedia / Wikidata
- fastAPI to run an API
- jupyter lab to run jupyter notebooks

Directories

- api: code that runs the API
- data: hardcoded data for this demo
- logs: log files
- notebooks: jupyter notebooks used during development
- notes: random notes
- scripts: scripts that run the API, interact with wikidata, import records to local instance of Wikibase


## Setup

1. Create [wikidata account](https://www.wikidata.org/w/index.php?title=Special:CreateAccount&returnto=Wikidata%3AMain+Page)

2. Create [wikidata bot account](https://www.wikidata.org/wiki/Special:BotPasswords)

3. install libraries

requires Python 3.6.8+

Optional: create a virtual environment called 'myenv' using venv

```
python3 -m venv myenv
source myenv/bin/activate
```

install libraries

```bash
pip install wheel
pip install -U setuptools
pip install -r requirements.txt
```

4. Edit user-config.py

Copy `user-config.sample.py` and rename it `user-config.py`. Replace 'my_username' with your wikidata username.


5. Edit user-password.py

Copy `user-password.sample.py` and rename it `user-password.py`. Replace 'my_username' with your wikidata username, 'my_username_bot' with your wikidata bot username, and 'bot_password' with your wikidata bot password.


## Run the code

Start api

```
cd api
uvicorn main:app --reload
```

 Start jupyter notebooks

```
// inside the root folder of the repo

jupyter lab
```

run the various scripts

```
// inside the root folder of the repo

python scripts/<file>.py
```

