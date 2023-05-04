## Description
Our service is designed to monitor website availability and keep track of important metrics in a database. 
We check if a website is returning a code 200 then, we also verify if the requested page matches a specified regex pattern.
Users have the option to customize the interval and regex pattern for each check. 
Personalization options include setting the check interval to anywhere between 5 and 300 seconds, as well as specifying the regex pattern that must match content on the page.

I created this project while working on a homework assignment. 
I didn't want to discard it because completing it took a lot of time and effort. Although it's not my best work, 
I enjoyed writing it because I hadn't used Python async ecosystem before and hadn't written big projects in Python for more than four years. If you're interested, feel free to submit a pull request.

## Tests
You can run tests with `pytest` in root directory.

## Run service
To run the service, simply use the command `python main.py` from the `src/monmon` directory. Alternatively, you can use a tool like gunicorn.

## Install deps
Main deps: `pip install -e .`
Install linters: `pip install -e .["linters"]`

## Build
`python -m build`

## Know issues
Currently, there seems to be an issue with the graceful shutdown feature as it is facing difficulty in handling the async.sleep function.
