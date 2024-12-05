""" This file is used to download the flights data from xcontest.org.

Some tools and packages musts be installed to make this code functional :
    pandas --> https://pandas.pydata.org/docs/getting_started/install.html
        Warning : literal html is deprecated with raed_html() and will be removed in future versions.
        we have to use StringIO from io (https://docs.python.org/3/library/io.html#io.TextIOBase)
    selenium --> https://selenium-python.readthedocs.io/
    geckodriver --> https://stackoverflow.com/questions/40867959/installing-geckodriver-only-using-terminal

System info :
    os --> Debian bookworm (12)
    python --> 3.11.2
    pandas --> 2.2.3
    selenium -->4.26.1

More explication in comments along the code.
"""
from import_merra_files import alert_sender
import sys
import os
from selenium import webdriver # will run firefox
from selenium.webdriver.firefox.service import Service # will take the path to Geckodriver
from selenium.webdriver.common.by import By # used to find the looking tag
from selenium.webdriver.support.ui import WebDriverWait # used to wait for all features to load on the driver
from selenium.webdriver.support import expected_conditions as ec # used to specify what we are looking for on the page
from selenium.webdriver.firefox.options import Options
import pandas as pd
from io import StringIO
import logging
from datetime import datetime, timedelta
import time


def  setup_logger(log_dir, log_name):
    """

    :param log_dir:
    :param log_name:
    :return:
    """
    logger = logging.getLogger(log_name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    info_handler = logging.FileHandler(os.path.join(log_dir, 'infos.log'), mode="a")
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(info_formatter)

    error_handler = logging.FileHandler(os.path.join(log_dir, 'errors.log'), mode="a")
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


def flight_contest(services, option, years, contests, countries, pages, date):

    """

    :param services:
    :param option:
    :param years:
    :param contests:
    :param countries:
    :param pages:
    :param date:
    :return:
    """
    log = setup_logger("../Log/get_data", "flight_contest.log")
    driver = webdriver.Firefox(service=services, options=option)
    flight = None
    try:
        log.info(f"Downloading flights data {date} - {contests} - {countries}")
        if years == "2025":
            url = f"https://www.xcontest.org/{contests}/en/flights/#flights[sort]=reg@filter[country]={countries}@{pages}"
        else:
            url = f"https://www.xcontest.org/{year}/{contests}/en/flights/#filter[date]={date}@filter[country]={countries}@{pages}"
        driver.get(url)
        WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.TAG_NAME, "table")))
        html_content = driver.page_source
        html_file = StringIO(html_content)
        result = pd.read_html(html_file)
        driver.quit()
        flight = result[1]
    except Exception as exc:
        log.error(f"Error {exc} for {contests} {countries} {date} {pages}")

    finally:
        if driver:
            driver.quit()
        log.info(f"Close Driver")
    return flight


def flight_file_maker(html_content, contests, countries, pages, date):
    """

    :param html_content:
    :param contests:
    :param countries:
    :param pages:
    :param date:
    :return:
    """

    log = setup_logger("../Log/write_data", "flight_file_maker.log")
    log.info(f"Writing CSV flights file  {date} - {contests} - {countries}")
    try:
        if contests == "bpc":
            html_content.to_csv(f"./Data/flight_data/bpc/{contests}{date}_{countries}_{pages}.csv", sep=";",
                                index=False)
        elif contests == "world":
            html_content.to_csv(f"./Data/flight_data/world/{contests}{date}_{countries}_{pages}.csv", sep=";",
                                index=False)
        elif contests == "switzerland":
            html_content.to_csv(f"./Data/flight_data/switzerland/{contests}{date}_{countries}_{pages}.csv", sep=";",
                                index=False)
    except Exception as exc:
        log.error(f"Error {exc} : file {contests} {countries} {date} not write")
    finally:
        log.info(f"File {contests} {countries} {date} : end of process")


service = Service("/usr/local/bin/geckodriver")
options = Options()
options.add_argument("--headless") # Option put in driver to not open the firefox window
DELAY = 60
DELAY2 = 30

try:
    for contest in ("bpc", "world", "switzerland"): # Flight in France and Belgium uploaded in all relevant contests (also bordering contests)
        for year in ("2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"):
            # in xcontest, season start in October.
            # we have to download day by day because xcontest site is not suitable to use only year feature
            start_date = datetime(int(year) - 1, 10, 1)
            end_date = datetime(int(year), 9, 30)
            current_date = start_date
            for page in range(0, 300, 100): # page is the starting range in the table (no more than 2 pages by day)
                try:
                    while current_date <= end_date:
                        formatted_date = current_date.strftime("%Y-%m-%d")
                        if page == 0:
                            flight_from_web = flight_contest(services=service, option=options, contests=contest, years=year,
                                                             countries="BE", pages="", date=formatted_date)
                            flight_file_maker(flight_from_web, contests=contest, countries="BE", pages="",
                                              date=formatted_date)
                            time.sleep(DELAY2)
                            flight_from_web = flight_contest(services=service, option=options, contests=contest, years=year,
                                                             countries="FR", pages="", date=formatted_date)
                            flight_file_maker(flight_from_web, contests=contest, countries="FR", pages="",
                                              date=formatted_date)
                        else:
                            pagee = f"flights[start]={str(page)}"
                            flight_from_web = flight_contest(services=service, option=options, contests=contest, years=year,
                                                                 countries="BE", pages=pagee, date=formatted_date)
                            flight_file_maker(flight_from_web, contests=contest, countries="BE", pages=page,
                                              date=formatted_date)
                            time.sleep(DELAY2)
                            flight_from_web = flight_contest(services=service, option=options, contests=contest, years=year,
                                                             countries="FR", pages=pagee, date=formatted_date)
                            flight_file_maker(flight_from_web, contests=contest, countries="FR", pages=page,
                                              date=formatted_date)
                        current_date += timedelta(days=1)
                        time.sleep(DELAY)
                except Exception as e:
                    alert_sender(f"Error {e} - for {contest} {year} {page} if you don't receive Global fail message, job will continue")
except Exception as e:
    alert_sender(f"Error {e} - Global fail try again later")
