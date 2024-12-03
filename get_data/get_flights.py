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
import sys
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
    driver = webdriver.Firefox(service=services, options=option)
    try:


        if years == "2025":
            url = f"https://www.xcontest.org/{contests}/en/flights/#flights[sort]=reg@filter[country]={countries}@{pages}"
        else:
            url = f"https://www.xcontest.org/{year}/{contests}/en/flights/#filter[date]={date}@filter[country]={countries}@{pages}"
        driver.get(url)
        WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.TAG_NAME, "table")))
        html_content = driver.page_source
        html_file = StringIO(html_content)
        result = pd.read_html(html_file)
        driver.quit()
        flight = result[1]
        if contests == "bpc":
            flight.to_csv(f"./Data/flight_data/bpc/{contests}{date}_{countries}_{pages}.csv", sep=";",
                          index=False)
        elif contests == "world":
            flight.to_csv(f"./Data/flight_data/world/{contests}{date}_{countries}_{pages}.csv", sep=";",
                          index=False)
        elif contests == "switzerland":
            flight.to_csv(f"./Data/flight_data/switzerland/{contests}{date}_{countries}_{pages}.csv", sep=";",
                          index=False)

    except Exception as e:
        logging.error(f"Error {e} for {contest} {countries} {date} {pages}")

    finally:
        if driver:
            driver.quit()

# Standard config for logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.FileHandler(f"../Log/error.log", mode="w"),
                              logging.StreamHandler(sys.stdout)]) # Write logs in a file and in prompt

service = Service("/usr/local/bin/geckodriver")
options = Options()
options.add_argument("--headless") # Option put in driver to not open the firefox window

# Flight in France and Belgium uploaded in all relevant contests (also bordering contests)
for contest in ("bpc", "world", "switzerland"):
    for country in ("BE", "FR"):
        if contest == "switzerland" and country == "BE":
            continue # No enough Swiss flight in Belgium
        else:
            for year in ("2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"):
                # in xcontest, season start in October.
                # we have to download day by day because xcontest site is not suitable to use only year feature
                start_date = datetime(int(year) - 1, 10, 1)
                end_date = datetime(int(year), 9, 30)
                current_date = start_date
                for page in range(0, 300, 100): # page is the starting range in the table (no more than 2 pages by day)
                    while current_date <= end_date:
                        formatted_date = current_date.strftime("%Y-%m-%d")
                        if page == 0:
                            flight_contest(services=service, option=options, contests=contest, years=year,
                                           countries=country, pages="", date=formatted_date)
                        else:
                            page = f"flights[start]={str(page)}"
                            flight_contest(services=service, option=options, contests=contest, years=year,
                                           countries=country, pages=page, date=formatted_date)
                        current_date += timedelta(days=1)
