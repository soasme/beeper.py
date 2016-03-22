# beeper.py

Bundling virtualenv and your project as a relocatable tar.

That makes you have an enjoyment of deploy experience: fetch tar, extract tar, run install, and it' done!

## Writer your `beeper.yml`

Example:

```yaml
application: app
manifest:
    - app/
    - manage.py
scripts:
    - npm install
    - node_modules/fis/bin/fis release -r app/frontend/  -f app/frontend/fis-conf.js -mpod ./app
postinstall:
    - echo "Done."
```

* define `application`, which will be prefix in the naming of tar
* define `manifest`, which declares what files will be included into tar
* define `scripts`, which will be executed in a row before packaging into a tar
* define `postinstall`, which will be executed in a row after tar been deployed and relocated.

## Run build process

`beeper build` is the most important command. It will run scripts, pack all of the `manifest` files and venv into a tar.

Example

```
$ ls
app  beeper.yml manage.py
$ beeper build --version b3d53cf
...
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
