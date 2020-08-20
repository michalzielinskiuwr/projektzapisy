import psycopg2
import argparse
import json
import sys
from loremipsum import generate_paragraph


def anonymize_poll(conn):
    cur = conn.cursor()
    # create answers from schemas
    query = "select PS.id, PS.questions from poll_schema PS"
    cur.execute(query)
    schemas = cur.fetchall()
    jsons_dict = dict()
    for row in schemas:
        json_src = row[1]
        for field in json_src['schema']:
            if field['type'] == 'textarea':
                field['answer'] = generate_paragraph()[2]
            elif field['type'] == 'radio':
                field['answer'] = field['choices'][0]
            json_dest = json.dumps(json_src)
            jsons_dict[row[0]] = json_dest
    # insert answers to sumbissions based on schema type
    query = "select SUB.id, SUB.schema_id from poll_submission SUB"
    # to add to query (?) where submitted = 't'
    cur.execute(query)
    polls = cur.fetchall()
    for row in polls:
        cur.execute("update poll_submission set answers = %s where id = %s",
                    (jsons_dict[row[1]], row[0]))
    cur.close()
    conn.commit()


def connect_and_anonymize(args):
    try:
        conn = psycopg2.connect(dbname=args.database_name, user=args.user,
                                password=args.password, host="localhost", port=args.port)

        anonymize_poll(conn)
    except Exception as e:
        print(str(e))
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', required=True)
    parser.add_argument('-ps', '--password', required=True)
    parser.add_argument('-db', '--database_name', required=True)
    parser.add_argument('-p', '--port', required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    conn = connect_and_anonymize(args)
    sys.exit(0)


if __name__ == '__main__':
    main()
