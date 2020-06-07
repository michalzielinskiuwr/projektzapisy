import psycopg2
import json
import sys

# TODO exceptions
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
                field['answer'] = 'ans'
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
        cur.execute("update poll_submission set answers = %s where id = %s", (jsons_dict[row[1]], row[0]))
    cur.close()
    conn.commit()

def connect_and_anonymize():
    if len(sys.argv) < 5:
        sys.exit(1)
    try:
        conn = psycopg2.connect(dbname=sys.argv[3], user=sys.argv[1],
            password=sys.argv[2], host="localhost", port=sys.argv[4])
        anonymize_poll(conn)
    except Exception as e:
        print(str(e))
        sys.exit(1)

def main():
    conn = connect_and_anonymize()
    sys.exit(0)

if __name__ == '__main__':
    main()