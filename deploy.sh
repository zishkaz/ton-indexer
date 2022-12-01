#!/bin/bash
set -e

export TONCENTER_ENV=${1:-stage}
export INDEXER_REV=${2:-a}
echo "TONCENTER_ENV: ${TONCENTER_ENV}"
echo "INDEXER_REV: ${INDEXER_REV}"

if [[ "${TONCENTER_ENV}" == "testnet" ]]; then
    echo "Using testnet config"
    export TON_INDEXER_LITESERVER_CONFIG=private/private.toncenter-testnet.json
else
    echo "Using mainnet config"
    export TON_INDEXER_LITESERVER_CONFIG=private/private.toncenter.json
fi

export $(cat .env) > /dev/null|| echo "No .env file"

INDEXER_WORKER_NAME=${INDEXER_REV} envsubst '$INDEXER_WORKER_NAME' < docker-compose.swarm.yaml > docker-compose.printed.yaml

docker compose -f docker-compose.printed.yaml build
docker compose -f docker-compose.printed.yaml push

docker stack deploy -c docker-compose.printed.yaml ${TONCENTER_ENV}-indexer
rm -f docker-compose.printed.yaml
