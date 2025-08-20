# Docker usage instructions
# TODO pārrakstīt latviski un papildināt

1. Make sure to populate the env file and rename it to .env
2. Launch all scripts from this directory

# DEV

### To build:
(Takes ~5 minutes)
docker compose up --build

### Regular launch after building
docker compose up

[localhost tagad būs pieejama demo vide]

### To take down:
docker compose down

# Production

### To build:
./build_and_push.sh
(Optionally add --TAG to specify version)

### To launch 
./deploy_prod.sh
(Optionally add --TAG to specify version)
