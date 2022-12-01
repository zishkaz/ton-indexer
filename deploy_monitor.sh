#!/bin/bash
set -e

docker stack deploy -c docker-compose.monitor.yaml monitor
