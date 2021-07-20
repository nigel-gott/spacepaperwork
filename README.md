# GooseTools

# Pre-Requisites

1. https://git-scm.com/book/en/v2/Getting-Started-Installing-Git/
1. https://docs.docker.com/get-docker/
1. https://docs.docker.com/compose/install/

# Running For Local Development In Docker

1. ```git clone https://github.com/nigel-gott/spacepaperwork.git && cd spacepaperwork```
1.

 ```
 docker-compose -f local.yml up --build
 ```

1. Visit your new site running at http://0.0.0.0:8000/
1. Trigger any crons that need to be run (import market data, sync discord roles
   etc): ```./docker_managepy.sh runcrons```
1. Get an interactive python shell into goosetools
   by ```./docker_managepy.sh shell_plus```
1. Run non-integration tests ```./tests.sh```
1. Run integration tests ```./integration_test.sh```
1. Watch filesystem for changes and re-run non-integration tests when something
   changes ```./test_watcher.sh```
1. Run pre-commit checks ```./pre_commit_checks.sh```

# Running For Local Development using VirtualEnv

1. ```git clone https://github.com/nigel-gott/spacepaperwork.git && cd spacepaperwork```
1.

 ```
 cp .env.local.example .env
 ```

1. Edit ```.env``` to match your environment
1. Install poetry dependencies:
    ```
    poetry install
    ```
1. Activate virtual env:
    ```
   poetry shell
    ```
1. Migrate the database:
    ```
    ./manage.py migrate
    ```
1. load fixtures:
    ```
    ./manage.py loaddata goosetools/users/fixtures/dev.json
    ```
1. Setup an initial organization:
    ```
    ./manage.py setup_tenant
    ```
1. Run the server:
    ```
    ./manage.py runserver_plus
    ```
1. Visit and Sign Up On http://localhost:8000/goosetools
1. Import market data using:
    ```
    ./manage.py runjobs hourly
    ```
1. Get an interactive python shell into goosetools:
    ```
    ./manage.py shell_plus
    ```
1. Run non-integration tests:
    ```
    pytest
    ```
1. Run integration tests:
    ```
    ./integration_test.sh
    ```
1. Watch filesystem for changes and re-run non-integration tests when something changes:
    ```
    ptw
    ```
1. Run pre-commit checks:
    ```
    pre-commit run --all-files
    ```
1. Install pre-commit checks:
    ```
    pre-commit install
    ```

# Cron setup

Spacepaperwork runs various jobs at timed intervals such as market data import,
repeating loot groups etc. You must run `./manage.py runcrons` every 5 minutes for this
to work. To do so I suggest you setup and use cron like so:

```
crontab -e
# Now edit and add the following lines:
*/5 * * * * TODO INSERT YOUR PYTHON EXEC HERE manage.py runcrons > /home/ubuntu/cronjob.log
```
