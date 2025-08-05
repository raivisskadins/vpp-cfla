# vpp-cfla
https://www.python.org/downloads/  
install python 3.10  

start jupyterlab with the command:  
jupyter lab   
 
## Virutal env

python3 -m venv .venv  
source .venv/bin/activate  
pip install -r requirements.txt  

## Docker dev container

### First run
docker compose up --build

### If not adding new dependencies
docker compose up

./scripts/build_and_push.sh v0.1.2

./scripts/deploy_prod.sh v0.1.2

http://localhost:8080/docs
