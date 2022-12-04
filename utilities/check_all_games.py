from typing import List

from bs4 import BeautifulSoup
from loguru import logger

from config_data.config import OUT_LIST, TIME_SORT_START, TIME_SORT_END, SCORE_DIFFERENCE, SCORE_ONE_TIME, \
    CHECK_CUR_SCORES
from datadase.dumplist_table import check_dumplist, add_dumplist
from datadase.sentlist_table import check_sentlist


@logger.catch
def check_all_games(page) -> List | bool:
    """
    Функция выбирает из матчей в лайф подходящие по критерию
    """

    soup = BeautifulSoup(page, 'lxml')

    # Получаем лиги
    results = soup.find_all("div", class_="dashboard-champ-content")
    if not results:
        logger.info("Нет лиг")
        return False

    clean_result: List = []
    for result in results:
        current_game = {}

        # Получаем имя лиги
        liga_name = result.find_all("div", class_="c-events__name")
        if not liga_name:
            logger.info("Нет имени лиги")
            continue
        else:
            name = liga_name[0].find_all("a", class_="c-events__liga")
            if not name:
                logger.info("Нет имени лиги")
                continue
            name = name[0].text.strip()
            if set(name.split()) & OUT_LIST:  # Проверяем есть ли лига в мусорных лигах
                continue

        # Получаем матчи
        games = result.find_all("div", class_="c-events__item c-events__item_col")
        if not games:
            logger.info("Нет матча в лиге")
            continue
        for game in games:
            url = game.find_all("a")
            if not url:
                continue

            # Получаем ссылку на матч
            url = 'https://1xstavka.ru/' + url[0].get('href')
            if check_sentlist(url) or check_dumplist(url):
                continue

            # Получаем время матча
            time = game.find_all("div", class_="c-events__time")
            if not time:
                continue
            time = time[0].text.strip()

            if time[0:2].isdigit():
                time_check: int = int(time[0:2])
            else:
                logger.info("Время не цифра")
                continue
            if not TIME_SORT_START < time_check < TIME_SORT_END:
                if time_check > TIME_SORT_END:
                    add_dumplist(url)
                continue
            if time.endswith(f'{time_check} 1-й Тайм'):
                continue
            # Получаем счет матча и проверяем по нужному критерию
            scores = game.find_all("span", class_="c-events-scoreboard__cell")
            if not scores or len(scores) not in (4, 6):
                logger.info("Счета нет")
                continue
            scores = [int(score.text.strip()) for score in scores]
            score_one_team, score_one_team_1t = scores[0], scores[1]
            if len(scores) == 4:
                score_two_team, score_two_team_1t = scores[2], scores[3]
            else:
                score_two_team, score_two_team_1t = scores[3], scores[4]

            scores_cur, scores_1t = score_one_team + score_two_team, score_one_team_1t + score_two_team_1t
            if (
                    score_one_team - score_two_team == SCORE_DIFFERENCE
                    or score_one_team_1t + score_two_team_1t == SCORE_ONE_TIME
                    or CHECK_CUR_SCORES and scores_cur != scores_1t
            ):
                continue

            # Получаем названия команд
            team_names = game.find_all("div", class_="c-events__team")
            if not team_names:
                logger.info("Нет названия команд")
                continue
            team_one, team_two = team_names[0].text.strip(), team_names[1].text.strip()

            if score_one_team > score_two_team:
                looser_id = 2
                looser = team_two
                winner = team_one
            else:
                looser_id = 1
                looser = team_one
                winner = team_two

            # Добавляем в словарь нужные значения
            current_game['looser_id'] = looser_id
            current_game['liga'] = name
            current_game['teams'] = f'{team_one} - {team_two}'
            current_game['looser'] = looser
            current_game['winner'] = winner
            current_game['time'] = time
            current_game['url'] = url
            current_game['score'] = f'{score_one_team} - {score_two_team}'
            current_game['score_sum'] = score_one_team + score_two_team
            clean_result.append(current_game)

    return clean_result
