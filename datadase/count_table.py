from datetime import datetime

from loguru import logger
from peewee import AutoField, TextField, IntegerField, Model

from config_data.config import CONNECT_TO_BASE

now = datetime.now


class BaseModel(Model):
    """
    Базовая модель
    """

    class Meta:
        database = CONNECT_TO_BASE


class CountList(BaseModel):
    """
    CountList
    """
    stat_id = AutoField(column_name='sent_id')
    name = TextField(column_name='name_stat', index=True)
    number_sent = IntegerField(column_name='number_sent', default=0)


@logger.catch
def add_countlist(name: str) -> None:
    """
    Функция прибавляет счетчик в таблицу CountList.
    """

    query = CountList.select().where(CountList.name == name)

    if not query.exists():
        CountList.create(name=name, number_sent=1)
    else:
        row = CountList.get(CountList.name == name)
        row.number_sent = row.number_sent + 1
        row.save()

    CONNECT_TO_BASE.close()


@logger.catch
def get_countlist(name: str) -> int:
    """
    Функция возвращает записи в таблице StatList.
    """

    query = CountList.select().where(CountList.name == name)
    if not query.exists():
        CountList.create(name=name, number_sent=1)
        CONNECT_TO_BASE.close()
        return 1
    else:
        row = CountList.get(CountList.name == name)
        CONNECT_TO_BASE.close()
        return row.number_sent
