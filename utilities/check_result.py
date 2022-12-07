from time import sleep

from bs4 import BeautifulSoup
from loguru import logger

from config_data.config import ID_CHAT
from datadase.sentlist_table import out_sentlist, get_sentlist, delete_sentlist
from datadase.statlist_table import add_win_statlist, add_all_statlist
from loader_telebot import bot
from utilities.driver import get_driver


@logger.catch()
def sleep_check_result() -> None:
    """
    Функция проверяет результат матча
    """
    logger.info("Processing the results of matches")
    out_sentlist()
    game_all = get_sentlist()
    if not game_all:
        return
    browser = get_driver(headless=True)
    for game in game_all:
        url_game = game['url_stats']
        browser.get(url_game)
        sleep(1)

        soup = BeautifulSoup(browser.page_source, 'lxml')
        scoreboard_info = soup.find_all(
            "div",
            class_="st-scoreboard__info st-scoreboard__info--main st-scoreboard-info st-scoreboard-info--main"
        )
        if scoreboard_info:
            scoreboard_info_all = [text.strip() for text in scoreboard_info[0].text.split('\n') if text.strip() != '']
        else:
            continue
        if 'Матч состоялся' in scoreboard_info_all or 'Match finished' in scoreboard_info_all:
            score = scoreboard_info_all[2]

        elif 'После серии пенальти' in scoreboard_info_all or 'After penalty shootout' in scoreboard_info_all:
            score = scoreboard_info_all[2][1:-1]
        else:
            continue

        goals_time = ''
        if score:
            text = game['text_message']
            scores = [int(symbol) for symbol in score if symbol.isdigit()]
            if sum(scores) == 0:
                continue
            elif game['score_sum'] != sum(scores):
                match_chronicles = soup.find_all(
                    "div",
                    class_="match-chronicle__row-event"
                )

                # Добавляем время голов

                if match_chronicles:
                    trigger = False
                    start = 1
                    for row in reversed(match_chronicles):
                        if start == 1 and row.text.strip() not in ('1 Тайм', '1 Half'):
                            break
                        start += 1

                        if row.text.strip() in ('2 Тайм', '2 Half'):
                            trigger = True
                        elif row.text.strip() in ('ОТ', 'Overtime'):
                            break
                        if not trigger:
                            continue
                        check_row = row.find_all(
                            "svg", class_='st-svg-ico st-svg-ico--soccer-ball st-svg-ico--black has-tooltip')
                        check_row_red = row.find_all(
                            "svg", class_='st-svg-ico st-svg-ico--soccer-ball st-svg-ico--red has-tooltip')
                        if check_row or check_row_red:
                            goal_time = row.find_all('div', class_='match-chronicle__time')
                            if goal_time and check_row:
                                goals_time += f' ⚽{goal_time[0].text.strip()}'
                            else:
                                # Добавляем вопросительный знак, так как красный мяч = незабитый пенальти или автогол
                                goals_time += f' ⚽? {goal_time[0].text.strip()}'
                if goals_time:
                    goals_time = goals_time + '\n'
                text_message = text + f'\n✅'
                add_win_statlist({'all', game['liga_names']})
            else:
                text_message = text + f'\n❌'

            bot.edit_message_text(
                chat_id=ID_CHAT, message_id=game['id_message'], parse_mode='html',
                text=text_message + f' <i>Счет {score} {goals_time}<a href="{url_game}">Статистика матча</a></i>')

            add_all_statlist({'all', game['liga_names']})
            delete_sentlist(game['sent_id'])
    browser.quit()
