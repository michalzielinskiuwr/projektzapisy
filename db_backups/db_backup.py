import subprocess
import os
import environ
import traceback
import time
from datetime import datetime, timedelta

import anonymize
from slack_notifications import connect_slack_client, send_success_notification, \
    send_error_notification
from dropbox_upload import upload_dumps


def get_secrets():
    env = environ.Env()
    secrets_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                     os.pardir, 'env', '.env')
    environ.Env.read_env(secrets_file_path)
    return env


def get_filename(suff):
    time_now_str = time.strftime('%Y_%m_%d__%H_%M_%S')
    path = f'/tmp/ii_zapisy_db_dump_{time_now_str}_{suff}'
    return f'{path}.7z'


def perform_dump(secrets_env):
    prod_filename = get_filename('prod')
    dev_filename = get_filename('dev')
    # full dump - prod and dev
    res = subprocess.run(["sh", "backup.sh", prod_filename, dev_filename],
                         stderr=subprocess.PIPE)
    if res.returncode != 0:
        error_str = res.stderr.decode('utf-8')
        raise RuntimeError(
            f'backup.sh failed with error code {res.returncode}: {error_str}'
        )
    # send to dropbox
    dev_link = upload_dumps(secrets_env.str('DROPBOX_OAUTH2_TOKEN'), prod_filename,
                            dev_filename)
    return dev_link


def main():
    secrets_env = get_secrets()
    slack_client = connect_slack_client(secrets_env.str('SLACK_TOKEN'))
    try:
        start_time = datetime.now()
        # perform dump
        dev_link = perform_dump(secrets_env)
        end_time = datetime.now()
        seconds_elapsed = (end_time - start_time).seconds
        # send slack message
        send_success_notification(slack_client, dev_link.url, seconds_elapsed)
    except Exception:
        # send error slack massage
        err_description = traceback.format_exc()
        send_error_notification(slack_client, err_description)


if __name__ == '__main__':
    main()
