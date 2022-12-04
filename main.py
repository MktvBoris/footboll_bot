import sys
from threading import Thread

from time import sleep, localtime
from loguru import logger

from config_data.config import CONNECT_TO_BASE
from datadase.count_table import CountList
from datadase.dumplist_table import DumpList
from datadase.sentlist_table import SentList
from datadase.statlist_table import StatList, check_statistic
from utilities.backup_db import send_db
from utilities.check_all_games import check_all_games
from utilities.check_game import check_game
from utilities.check_result import sleep_check_result
from utilities.driver import get_driver


@logger.catch
def connect_to_base(headless) -> bool:
    """
    Функция подключается к сайту, выбирает матчи и проверяет их
    """
    base_url = "https://1xstavka.ru/live/football"
    browser = get_driver(headless)
    try:
        browser.get(base_url)
    except Exception:
        logger.info(f"Error connecting to {base_url}.")
        browser.quit()
        return False
    sleep(1)
    page = browser.page_source
    browser.quit()

    all_games = check_all_games(page)
    if not all_games:
        sleep(60)
        return False
    else:
        logger.info(f'There were matches: {len(all_games)}.')
        for current_game in all_games:
            check_game(current_game)
        return True


def result_check() -> None:
    """
    Функция запускает проверку результатов матча и статистику в заданное время
    """
    while True:
        try:
            sleep(1)
            time_now = localtime()
            if time_now.tm_min in (5, 15, 25, 35, 45, 55):
                sleep_check_result()
                sleep(60)
            elif time_now.tm_hour == 8 and time_now.tm_min == 0:
                check_statistic()
                send_db()
                sleep(60)
        except Exception:
            pass


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <yellow>{message}</yellow>", level="INFO"
    )
    logger.add(
        "runtime.log", rotation="1 days", retention="3 days",
        format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}"
    )
    logger.info("The bot is running")

    CONNECT_TO_BASE.create_tables([SentList, DumpList, StatList, CountList])
    CONNECT_TO_BASE.close()

    Thread(target=result_check).start()

    while True:
        try:
            connect_to_base(headless=True)
        except KeyboardInterrupt:
            logger.info("Completion of work")
            sys.exit()
        except Exception:
            continue
