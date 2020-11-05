# GooseTools

# Pre-Requisites 
1. https://git-scm.com/book/en/v2/Getting-Started-Installing-Git/
2. https://docs.docker.com/get-docker/
3. https://docs.docker.com/compose/install/

# Running Locally
1. ```git clone git@github.com:GROON-Echoes-Dev-Team/goosetools.git && cd goosetools```
2. Copy ```.env.docker.example``` to ```.env``` and fill in a secret key if you care.
3. 
    ```
    docker-compose -f local.yml up --build
    ```
4. Visit and Sign Up On http://localhost:8000/goosetools
5. Make yourself an admin by: ```./docker_managepy.sh runscript make_user_admin --script-args=REPLACE_WITH_YOUR_USERNAME_ENTERED_ON_GOOSETOOLS_SIGNUP```
6. Import market data using: ```./docker_managepy.sh runjobs hourly```
7. Get an interactive python shell into goosetools by ```./docker_managepy.sh shell_plus```
