#!/bin/bash -x
set -e

# //////////////////////////////////////////////////////////////////////////////
# Variables
# //////////////////////////////////////////////////////////////////////////////
LATTICE_PATH="$PWD"

TARGET_ENV=$1
if [[ $TARGET_ENV == "production" ]]
then
  echo "Recognized Environment: '${TARGET_ENV}'"
  source ./.env
elif [[ $TARGET_ENV == "development" ]]
then
  echo "Recognized Environment: '${TARGET_ENV}'"
  source ./.env
elif [[ $TARGET_ENV == "local" ]]
then
  echo "Recognized Environment: '${TARGET_ENV}'"
  source ./.env
else
  echo "Unrecognized Environment: '${TARGET_ENV}'"
  exit 1
fi

LATTICE_DATABASE_APP_PATH="$LATTICE_PATH/database/app"

UNDERLINE='\033[4;37m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[1;31m'
NC='\033[0m'

# //////////////////////////////////////////////////////////////////////////////
# Common Functions
# //////////////////////////////////////////////////////////////////////////////
function confirm_command () {
  # Remind of environment
  echo -e "Env: ${UNDERLINE}${TARGET_ENV}${NC}"
  # Remind of command
  if [[ -n "$1" ]]
  then
    echo -e "Cmd: ${UNDERLINE}manage.sh ${1} ${2} ${3} ${4}${NC}\n"
  fi
  # Confirm
  read -p "Are you sure? [Y/n] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Y]$ ]]
  then
    echo -e "${GREEN}Running${NC}\n"
  else
    echo -e "${RED}Aborted${NC}\n"
    exit 0
  fi
}

function confirm_finish() {
  echo -e "\n${GREEN}manage.sh - Finished${NC}\n"
}

# TODO: placeholder for whne we want to get secrets from a vault
# function get_secret {
#   echo $(bash "${LATTICE_PATH}/ops/get-secret.sh" $TARGET_ENV $1)
# }

# //////////////////////////////////////////////////////////////////////////////
# Database Functions
# //////////////////////////////////////////////////////////////////////////////

function run_migrate () {
  # Vars
  # DATABASE_APP_USER_NAME=$(get_secret ".DATABASE_APP_USER_NAME")
  # DATABASE_APP_USER_PASSWORD=$(get_secret ".DATABASE_APP_USER_PASSWORD")
  # DATABASE_APP_NAME=$(get_secret ".DATABASE_APP_NAME")
  # DATABASE_APP_HOST=$(get_secret ".DATABASE_APP_HOST")
  # DATABASE_APP_PORT=$(get_secret ".DATABASE_APP_PORT")
  # --- replace vars that are docker specific for mig scripts
  if [[ $DATABASE_APP_HOST == "database_app" ]]
  then
    DATABASE_APP_HOST="localhost"
  fi
  # Migrate
  if [[ $1 == "rollback" ]]
  then
    echo "WARNING: You are about to rollback the '$TARGET_ENV' database."
    confirm_command
    DATABASE_APP_USER_NAME=$DATABASE_APP_USER_NAME \
    DATABASE_APP_USER_PASSWORD=$DATABASE_APP_USER_PASSWORD \
    DATABASE_APP_NAME=$DATABASE_APP_NAME \
    DATABASE_APP_HOST=$DATABASE_APP_HOST \
    DATABASE_APP_PORT=$DATABASE_APP_PORT \
      alembic downgrade -1
  elif [[ $1 == "head" ]]
  then
    DATABASE_APP_USER_NAME=$DATABASE_APP_USER_NAME \
    DATABASE_APP_USER_PASSWORD=$DATABASE_APP_USER_PASSWORD \
    DATABASE_APP_NAME=$DATABASE_APP_NAME \
    DATABASE_APP_HOST=$DATABASE_APP_HOST \
    DATABASE_APP_PORT=$DATABASE_APP_PORT \
      alembic upgrade head # TODO: allow taking a specific migration id or increment number
  else
    echo "Missing 'rollback' or 'head' command."
    exit 1
  fi
}

function run_seed () {
  # Vars
  # DATABASE_APP_USER_NAME=$(get_secret ".DATABASE_APP_USER_NAME")
  # DATABASE_APP_USER_PASSWORD=$(get_secret ".DATABASE_APP_USER_PASSWORD")
  # DATABASE_APP_NAME=$(get_secret ".DATABASE_APP_NAME")
  # DATABASE_APP_HOST=$(get_secret ".DATABASE_APP_HOST")
  # DATABASE_APP_PORT=$(get_secret ".DATABASE_APP_PORT")
  # --- replace vars that are docker specific for mig scripts
  if [[ $DATABASE_APP_HOST == "database_app" ]]
  then
    DATABASE_APP_HOST="localhost"
  fi
  # Migrate
  if [[ $TARGET_ENV == "local" ]]
  then
    echo "WARNING: Seed the '$TARGET_ENV' database? This action will wipe data."
    confirm_command
    DATABASE_APP_USER_NAME=$DATABASE_APP_USER_NAME \
    DATABASE_APP_USER_PASSWORD=$DATABASE_APP_USER_PASSWORD \
    DATABASE_APP_NAME=$DATABASE_APP_NAME \
    DATABASE_APP_HOST=$DATABASE_APP_HOST \
    DATABASE_APP_PORT=$DATABASE_APP_PORT \
      python seed.py
  else
    echo "You can only seed local and dev databases."
    exit 1
  fi
}

# //////////////////////////////////////////////////////////////////////////////
# Run
# //////////////////////////////////////////////////////////////////////////////
echo -e "${GREEN}manage.sh - Started${NC}"
COMMAND=$2
OPTION_ONE=$3
OPTION_TWO=$4

# Execute command
case "${COMMAND}" in
  # Setup
  setup)
  cd "$LATTICE_DATABASE_APP_PATH"
  pip install -r requirements.txt
  cd -
  confirm_finish
  exit 0
  ;;

  # Database - App
  migrate-app)
  confirm_command $COMMAND $OPTION_ONE $OPTION_TWO
  cd "$LATTICE_DATABASE_APP_PATH"
  run_migrate $OPTION_ONE $OPTION_TWO
  cd -
  confirm_finish
  exit 0
  ;;
  seed-app)
  confirm_command $COMMAND $OPTION_ONE $OPTION_TWO
  cd "$LATTICE_DATABASE_APP_PATH"
  run_seed
  cd -
  confirm_finish
  exit 0
  ;;

  # Unhandled
  *)
  echo "Unrecognized Command: '${2}'"
  exit 1
  ;;
esac
