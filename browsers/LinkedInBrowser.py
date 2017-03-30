# -*- coding: utf-8 -*-
import time
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4 import Tag
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from browsers.Browser import Browser
from utils.definitions import *
from utils.utils import is_english


class LinkedInBrowser(Browser):
    def __init__(self, executable_path):
        Browser.__init__(self, executable_path)
        self.login_url = 'https://www.linkedin.com/uas/login'
        self.base_url = 'https://www.linkedin.com'

    def init_elements(self):
        self.elements['username'] = {'by': By.ID, 'val': 'session_key-login'}
        self.elements['password'] = {'by': By.ID, 'val': 'session_password-login'}
        self.elements['login_button'] = {'by': By.ID, 'val': 'btn-primary'}
        self.elements['search_box'] = {'by': By.ID, 'val': 'main-search-box'}
        self.elements['results_container'] = {'by': By.CLASS_NAME, 'val': 'results-list'}
        self.elements['data_container'] = {'by': By.CLASS_NAME, 'val': 'core-rail'}

    def update_elements_before_login(self):
        username_input_id = None
        password_input_id = None
        login_button_id = None

        for line in self.browser.page_source.split('\n'):
            # find id of the username input box
            if "placeholder=\"Email" in line:
                username_input_id = line.split('id=\"')[1].split('\"')[0]
            # find id of the password input box
            if "placeholder=\"Password\"" in line:
                password_input_id = line.split('id=\"')[1].split('\"')[0]
            # find id of the log in button
            if "value=\"Sign In\"" in line:
                login_button_id = line.split('id=\"')[1].split('\"')[0]

        if username_input_id:
            self.elements['username']['val'] = username_input_id
        if password_input_id:
            self.elements['password']['val'] = password_input_id
        if login_button_id:
            self.elements['login_button']['val'] = login_button_id

    def update_elements_after_login(self):
        search_box_id = None

        for line in self.browser.page_source.split('\n'):
            # find id of the search input box
            if "placeholder=\"Search\"" in line:
                search_box_id = line.split('id=\"')[1].split('\"')[0]

        if search_box_id:
            self.elements['search_box']['val'] = search_box_id

    def get_results_urls(self, query):
        self.update_elements_after_login()
        search_box = self.browser.find_element(self.elements['search_box']['by'],
                                               self.elements['search_box']['val'])
        search_box.clear()
        search_box.click()
        search_box.send_keys('%s\n' % query.decode('utf-8'))
        time.sleep(5)
        try:
            self.wait_for_element(self.elements['results_container'])
        except TimeoutException:
            self.logger.debug("timeout")
            return []
        bs = BeautifulSoup(self.browser.page_source, "html.parser")
        results = bs.find('ul', {'class': 'results-list'})
        urls = []
        if results:
            for result in results.children:
                if isinstance(result, NavigableString):
                    continue
                if isinstance(result, Tag):
                    href = result.find('a', {'class': 'search-result__result-link ember-view'})
                    if href:
                        href = href.get('href')
                        urls.append(self.base_url + href)
        return urls

    def scrape_result(self):
        result = {'first_name': '', 'last_name': '',
                  'email': '', 'phone': '',
                  'address': '', 'work_place': '',
                  'job_title': '', 'education': []}
        self.wait_for_element(self.elements['data_container'])
        bs = BeautifulSoup(self.browser.page_source, "html.parser")
        full_name = bs.find('h1', {'class': 'pv-top-card-section__name Sans-26px-black-85% mb1'}).text
        result['first_name'] = full_name.split(' ')[0]
        result['last_name'] = full_name.split(' ')[1]

        # contact info
        self.browser.find_element(By.CSS_SELECTOR, ".contact-see-more-less.link-without-visited-state").click()
        time.sleep(5)
        bs = BeautifulSoup(self.browser.page_source, "html.parser")
        email_tag = bs.find(text="Email")
        if email_tag:
            result['email'] = email_tag.findNext('div').text.strip()
        phone_tag = bs.find(text="Phone")
        if phone_tag:
            result['phone'] = phone_tag.findNext('div').text.strip().split(' ')[0].replace('-', '')
        address_tag = bs.find(text="Address")
        if address_tag:
            address = address_tag.findNext('div').text.strip()
            if is_english(address):
                result['address'] = address.lower()
            else:
                result['address'] = address
        # we don't have use for it at the moment.
        # website_tag = bs.find(text="Website")
        # if website_tag:
        #     result['website'] = website_tag.findNext('a').get("href").strip()

        # experience
        experience_tag = bs.find('section', {'class': 'pv-profile-section experience-section ember-view'})
        if experience_tag:
            current_job = experience_tag.findNext('ul').find('li')
            if current_job.h3:
                job_title = current_job.h3.text.strip()
                if is_english(job_title):
                    result['job_title'] = job_title.lower()
                else:
                    result['job_title'] = job_title
            if current_job.h4:
                work_place = current_job.h4.text.replace('Company Name', '').strip()
                if is_english(work_place):
                    result['work_place'] = work_place.lower()
                else:
                    result['work_place'] = work_place

        # education
        education_tag = bs.find('section', {'class': 'pv-profile-section education-section ember-view'})
        if education_tag:
            for e in education_tag.findAll('li'):
                education = {'school': '', 'graduation_year': '', 'degree': '', 'major': ''}
                if e.h3:
                    education['school'] = e.h3.text.encode('utf-8').strip()
                degree = e.find(text='Degree Name')
                if degree:
                    degree = degree.findNext('span').text.strip()
                    for d in degrees:
                        if d in degree.lower().replace('.', ''):
                            education['degree'] = degrees.index(d)
                major = e.find(text='Field Of Study')
                if major:
                    major_ = major.findNext('span').text.strip().lower()
                    for k in majors:
                        if major_ in majors[k]:
                            education['major'] = k
                    if education['major'] == '':
                        if is_english(major_):
                            education['major'] = major_.lower()
                        else:
                            education['major'] = major_
                period = e.find(text='Dates attended or expected graduation')
                if period:
                    education['graduation_year'] = period.findNext('span').text.strip()[-4:]
                for s in schools:
                    if s in education['school'].lower():
                        education['school'] = 'Technion'
                        result['education'].append(education)
                        break

        if len(result['education']) > 0:
            return result
        else:
            return None
