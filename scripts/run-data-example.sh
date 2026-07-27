#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 {elasticsearch|opensearch|qdrant|redis|mongodb|s3|sqlalchemy}" >&2
  exit 2
fi

case "$1" in
  elasticsearch) module=example_data_elasticsearch_1.data_ports ;;
  opensearch) module=example_data_opensearch_1.data_ports ;;
  qdrant) module=example_data_qdrant_1.data_ports ;;
  redis) module=example_data_redis_1.data_ports ;;
  mongodb) module=example_data_mongodb_1.data_ports ;;
  s3) module=example_data_s3_1.data_ports ;;
  sqlalchemy) module=example_data_sqlalchemy_1.data_ports ;;
  *)
    echo "unknown data example: $1" >&2
    exit 2
    ;;
esac

export PYTHONPATH="../muscles/src:../muscles-data/src:../muscles-data-elasticsearch/src:../muscles-data-opensearch/src:../muscles-data-qdrant/src:../muscles-data-redis/src:../muscles-data-mongodb/src:../muscles-data-s3/src:../muscles-data-sqlalchemy/src:.${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m "$module"
