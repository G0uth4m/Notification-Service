# Notification Service

## Setup
### Activate virtual environment
```
$ python3 -m venv venv/
$ source venv/bin/activate
```

### Install requirements
```
$ pip install -r requirements.txt
```

### Install mongodb and redis server
```
$ sudo apt install mongodb
$ sudo apt install redis-server
```

### Start mongodb and redis-server
```
$ sudo service mongodb start
$ sudo service redis-server start
```

### Setup redis queue listeners
```
$ rq worker webpush-jobs
```
Open another terminal
```
$ rq worker db-jobs
```

### Run flask
```
$ flask run
```

## Authors
* **Goutham** 