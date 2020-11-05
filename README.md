# GooseTools

# Running Locally
1. Copy ```.env.example``` to ```.env``` and fill in a secret key if you care.
2. 
    ```
    docker-compose -f local.yml up --build
    ```
3. Visit http://localhost:8000/goosetools
4. Make yourself an admin by: ```./docker_managepy.sh runscript make_user_admin --script-args=REPLACE_WITH_YOUR_USERNAME_ENTERED_ON_GOOSETOOLS_SIGNUP```
5. Import market data using: ```./docker_managepy.sh runjobs hourly```
6. Get an interactive python shell into goosetools by ```./docker_managepy.sh shell_plus```