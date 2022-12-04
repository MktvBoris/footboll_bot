from loguru import logger
from webdav3.client import Client
from webdav3.exceptions import WebDavException

from config_data.config import LOGIN_MAIL, PASS_MAIL


@logger.catch
def send_db() -> None:
    """
    Функция отправляет копию БД в облако
    """
    data = {
        'webdav_hostname': "https://webdav.cloud.mail.ru",
        'webdav_login': LOGIN_MAIL,
        'webdav_password': PASS_MAIL
    }
    try:
        client = Client(data)

        if not client.check('backup'):
            client.mkdir('backup')
        if client.check("backup/db_75.sqlite"):
            client.clean('backup/db_75.sqlite')

        client.upload_sync(remote_path="backup/db_75.sqlite", local_path='db_75.sqlite')
    except WebDavException:
        pass
