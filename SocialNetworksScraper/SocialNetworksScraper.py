# -*- coding: utf-8 -*-

import threading

# from browsers.LinkedInBrowser import LinkedInBrowser
from selenium import webdriver

from browsers.FacebookBrowser import FacebookBrowser
# from database.database import Database
from utils import utils
import ConfigParser


class SocialNetworksScraper:
    def __init__(self, db=None, translations_db_table=None):
        self.db = db
        self.translations_db_table = translations_db_table
        self.browsers = []
        self.translator = None
        self.logger = utils.get_logger(self.__class__.__name__)
        self.webdriver_exec_path = \
            r'C:\Users\sergeyy\Documents\School\IEM web scrapper\webdrivers\chromedriver.exe'
        self.results = {}
        self.best_result = {}

    def add_browser(self, browser, username, password, translator=False):
        b = browser(self.webdriver_exec_path)
        if b.login(username, password):
            self.browsers.append(b)
            self.results[b.__class__.__name__] = []
            if translator:
                self.translator = b
        else:
            self.logger.error("Invalid browser params")

    def scrape(self, record):
        threads = []
        name = record['first_name'] + " " + record['last_name']
        if not utils.is_english(name):
            first_name, last_name = name.split(' ')
            f_translations = []
            l_translations = []
            if self.db:
                f_translations = self.db.get_record(first_name)
                l_translations = self.db.get_record(last_name)
            if self.translator:
                if len(f_translations) == 0:
                    self.logger.info("Translating {0}".format(first_name))
                    f_translations = self.translator.get_translations(first_name, first_name=True)
                    # TODO: make sure it works:
                    if self.db:
                        if f_translations:
                            self.db.update_record(first_name, f_translations)
                    self.logger.info("Translations for first name:\n%s" % f_translations)
                    # print(f_translations)
                if len(l_translations) == 0:
                    self.logger.info("Translating {0}".format(last_name))
                    l_translations = self.translator.get_translations(last_name, first_name=False)
                    # TODO: make sure it works:
                    if self.db:
                        if l_translations:
                            self.db.update_record(last_name, l_translations)
                    self.logger.info("Translations for last name:\n%s" % l_translations)
                    # print(l_translations)
            # for b in self.browsers:
            #     if b.supports_hebrew:
            #         t = threading.Thread(target=self.__scrape, args=(b, name))
            #         t.start()
            #         threads.append(t)
            #     else:
            #         self.logger.info("{0} doesn't support hebrew searches".format(b.__class__.__name__))
            # for t in threads:
            #     t.join()
            # threads = []

            names = [name]

            for f in f_translations:
                for l in l_translations:
                    names.append(f + " " + l)
            for n in names:
                for b in self.browsers:
                    t = threading.Thread(target=self.__scrape, args=(b, n))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()
        else:
            for b in self.browsers:
                t = threading.Thread(target=self.__scrape, args=(b, name))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

        best_rank = -110
        for b in self.results:
            for r in self.results[b]:
                r['rank'] = self.get_result_rank(record, r['result'])
                if r['rank'] > best_rank:
                    best_rank = r['rank']
                    self.best_result[b] = r

        self.__print_best_results()

        self.__combine_origin_with_best_results(record)

    def __print_best_results(self):
        for b in self.best_result:
            self.logger.info('Best result in {0}'.format(b))
            for k, v in self.best_result[b].iteritems():
                print k, " :\t", v

    def __combine_origin_with_best_results(self, origin):
        for b in self.best_result:
            for k, v in self.best_result[b]['result'].iteritems():
                if k == 'education':
                    for e in v:
                        if e['degree'] == origin['degree']:
                            for k1, v1 in e.iteritems():
                                origin[k1] = v1
                else:
                    if v:
                        origin[k] = v

        self.logger.debug("Final origin = {0}".format(origin))

    def __scrape(self, browser, query):
        self.logger.info("Scraping {0} for: {1}".format(browser.__class__.__name__, query))
        results = browser.search(query)
        for result in results:
            if result is not None:
                self.results[browser.__class__.__name__].append({'result': result, 'rank': 0})

    def get_result_rank(self, origin, result):
        rank = 0
        rank += self.update_rank(origin['first_name'], result['first_name'], 5, 0)
        rank += self.update_rank(origin['last_name'], result['last_name'], 5, 0)
        rank += self.update_rank(origin['email'], result['email'], 30, -30)
        rank += self.update_rank(origin['phone'], result['phone'], 20, -20)
        rank += self.update_rank(origin['address'], result['address'], 15, -15)
        rank += self.update_rank(origin['work_place'], result['work_place'], 10, -10)
        rank += self.update_rank(origin['job_title'], result['job_title'], 5, -5)
        max_e_rank = -100
        for e in result['education']:
            if origin['degree'] != e['degree']:
                continue
            e_rank = 0
            e_rank += self.update_rank(origin['graduation_year'], e['graduation_year'], 10, -10)
            e_rank += self.update_rank(origin['degree'], e['degree'], 10, -10)
            e_rank += self.update_rank(origin['major'], e['major'], 10, -10)
            if e_rank > max_e_rank:
                max_e_rank = e_rank
        rank += max_e_rank
        return rank

    @staticmethod
    def update_rank(origin, result, weight_eq, weight_diff):
        if origin != '' and result != '':
            if isinstance(origin, str):
                origin = origin.lower()
                result = result.lower()
                return weight_eq if origin in result.encode('utf8') or result.encode('utf8') in origin else weight_diff
            else:
                return weight_eq if origin == result else weight_diff
        else:
            return 0


if __name__ == "__main__":
    browser = webdriver.Chrome(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1'])
    browser.get("https://www.facebook.com/")
    for line in self.browser.page_source.split('\n'):
        print line
    config = ConfigParser.ConfigParser()
    config.read(r"C:\Users\sergeyy\Desktop\BitBucket\iem_web_scraper\config\login.ini")

    # TODO: make sure this works
    # print get_field_mapping(config, 'Database', 'main_table_name')
    # db = Database(username=config.get('Database', 'username'), password=config.get('Database', 'password'),
    #               hostname=config.get('Database', 'hostname'), db_name=config.get('Database', 'db_name'))
    # records = db.get_latest(5, config.get('Database', 'main_table_name'))
    # scraper = SocialNetworksScraper(db)
    # TODO: replace this with records retrieval from the DB.
    records = [{'first_name': 'yaacov', 'last_name': 'shapiro', 'email': '', 'phone': '0503035177', 'address': '',
                'work_place': 'mellanox', 'job_title': '', 'graduation_year': '2011', 'degree': 0, 'major': ''}]

    scraper = SocialNetworksScraper()
    # scraper.add_browser(browser=LinkedInBrowser, username=config.get('Browsers', 'LinkedIn.username'),
    #                     password=config.get('Browsers', 'LinkedIn.password'))
    scraper.add_browser(browser=FacebookBrowser, username=config.get('Browsers', 'Facebook.username'),
                        password=config.get('Browsers', 'Facebook.password'), translator=True)

    for record in records:
        scraper.scrape(record)
