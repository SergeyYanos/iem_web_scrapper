import pickle
import time
from urllib2 import unquote
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotVisibleException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils import utils


class Browser:
    def __init__(self, executable_path):
        self.browser = webdriver.Chrome(
            executable_path=executable_path, service_args=['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1'])

        self.login_url = None
        self.base_url = None
        self.elements = {'username': {'by': None, 'val': None},
                         'password': {'by': None, 'val': None},
                         'login_button': {'by': None, 'val': None},
                         'search_box': {'by': None, 'val': None},
                         'results_container': {'by': None, 'val': None},
                         'data_container': {'by': None, 'val': None}}
        self.init_elements()
        self.wait_time = 60
        self.current_url = None
        self.logger = utils.get_logger(self.__class__.__name__)
        self.supports_hebrew = True
        self.login_tries = 1
        self.search_counter = 0
        self.click_counter = 0

        # try:
        #
        # cookies =
        # pickle.load
        # (open("C:\\Users\\sergeyy\\Desktop\\iem_algorithm\\IEM web scrapper\\browsers\\{0}.pkl".format
        # (self.__class__.__name__), "rb"))
        #     for cookie in cookies:
        #         self.browser.add_cookie(cookie)
        # except IOError:
        #     pass

    def init_elements(self):
        raise NotImplementedError

    def wait_for_element(self, element, wait_time=None):
        if wait_time:
            wt = wait_time
        else:
            wt = self.wait_time
        wait = WebDriverWait(self.browser, wt)
        wait.until(EC.presence_of_element_located((element['by'], element['val'])))

    def login(self, username, password):
        self.login_tries -= 1
        self.logger.info('Trying to log in to {0}'.
                         format(self.__class__.__name__.split('Browser')[0]))
        try:
            self.update_elements_before_login()

            if any(self.elements[k] is None for k in self.elements):
                raise Exception("Browser must fill the elements dict")

            self.browser.get(self.login_url)
            self.wait_for_element(self.elements['login_button'])

            username_field = \
                self.browser.find_element(self.elements['username']['by'], self.elements['username']['val'])
            password_field = \
                self.browser.find_element(self.elements['password']['by'], self.elements['password']['val'])
            username_field.send_keys(username)
            password_field.send_keys(password)
            login_button = self.browser.find_element(self.elements['login_button']['by'],
                                                     self.elements['login_button']['val'])
            login_button.click()
            time.sleep(5)
            self.update_elements_after_login()
            self.wait_for_element(self.elements['search_box'])
        except Exception as e:
            self.logger.exception(e)
            if self.login_tries == 0:
                self.logger.error('Failed to log in.')
                return False
            else:
                return self.login(username, password)
        self.logger.info('Successfully logged in.')
        return True

    def search(self, query):
        self.search_counter += 1
        try:
            urls = self.get_results_urls(query)
            self.browser.execute_script("window.history.go(-1)")
            time.sleep(1)
            return_data = []
            for url in urls:
                try:
                    self.__save_current_url()
                    self.browser.get(url)
                    self.click_counter += 1
                    self.wait_for_element(self.elements['data_container'])
                    return_data.append(self.scrape_result())
                    self.__restore_url()
                except Exception:
                    pass
        except NoSuchElementException:
            return []
        return return_data

    def update_elements_before_login(self):
        pass

    def update_elements_after_login(self):
        pass

    def get_results_urls(self, query):
        """
        Gets urls of the search results form a web page.
        :param query: query for the search box.
        :return: list of urls.
        """
        return []

    def scrape_result(self):
        """
        Scrapes the web page for wanted data.
        :param url: url of the web page to be scraped.
        :return: scraped data.
        """
        return None

    def __save_current_url(self):
        self.current_url = self.browser.current_url

    def __restore_url(self):
        self.browser.get(self.current_url)

    def __del__(self):
        # pickle.dump(self.browser.get_cookies(), open("C:\\Users\\sergeyy\\Desktop\\iem_algorithm\\IEM web scrapper\\browsers\\{0}.pkl".format(self.__class__.__name__), "wb"))
        self.browser.close()
        self.logger.info('Search counter: {0}'.format(self.search_counter))
        self.logger.info('Click counter: {0}'.format(self.click_counter))

    @staticmethod
    def parse_href(href):
        parsed_href = ''
        if 'redirect' in href:
            parsed_href = href.split('url=')[1]
        if 'php?u=' in href:
            parsed_href = href.split('php?u=')[1]
            parsed_href = unquote(parsed_href)
        return parsed_href
