# -*- coding: utf-8 -*-
import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from browsers.Browser import Browser
from selenium.common.exceptions import TimeoutException
from utils.definitions import *
from utils.utils import is_english
import pyxdameraulevenshtein


class FacebookBrowser(Browser):
    def __init__(self, executable_path):
        Browser.__init__(self, executable_path)
        self.login_url = 'https://www.facebook.com/'
        self.base_url = 'https://www.facebook.com/'

    def init_elements(self):
        self.elements['username'] = {'by': By.ID, 'val': 'email'}
        self.elements['password'] = {'by': By.ID, 'val': 'pass'}
        self.elements['login_button'] = {'by': By.ID, 'val': 'u_0_u'}
        self.elements['search_box'] = {'by': By.CLASS_NAME, 'val': '_1frb'}
        self.elements['results_container'] = {'by': By.ID, 'val': 'BrowseResultsContainer'}
        self.elements['data_container'] = {'by': By.CLASS_NAME, 'val': '_51sx'}

    def update_elements_before_login(self):
        username_input_id = None
        password_input_id = None
        login_button_id = None

        for line in self.browser.page_source.split('\n'):
            print line
            # find id of the username input box
            if "name=\"email\"" in line:
                username_input_id = line.split('id=\"')[1].split('\"')[0]
            # find id of the password input box
            if "name=\"pass\"" in line:
                password_input_id = line.split('id=\"')[1].split('\"')[0]
            # find id of the log in button
            if "value=\"Log In\"" in line:
                login_button_id = line.split('id=\"')[1].split('\"')[0]

        if username_input_id:
            self.elements['username']['val'] = username_input_id
        if password_input_id:
            self.elements['password']['val'] = password_input_id
        if login_button_id:
            self.elements['login_button']['val'] = login_button_id

    def update_elements_after_login(self):
        search_box_class = None

        bs = BeautifulSoup(self.browser.page_source, "html.parser")
        try:
            search_box_class = bs.find('input', {'placeholder': 'Search Facebook'}).get('class')[0]
        except AttributeError:
            pass

        if search_box_class:
            self.elements['search_box']['val'] = search_box_class

    def get_results_urls(self, query):
        self.update_elements_after_login()
        search_box = self.browser.find_element(self.elements['search_box']['by'], self.elements['search_box']['val'])
        search_box.clear()
        search_box.click()
        search_box.send_keys('%s\n' % query.decode('utf-8'))

        self.browser.get(self.browser.current_url.replace('top', 'people'))

        try:
            self.wait_for_element(self.elements['results_container'])
        except TimeoutException:
            return []

        time.sleep(10)

        bs = BeautifulSoup(self.browser.page_source, "html.parser")

        results = bs.findAll('a', {'class': '_2ial _8o _8s lfloat _ohe'})
        urls = []

        for result in results:
            href = result.get('href').split('/')[3]
            if 'profile.php' in href:
                href = href.replace('ref=br_rs', 'sk=about')
            else:
                href = href.replace('?ref=br_rs', '/about')
            href = self.base_url + href
            urls.append(href)
        return urls

    def scrape_result(self):
        result = {'first_name': '', 'last_name': '',
                  'email': '', 'phone': '',
                  'address': '', 'work_place': '',
                  'job_title': '', 'education': []}

        self.wait_for_element(self.elements['data_container'])
        bs = BeautifulSoup(self.browser.page_source, "html.parser")
        full_name = bs.find('span', {'id': 'fb-timeline-cover-name'}).text
        result['first_name'] = full_name.split(' ')[0]
        result['last_name'] = full_name.split(' ')[1]

        contact_info = bs.find('div', {'class': '_4ms4'})
        if contact_info:
            phone_tag = bs.find(text='Phones')
            if phone_tag:
                phone = phone_tag.findNext('div').text
                if phone:
                    result['phone'] = phone.replace('-', '')
            email_tag = bs.find(text='Email')
            if email_tag:
                email = email_tag.findNext('div').text
                if email:
                    result['email'] = email
            address_tag = bs.find(text='Address')
            if address_tag:
                address = address_tag.findNext('div').text
                if address:
                    if len(address.split(', ')) > 1:
                        result['address'] = address.split(', ')[0]
                    else:
                        result['address'] = address
            else:
                address_tag = bs.find('div', {'class': '_c24 _50f4'})
                if address_tag:
                    address = address_tag.text
                    if address:
                        try:
                            if 'Lives in ' in address:
                                if len(address.split('Lives in ')[1].split(', ')) > 1:
                                    result['address'] = address.split('Lives in ')[1].split(', ')[0]
                                else:
                                    result['address'] = address.split('Lives in ')[1]
                            elif 'From ' in address:
                                if len(address.split('From ')[1].split(', ')) > 1:
                                    result['address'] = address.split('From ')[1].split(', ')[0]
                                else:
                                    result['address'] = address.split('From ')[1]
                        except IndexError:
                            pass
            # we don't have use for it at the moment.
            # website_tag = bs.find(text='Website')
            # if website_tag:
            #     website = website_tag.findNext('div').text
            #     if website:
            #         result['data']['contact info']['website'] = website

        self.browser.get(self.browser.current_url + "?&section=education")
        bs = BeautifulSoup(self.browser.page_source, "html.parser")
        experience = bs.find(text='Work')
        if experience:
            current_job = experience.findNext('ul').find('li')
            work_place = current_job.find('div', {'class': '_2lzr _50f5 _50f7'})
            if work_place:
                company = work_place.text
                if company:
                    if is_english(company):
                        result['work_place'] = company.lower()
                    else:
                        result['work_place'] = company
            description_tag = current_job.find('div', {'class': '_173e _50f8 _50f3'})
            if description_tag:
                description = description_tag.text
                job_title = description.encode('utf-8').split('\xc2\xb7')[0].strip()
                if is_english(job_title):
                    result['job_title'] = job_title.lower()
                else:
                    result['job_title'] = job_title

        education_tag = bs.find(text='Education')
        if education_tag:
            for child in education_tag.findNext('ul').children:
                education = {'school': '', 'graduation_year': '', 'degree': '', 'major': ''}
                school = child.find('div', {'class': '_2lzr _50f5 _50f7'})
                if school:
                    education['school'] = school.text.encode('utf-8')
                description_tag = child.find('div', {'class': 'fsm fwn fcg'})
                if description_tag:
                    description = description_tag.text
                    sections = description.encode('utf-8').split('\xc2\xb7')
                    for s in sections:
                        for d in degrees:
                            if d in s.lower().replace('.', ''):
                                education['degree'] = degrees.index(d)
                                major = []
                                for i in s.split(' '):
                                    if d not in i.lower().replace('.', ''):
                                        major.append(i)
                                major_ = " ".join(major).strip()
                                for k in majors:
                                    if major_ in majors[k]:
                                        education['major'] = k
                                if education['major'] == '':
                                    if is_english(major_):
                                        education['major'] = major_.lower()
                                    else:
                                        education['major'] = major_
                        if bool(re.search('\d', s)):
                            if "Class of" in s:
                                education['graduation_year'] = s.strip()[-4:]
                for s in schools:
                    if s in education['school'].lower():
                        education['school'] = 'Technion'
                        result['education'].append(education)
                        break

        if len(result['education']) > 0:
            return result
        else:
            return None

    def get_translations(self, entry, first_name=True):
        translations = []
        search_box = self.browser.find_element(self.elements['search_box']['by'], self.elements['search_box']['val'])
        search_box.clear()
        search_box.click()
        search_box.send_keys('%s\n' % entry.decode('utf-8'))

        self.browser.get(self.browser.current_url.replace('top', 'people'))
        time.sleep(2)

        start = time.time()
        try:
            while True:
                page_size = len(self.browser.page_source)
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                if time.time() - start > self.wait_time:
                    break
                if page_size == len(self.browser.page_source):
                    break
        except BaseException:
            return []

        bs = BeautifulSoup(self.browser.page_source, "html.parser")

        results = bs.findAll('div', {'class': '_5d-5'})
        if results:
            for result in results:
                english_name = re.sub(r"[^A-Za-z\s]", "", result.text.strip()).strip()
                if english_name:
                    if first_name:
                        if english_name.split(' ')[0].lower() not in translations:
                            translations.append(english_name.split(' ')[0].lower())
                    else:
                        try:
                            if english_name.split(' ')[1].lower() not in translations:
                                translations.append(english_name.split(' ')[1].lower())
                        except IndexError:
                            translations.append(english_name)

        # filter the translations using normalized_damerau_levenshtein_distance
        distances = []
        for t in translations:
            sum_of_distance = 0
            for t1 in translations:
                if t != t1:
                    sum_of_distance += pyxdameraulevenshtein.normalized_damerau_levenshtein_distance(t, t1)
            distances.append(float(sum_of_distance) / float(len(translations)))
        for i in range(len(distances) - 1):
            if distances[i] > 0.85:
                translations.remove(translations[i])

        return translations
