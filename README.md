<a href="https://github.com/vbonvin/ipt_connect"><img style="position: absolute; top: 0; left: 0; border: 0;" src="https://s3.amazonaws.com/github/ribbons/forkme_left_green_007200.png" alt="Fork me on GitHub"></a>

# ipt_connect

A python/django web-based interface to track the grades, compute the rankings and display a lot of interesting statistics on the <a href="https://iptnet.info">International Physicists' Tournament</a>. 

### Status
* Code: working, v2.0, minor display bugs to fix
* Documentation: work in progress
* CI: None

 <a href='http://ipt-connect.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/ipt-connect/badge/?version=latest' alt='Documentation Status' /></a>

### Starting:
* Install the requirements `pip install -r requirements.txt`
* Run `python manage.py runserver`
* Open <a href="http://127.0.0.1:8000/IPTdev/">http://127.0.0.1:8000/IPTdev/</a>


### Requirements:
- Python 2.x
- Django > 1.9
- Pillow


## F.A.Q:

### How to add superuser and sign in to site?
* Run `python manage.py createsuperuser`
* Set username, email address and password.
* Run `python manage.py runserver`
* Open <a href="http://127.0.0.1:8000/admin/">http://127.0.0.1:8000/admin/</a> and sign in.
