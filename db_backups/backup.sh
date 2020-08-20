
# exit when returns non-zero
set -e

OUTFILE_PATH_PROD="$1"
OUTFILE_PATH_DEV="$2"
TEMP_DUMP_PATH_PROD='/tmp/ii_zapisy_dump_prod.sql'
TEMP_DUMP_PATH_DEV='/tmp/ii_zapisy_dump_dev.sql'
TEMP_DB_NAME='II_ZAPISY_BACKUP_TEMP_DB'


read_variables()
{
    file="$PWD/../env/.env"
    while IFS="=" read -r key value; do
        case "$key" in
            "DATABASE_NAME") DATABASE_NAME="$value" ;;
            "DATABASE_USER") DATABASE_USER="$value" ;;
            "DATABASE_PASSWORD") DATABASE_PASSWORD="$value" ;;
            "DATABASE_PORT") DATABASE_PORT="$value" ;;
            "DATABASE_DUMP_PASSWORD") DATABASE_DUMP_PASSWORD="$value" ;;
        esac
    done < "$file"
}


read_variables

[ -z "${DATABASE_NAME}" ] && echo "Secret variable is missing" && exit 1;
[ -z "${DATABASE_USER}" ] && echo "Secret variable is missing" && exit 1;
[ -z "${DATABASE_PASSWORD}" ] && echo "Secret variable is missing" && exit 1;
[ -z "${DATABASE_PORT}" ] && echo "Secret variable is missing" && exit 1;
[ -z "${DATABASE_DUMP_PASSWORD}" ] && echo "Secret variable is missing" && exit 1;

# check if 7za is installed
if ! [ -x "$(command -v 7za)" ]; then
  echo "p7zip-full is requiredddd." >&2
  exit 2
fi

# save prod database to temp file
PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
-U "${DATABASE_USER}" -h localhost -p "${DATABASE_PORT}" \
"${DATABASE_NAME}" > "$TEMP_DUMP_PATH_PROD"

# reload database as temp
sudo -su postgres psql -c "DROP DATABASE IF EXISTS \"$TEMP_DB_NAME\";"
sudo -su postgres psql -c "CREATE DATABASE \"$TEMP_DB_NAME\";"
PGPASSWORD="${DATABASE_PASSWORD}" psql -U "${DATABASE_USER}" -h localhost \
-p "${DATABASE_PORT}" -d "$TEMP_DB_NAME" < "$TEMP_DUMP_PATH_PROD"

# anonymize elements:
#   students' data, passwords
PGPASSWORD="${DATABASE_PASSWORD}" psql -U "${DATABASE_USER}" -h localhost \
-p "${DATABASE_PORT}" -f anonymize.sql "$TEMP_DB_NAME" 
#   poll - TODO install psycopg2
python anonymize.py -u "${DATABASE_USER}" -ps "${DATABASE_PASSWORD}" -db "$TEMP_DB_NAME" \
-p "${DATABASE_PORT}"

# save dev database to temp file
PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
-U "${DATABASE_USER}" -h localhost -p "${DATABASE_PORT}" \
"$TEMP_DB_NAME" > "$TEMP_DUMP_PATH_DEV"

sudo -su postgres psql -c "DROP DATABASE \"$TEMP_DB_NAME\";"

# compress files
7za a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on "$OUTFILE_PATH_DEV" "$TEMP_DUMP_PATH_DEV"
7za a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on -p"$DATABASE_DUMP_PASSWORD" \
"$OUTFILE_PATH_PROD" "$TEMP_DUMP_PATH_PROD"

# remove temp dumps
rm "$TEMP_DUMP_PATH_DEV"
rm "$TEMP_DUMP_PATH_PROD"
