from datetime import datetime
from typing import List

from loguru import logger
from peewee import AutoField, TextField, BooleanField, DateTimeField, IntegerField

from config_data.config import CONNECT_TO_BASE, ID_CHAT
from datadase.count_table import BaseModel
from loader_telebot import bot


class SentList(BaseModel):
    """
    SentList
    """
    sent_id = AutoField(column_name='sent_id')
    url = TextField(column_name='url', index=True)
    url_stats = TextField(column_name='url_stats')
    issue = BooleanField(column_name='issue', index=True, default=False)
    created_date = DateTimeField(column_name='created_date')
    id_message = IntegerField(column_name='id_message')
    text_message = TextField(column_name='text_message')
    score_sum = IntegerField(column_name='score_sum')
    liga_names = IntegerField(column_name='liga_names', null=True)


@logger.catch
def add_sentlist(url: str, url_stats: str, id_message: int, text_message: str, score_sum: int, liga_names: str) -> None:
    """
    Функция добавляет матч в таблицу SentList.
    """
    now = datetime.now()
    full_list = SentList.select().order_by(SentList.created_date)
    if full_list.count() == 50:
        full_list[0].delete_instance()

    query = SentList.select().where(SentList.url == url)
    if not query.exists():
        SentList.create(
            url=url, url_stats=url_stats, id_message=id_message,
            text_message=text_message, score_sum=score_sum,
            liga_names=liga_names, created_date=now
        )

    CONNECT_TO_BASE.close()


@logger.catch
def delete_sentlist(sent_id: int) -> None:
    """
    Функция удаляет запись по sent_id в таблице SentList.
    """
    row = SentList.get(SentList.sent_id == sent_id)
    row.delete_instance()

    CONNECT_TO_BASE.close()


def out_sentlist():
    """
    Функция удаляет не рассчитанные ставки в таблице SentList.
    """
    full_list = SentList.select()
    for elem in full_list:
        today = datetime.now()
        created_date = elem.created_date
        time_deltadays = (today - created_date).days
        if time_deltadays > 1:
            text = elem.text_message
            message_id = elem.id_message
            text_message = text + f'\n⍻ Результаты не найдены.'

            bot.edit_message_text(
                chat_id=ID_CHAT, message_id=message_id,
                text=text_message, parse_mode='html')
            elem.delete_instance()
            CONNECT_TO_BASE.close()
            break
    return True


@logger.catch
def check_sentlist(url: str) -> bool:
    """
    Функция проверяет есть ли запись с таким url в таблице SentList.
    """
    full_list = [ex.url for ex in SentList.select()]

    if url in full_list:
        CONNECT_TO_BASE.close()
        return True
    else:
        CONNECT_TO_BASE.close()
        return False


@logger.catch
def get_sentlist() -> List | bool:
    """
    Функция возвращает записи из таблицы SentList.
    """
    full_list: List = [{'sent_id': ex.sent_id, 'url': ex.url,
                        'url_stats': ex.url_stats,
                        'id_message': ex.id_message,
                        'text_message': ex.text_message,
                        'score_sum': ex.score_sum,
                        'liga_names': ex.liga_names
                        } for ex in SentList.select()]
    if full_list:
        CONNECT_TO_BASE.close()
        return full_list
    else:
        CONNECT_TO_BASE.close()
        return False
