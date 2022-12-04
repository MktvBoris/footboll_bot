import re
from time import sleep
from typing import Dict, List

from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By

from config_data.config import ATTACKS, DANGEROUS_ATTACKS, SHOTS_ON_TARGET, SHOTS_TOWARDS_THE_GOAL, ID_CHAT, \
    PARTNERS_URL, CORNER_CHECK, CORNERS
from datadase.count_table import get_countlist, add_countlist
from datadase.dumplist_table import add_dumplist, check_dumplist
from datadase.sentlist_table import add_sentlist, check_sentlist
from datadase.statlist_table import get_statlist
from loader_telebot import bot
from utilities.driver import get_driver


@logger.catch
def filter_stats(string) -> str | List:
    """
    Функция фильтрует значения статистики игры
    """
    string = string.text.strip()
    if '\n' in string:
        strings = [int(elem.strip()) for elem in string.split()]
        return strings

    return string


@logger.catch
def filter_events(string) -> str | int:
    """
    Функция фильтрует события игры
    """
    string_title = string.get('title')
    if string_title == 'Красные карточки':
        return string_title
    elif string_title == 'Угловые':
        string = int(string.text.strip())
        return string
    else:
        return 0


@logger.catch
def check_game(game: Dict) -> bool:
    """
    Функция матч подходит ли по критерию
    """

    if check_sentlist(game['url']) or check_dumplist(game['url']):
        return False

    pattern: str = r'(?<=https://1xstavka.ru/).+'
    url_start: str = 'https://eventsstat.com/'

    browser = get_driver(headless=True)
    browser.get(game['url'])

    sleep(1)
    page = browser.page_source
    soup = BeautifulSoup(page, 'lxml')

    # Проверяем есть ли события по игре (необходимы для отслеживания результатов)
    actions_btn: List = browser.find_elements(By.CLASS_NAME, 'event-actions-btn__svg')
    if actions_btn:
        actions_btn[0].click()
    else:
        logger.info(f"{game['url']} Нет event-actions-btn__svg")
        add_dumplist(game['url'])
        browser.quit()
        return False
    sleep(1)
    events_btn: List = browser.find_elements(By.CLASS_NAME, 'event-statistics__btn')
    if not events_btn:
        logger.info(f"{game['url']} Нет кнопок в действии")
        add_dumplist(game['url'])
        browser.quit()
        return False
    else:
        for btn in events_btn:
            if btn.text == 'Статистика':
                btn.click()
                browser.switch_to.window(browser.window_handles[1])
                url = browser.current_url
                url_stats = url_start + re.search(pattern, url).group(0)
                browser.quit()
                break
        else:
            logger.info(f"{game['url']} Нет кнопки 'Статистика'")
            add_dumplist(game['url'])
            browser.quit()
            return False

    # Получаем общее табло игры
    results = soup.find_all("div", class_="mainTablo")
    if not results:
        logger.info(f"{game['url']} Нет табло")
        add_dumplist(game['url'])
        return False

    # Получаем статистику матча
    stats = results[0].find_all("div", class_="c-chart-stat__row")
    if not stats:
        logger.info(f"{game['url']} Нет статистики матча")
        add_dumplist(game['url'])
        return False
    stats = [filter_stats(string) for string in stats]
    if len(stats) != 10:
        logger.info(f"{game['url']} Не вся статистика матча")
        add_dumplist(game['url'])
        return False

    # Проверяем по нужным критериям
    flag = True
    for index in range(0, len(stats), 2):
        if stats[index] == 'Атаки':
            if stats[index + 1][0] + stats[index + 1][1] < ATTACKS:
                flag = False
        elif stats[index] == 'Опасные атаки':
            if stats[index + 1][0] + stats[index + 1][1] < DANGEROUS_ATTACKS:
                flag = False
        elif stats[index] == 'Удары в створ':
            if stats[index + 1][0] + stats[index + 1][1] < SHOTS_ON_TARGET:
                flag = False
        elif stats[index] == 'Удары в сторону ворот':
            if stats[index + 1][0] + stats[index + 1][1] < SHOTS_TOWARDS_THE_GOAL:
                flag = False
        elif stats[index] == 'Владение мячом %':
            if abs(stats[index + 1][0] - stats[index + 1][1]) > 10:
                if stats[index + 1][0] > stats[index + 1][1] and game['looser_id'] == 1:
                    flag = False
                elif stats[index + 1][0] < stats[index + 1][1] and game['looser_id'] == 2:
                    flag = False
    if not flag:
        return False

    tablo_str = ''
    for index in range(0, len(stats), 2):
        tablo_str += f'{stats[index]} {stats[index + 1][0]} - {stats[index + 1][1]}\n'

    # Получаем угловые матча
    c_tablo = soup.find_all("div", class_="c-tablo__main c-tablo-main")
    if not c_tablo:
        logger.info(f"{game['url']} Нет правого табло")
        add_dumplist(game['url'])
        return False
    c_tablo_all = c_tablo[0].find_all("div", class_="o-tablo-info-list u-asfe c-tablo__event-info")
    if not c_tablo_all:
        corner_one = 0
        corner_two = 0
    else:
        event_one = c_tablo_all[0].find_all("div", class_="c-tablo-event")
        if not event_one:
            corner_one = 0
        else:
            events_one = [filter_events(event) for event in event_one]
            if 'Красные карточки' in events_one:
                add_dumplist(game['url'])
                logger.info(f"{game['url']} В матче красная карточка")
                return False
            else:
                corner_one = sum(events_one)

        if len(c_tablo_all) < 2:
            corner_two = 0
        else:
            events_two = c_tablo_all[1].find_all("div", class_="c-tablo-event")
            if not events_two:
                corner_two = 0
            else:
                events_two = [filter_events(event) for event in events_two]
                if 'Красные карточки' in events_two:
                    add_dumplist(game['url'])
                    return False
                else:
                    corner_two = sum(events_two)

    if CORNER_CHECK:
        if corner_one + corner_two < CORNERS:
            return False

    tablo_str += f'Угловые {corner_one} - {corner_two}\n'

    # Получаем котировки матча
    bets = soup.find_all("div", class_="bet_group")
    if not bets:
        logger.info(f"{game['url']} Нет котировок")
        add_dumplist(game['url'])
        return False

    for group in bets:
        name_bet = group.find_all("span", class_="bet-title__label bet-title__text bet-title-label")
        if 'Тотал' == name_bet[0].text.strip():
            bet = group.find_all("span", class_="bet_type")
            if bet[0].text.strip() != f'{game["score_sum"]}.5 Б':
                logger.info(f"{game['url']} Не верная котировка {bet[0].text.strip()}")
                add_dumplist(game['url'])
                return False
            kf = group.find_all("i", class_="koeff__label")
            bet_str = f'Тотал: {bet[0].text.strip()} - {kf[0].text.strip()}'
            try:
                bet_str += f', {bet[2].text.strip()} - {kf[2].text.strip()}'
            except IndexError:
                pass

            # Получаем статистику по чемпионату
            liga_rate = get_statlist(game["liga"])
            if liga_rate:
                star_rating = round(liga_rate["win_rate"])
                star = '🏅'
                if 20 < star_rating <= 40:
                    star += '🏅'
                elif 40 < star_rating <= 60:
                    star += '🏅🏅'
                elif 60 < star_rating <= 80:
                    star += '🏅🏅🏅'
                elif 80 < star_rating <= 100:
                    star += '🏅🏅🏅🏅'
                stat_str = f'\nСтатистика лиги: {star_rating}% {star}\n' \
                           f'Всего: {liga_rate["all"]} Выиграно: {liga_rate["win"]}'
            else:
                stat_str = ''

            count_message = get_countlist('count')

            text_message = f'<i>#{count_message} Будет гол!\n' \
                           f'🏆 {game["liga"]}\n' \
                           f'⚽ <code>{game["teams"]}</code>\n' \
                           f'Счет: {game["score"]} ' \
                           f'Время {game["time"]}\n' \
                           f'{tablo_str}' \
                           f'{bet_str}{stat_str}' \
                           f'\n<a href="{PARTNERS_URL}">Зарегистрироваться</a>/' \
                           f'<a href="{game["url"]}">Ставить на матч</a></i>'

            # Добавляем в список отправленных и отправляем в чат сигнал
            current_id_message = (
                bot.send_message(chat_id=ID_CHAT, text=text_message, parse_mode='html')).id

            add_sentlist(
                url_stats=url_stats, url=game["url"], id_message=current_id_message,
                text_message=text_message, score_sum=game['score_sum'], liga_names=game["liga"])

            add_countlist('count')
            return True
    else:
        logger.info(f"{game['url']} Нет котировки 'Тотал'")
        add_dumplist(game["url"])
        return False
