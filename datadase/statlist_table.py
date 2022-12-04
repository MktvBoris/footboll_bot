from typing import Dict, Set

from loguru import logger
from peewee import AutoField, TextField, IntegerField

from config_data.config import CONNECT_TO_BASE, ID_CHAT, PARTNERS_URL
from datadase.count_table import BaseModel
from datadase.sentlist_table import get_sentlist
from loader_telebot import bot


class StatList(BaseModel):
    """
    StatList
    """
    stat_id = AutoField(column_name='sent_id')
    name_stat = TextField(column_name='name_stat', index=True)
    win = IntegerField(column_name='win', default=0)
    all = IntegerField(column_name='all', default=0)


@logger.catch
def add_all_statlist(name_stats: Set) -> None:
    """
    Функция добавляет статистику all в таблицу StatList.
    """
    for name_stat in name_stats:
        query = StatList.select().where(StatList.name_stat == name_stat)

        if not query.exists():
            StatList.create(name_stat=name_stat, all=1)
        else:
            row = StatList.get(StatList.name_stat == name_stat)
            row.all = row.all + 1
            row.save()

    CONNECT_TO_BASE.close()


@logger.catch
def add_win_statlist(name_stats: Set) -> None:
    """
    Функция добавляет статистику win в таблицу StatList.
    """
    for name_stat in name_stats:
        query = StatList.select().where(StatList.name_stat == name_stat)

        if not query.exists():
            StatList.create(name_stat=name_stat)

        row = StatList.get(StatList.name_stat == name_stat)
        row.win = row.win + 1
        row.save()

    CONNECT_TO_BASE.close()


@logger.catch
def get_statlist(name_stat: str) -> bool | Dict:
    """
    Функция возвращает записи в таблице StatList.
    """

    query = StatList.select().where(StatList.name_stat == name_stat)
    if not query.exists():
        return False
    else:
        result = {}
        row = StatList.get(StatList.name_stat == name_stat)
        result['win_rate'], result['win'], result['all'] = (row.win * 100) / row.all, row.win, row.all

        return result


@logger.catch
def check_statistic() -> None:
    logger.info("Processing match statistics")
    result = get_statlist('all')
    if not result:
        stat_str = 'Статистики нет'
    else:
        sent_list = get_sentlist()
        if sent_list:
            sent_str = f'\nНе рассчитанные: {len(sent_list)}'
        else:
            sent_str = ''

        stat_str = f'Статистика: {round(result["win_rate"])}%' \
                   f'\nВсего сигналов: {result["all"]} Выиграло: {result["win"]}{sent_str}' \
                   f'\n<b>1XСТАВКА</b>, лучшая легальная букмекерская контора на территории РФ. ' \
                   f'Забудь о блокировках, букмекер своевременно и в полном объеме выплачивает выигрыши игроку. ' \
                   f'Большой выбор ставок, видов спорта и событий, акции и многое другое. ' \
                   f'Используй промо-код <code>1xs_11826</code> при регистрации и получи увеличенный бонус. ' \
                   f'<a href="{PARTNERS_URL}">Зарегистрироваться в 1XСТАВКА</a>' \


    bot.send_message(chat_id=ID_CHAT, text=stat_str, parse_mode='html')
