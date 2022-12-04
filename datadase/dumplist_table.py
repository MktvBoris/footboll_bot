from datetime import datetime

from loguru import logger
from peewee import AutoField, TextField, DateTimeField

from config_data.config import CONNECT_TO_BASE
from datadase.count_table import BaseModel


class DumpList(BaseModel):
    """
    DumpList
    """
    sent_id = AutoField(column_name='sent_id')
    url = TextField(column_name='url', index=True)
    created_date = DateTimeField(column_name='created_date')


@logger.catch
def add_dumplist(url: str) -> None:
    """
    Функция добавляет матч в таблицу SentList.
    """
    now = datetime.now()
    full_list = DumpList.select().order_by(DumpList.created_date)
    if full_list.count() == 50:
        full_list[0].delete_instance()

    query = DumpList.select().where(DumpList.url == url)
    if not query.exists():
        DumpList.create(url=url, created_date=now)

    CONNECT_TO_BASE.close()


@logger.catch
def check_dumplist(url: str) -> bool:
    """
    Функция проверяет есть ли запись с таким url в таблице DumpList.
    """
    full_list = [ex.url for ex in DumpList.select()]
    if url in full_list:
        CONNECT_TO_BASE.close()
        return True
    else:
        CONNECT_TO_BASE.close()
        return False
