#!/bin/bash
set -e

# toncenter env: stage, testnet, mainnet
export TONCENTER_ENV=${1:-stage}
export INDEXER_REV=${2:-a}

export STACK_NAME="${TONCENTER_ENV}-indexer"
echo "Stack: ${STACK_NAME}"

if [ -f ".env.${TONCENTER_ENV}" ]; then
    echo "Found env for ${TONCENTER_ENV}"
    ENV_FILE=".env.${TONCENTER_ENV}"
elif [ -f ".env" ]; then
    echo "Found default .env"
    ENV_FILE=".env"
fi

# load environment variables
if [ ! -z "${ENV_FILE}" ]; then
    set -a
    source ${ENV_FILE}
    set +a
fi

if [ -z "${TON_INDEXER_LITESERVER_CONFIG}" ]; then
    if [[ "${TONCENTER_ENV}" == "testnet" ]]; then
        echo "Using testnet config"
        export TON_INDEXER_LITESERVER_CONFIG=private/testnet.json
    else
        echo "Using mainnet config"
        export TON_INDEXER_LITESERVER_CONFIG=private/mainnet.json
    fi
else
    echo "TON_INDEXER_LITESERVER_CONFIG is set"
fi

# attach to global network
GLOBAL_NET_NAME=$(docker network ls --format '{{.Name}}' --filter NAME=toncenter-global)

if [ -z "$GLOBAL_NET_NAME" ]; then
    echo "Found network: ${GLOBAL_NET_NAME}"
    docker network create -d overlay toncenter-global
fi

# build
docker compose -f docker-compose.swarm.yaml build # --no-cache
docker compose -f docker-compose.swarm.yaml push

# deploy
docker stack deploy -c docker-compose.swarm.yaml ${STACK_NAME}
