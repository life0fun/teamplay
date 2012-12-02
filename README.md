# A bot that talks to staff member and collect status.

Our software group wants to be more agile. We need to collect status from programmers for better software project
planning and monitoring.

This bot will collect status from each programmer on which CRs he's working on, how much time on that, and
what are the blockers and supports needed to progress the CR.

Each member's status is logged into its id file under logs/id.

Later, we do big data analysis on the data to find out:
1. what percentage a programmer is working on new work or support at various stages of a project.
2. the total time spending on each task, CR.
3. 

## Architecture

* A configuration file contains the member list, schedule time, and questions.
* find out Gtalk server IP address with tcpdump -n -i eth0
* the credential for Gtalk Jid and password and proxy credential is hard-coded.
* Talk to Gtalk from behind the proxy using TLS, not SSL.
* logging conf

## Start and stop

* virtualenv setup
``` javascript
	wget https://bitbucket.org/ianb/virtualenv/raw/tip/virtualenv.py
	mkdir -R ~/venv/base
    python virtualenv.py ~/venv/base  or
    python virtualenv.py ~/venv/proj1
	echo source ~/venv/base/bin/activate >> ~/.bashrc
	which python
	pip install sleekxmpp
```

* virtualenv wrapper
```
    wget http://pypi.python.org/packages/source/v/virtualenvwrapper/virtualenvwrapper-3.6.tar.gz
    python setup.py install
    or 
    pip install virtualenvwrapper

    echo `source /usr/local/bin/virtualenvwrapper.sh >> ~/.bashrc'

    mkvirtualenv teamplay
    workon teamplay
    pip install xleekxmpp
    pip install schedule

```

* start
```
    (./TeamBot.py &)
```

* kill the lingering script
``` javascript
    for p in $(ps -ef | grep TeamBot | awk '{print $2}'); do kill -9 $p; done`
    or
    pkill -f TeamBot
```
