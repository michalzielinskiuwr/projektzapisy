import psycopg2
import json

PASS_ANONIM = "pbkdf2_sha256$36000$Z6GlerjZ9cWC$M6zn6XGPc81913R1yw6SMouredUfO/DPnQwZ3XxUCnA="

"""
def anonimize_poll_(conn):
    cur = conn.cursor()
    query = "select PS.id PS.answers from poll_submission PS"
    cur.execute(query)
    poll_records = cur.fetchall()
    for row in poll_records:
        json_src = json.loads(row[1])
        for field in json_src['schema']:
            if field['type'] == 'textarea':
                field['answer'] == 'ans'
            elif field['type'] == 'radio':
                field['answer'] = field['choices'][0]
        json_dest = json.dumps(json_src)
        cur.execute('update poll_submission set answers = %s where id = %s', (json_dest, row[0]))    
    cur.close()
    conn.commit()
"""

# TODO exceptions
def anonimize_poll(conn):
    cur = conn.cursor()
    # create answers from schemas
    query = "select PS.id, PS.questions from poll_schema PS"
    cur.execute(query)
    schemas = cur.fetchall()
    jsons_dict = dict()
    for row in schemas:
        json_src = json.loads(row[1])
        for field in json_src['schema']:
            if field['type'] == 'textarea':
                field['answer'] == 'ans'
            elif field['type'] == 'radio':
                field['answer'] = field['choices'][0]
            json_dest = json.dumps(json_src)
            jsons_dict[row[0]] = json_dest
    # insert answers to sumbissions based on schema type
    query = "select SUB.id, SUB.schema_id from poll_submission SUB"
    cur.execute(query)
    polls = cur.fetchall()
    for row in polls:
    	cur.execute("update poll_submission set answers = %s where id = %s", (jsons_dict[row[1]], row[0]))
    cur.close()
    conn.commit()

# TODO exceptions
def anonimize_dev_database(conn):
    cur = conn.cursor()
    # Nuke IBANs
    cur.execute("UPDATE users_studiazamawiane SET bank_account=''")
    # Anonymize first/last names
    cur.execute("UPDATE auth_user SET first_name=CONCAT(SUBSTRING(first_name, 1, 1), '_', id)")
    cur.execute("UPDATE auth_user SET last_name=CONCAT(SUBSTRING(last_name, 1, 1), '_', id)")
    # Delete api tokens
    cur.execute("UPDATE authtoken_token SET key='niepoprawnytoken'")
    # Anonymize/remove email addresses
    cur.execute("UPDATE auth_user SET email='email@example.org'")
    cur.execute("DELETE FROM mailer_message")
    cur.execute("DELETE FROM mailer_messagelog")
    # Make sure everyone has the same simple password, in this case, 'pass'
    # See here: https://docs.djangoproject.com/en/2.0/topics/auth/passwords/
    cur.execute("UPDATE auth_user SET password= %s", (PASS_ANONIM))

    cur.close()
    conn.commit()
    anonimize_poll(conn)
