# beeper.py
Bundle virtualenv and your project as a relocatable tar.

## Writer you `beeper.yml`

Example:

```yaml
application: app
manifest:
    - app/
    - manage.py
scripts:
    - npm install
    - node_modules/fis/bin/fis release -r app/frontend/  -f app/frontend/fis-conf.js -mpod ./zion
```

## Run build process

Example

```
$ ls
app  beeper.yml manage.py
$ beeper --version b3d53cf
...
$ ls dist/
app-b3d53cf.tar
$ tar -tvf dist/app-b3d53cf.tar
app/
manage.py
venv/
venv/share/
...
```

## Distribute your application to server

A simple example of how to deploy a tar: use scp to upload tar to server, extract tar, run install.sh, and boom, run your server:

```
$ scp ./dist/app-b3d53cf.tar deploy@your-server:/var/www/app/app-b3d53cf.tar
$ ssh deploy@your-server /bin/bash -c "cd /var/www/app/; tar xf app-b3d53cf.tar; ./install.sh; venv/bin/python manage.py runserver"
```
