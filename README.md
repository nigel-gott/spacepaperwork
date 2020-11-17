# GooseTools

# Pre-Requisites
1. https://git-scm.com/book/en/v2/Getting-Started-Installing-Git/
2. https://docs.docker.com/get-docker/
3. https://docs.docker.com/compose/install/

# Running For Local Development In Docker
1. ```git clone git@github.com:GROON-Echoes-Dev-Team/goosetools.git && cd goosetools```
2.
    ```
    docker-compose -f local.yml up --build
    ```
3. Visit and Sign Up On http://localhost:8000/goosetools
4. Make yourself an admin by: ```./docker_managepy.sh runscript make_user_admin --script-args=REPLACE_WITH_YOUR_USERNAME_ENTERED_ON_GOOSETOOLS_SIGNUP```
5. Import market data using: ```./docker_managepy.sh runjobs hourly```
6. Get an interactive python shell into goosetools by ```./docker_managepy.sh shell_plus```
7. Run non-integration tests ```./tests.sh```
8. Run integration tests ```./integration_test.sh```
9. Watch filesystem for changes and re-run non-integration tests when something changes ```./test_watcher.sh```
10. Run pre-commit checks ```./pre_commit_checks.sh```

# Running For Local Development using VirtualEnv
1. ```git clone git@github.com:GROON-Echoes-Dev-Team/goosetools.git && cd goosetools```
2.
    ```
    cp .env.local.example .env
    ```
3. Edit ```.env``` to match your environment
4. Setup a virtual env:
    ```
    python3 -m venv venv
    ```
5. Activate virtual env:
    ```
    source venv/bin/activate
    ```
6. Install dependencies :
    ```
    pip install -r requirements.txt
    ```
7. Run the server:
    ```
    ./manage.py runserver_plus
    ```
8. Visit and Sign Up On http://localhost:8000/goosetools
9. Make yourself an admin by:
    ```
    ./manage.py runscript make_user_admin --script-args=REPLACE_WITH_YOUR_USERNAME_ENTERED_ON_GOOSETOOLS_SIGNUP
    ```
10. Import market data using:
    ```
    ./manage.py runjobs hourly
    ```
11. Get an interactive python shell into goosetools:
    ```
    ./manage.py shell_plus
    ```
12. Run non-integration tests:
    ```
    pytest
    ```
13. Run integration tests:
    ```
    ./integration_test.sh
    ```
14. Watch filesystem for changes and re-run non-integration tests when something changes:
    ```
    ptw
    ```
15. Run pre-commit checks:
    ```
    pre-commit run --all-files
    ```
16. Install pre-commit checks:
    ```
    pre-commit install
    ```
