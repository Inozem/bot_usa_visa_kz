from dotenv import load_dotenv, find_dotenv
import os
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

load_dotenv(find_dotenv())

RUCAPTCHA_API_KEY = os.getenv('RUCAPTCHA_API_KEY')
FILE_PATH = 'C:/Users/inoze/Downloads/'  # Путь для сохранения файлов


def starting_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    browser = webdriver.Chrome(options=options)
    return browser


def geting_login_data():
    login_input_text = {
        'email': 'Введите адрес электронной почты: \n',
        'password': 'Введите пароль: \n'
    }
    login_data = {key: input(value) for key, value in login_input_text.items()}
    return login_data


def reading_captcha():
    """Разгадывание капчи"""
    captcha = ''
    captchafile = {'file': open(f'{FILE_PATH}screenie.png', 'rb')}
    data = {'key': RUCAPTCHA_API_KEY, 'method': 'post'}
    response_post = requests.post('http://rucaptcha.com/in.php', files=captchafile, data=data)
    if 'OK' in response_post.text:
        captcha_id = response_post.text.split('|')[1]
        print(captcha_id)
        response_get_text = ''
        while 'OK' not in response_get_text:
            sleep(5)
            response_get = requests.get(f'http://2captcha.com/res.php?key={RUCAPTCHA_API_KEY}&action=get&id={captcha_id}')
            response_get_text = response_get.text
            print(response_get_text)
        captcha = response_get_text.split('|')[1]
    return captcha


def authorization(browser, email, password):
    """Авторизация"""
    browser.get('https://cgifederal.secure.force.com/')
    element_id_or_name_part = 'loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:'
    browser.find_element(By.ID, f'{element_id_or_name_part}username').send_keys(email)
    browser.find_element(By.ID, f'{element_id_or_name_part}password').send_keys(password)
    browser.find_element(By.NAME, f'{element_id_or_name_part}j_id167').click()
    sleep(10)  # Вместо паузы сделать выполнение следующей функции только после загрузки капчи
    browser.find_element(By.ID, f'{element_id_or_name_part}theId').screenshot(f'{FILE_PATH}screenie.png')
    browser.find_element(By.ID, f'{element_id_or_name_part}recaptcha_response_field').send_keys(reading_captcha())
    browser.find_element(By.ID, f'{element_id_or_name_part}loginButton').click()
    error_id_part = 'error:j_id132:j_id133:0:j_id134:j_id135:j_id137'
    if error_id_part in browser.page_source:
        error_text = browser.find_element(By.ID, f'{element_id_or_name_part}{error_id_part}').text
        print(error_text)
        login_data = {'email': email, 'password': password}
        if 'Captcha.' not in error_text:
            login_data = geting_login_data()
        browser = authorization(browser, **login_data)
    return browser


def city_selection(browser):
    """Выбор города"""
    tr_elements = browser.find_elements(By.TAG_NAME, 'tr')
    cities = {i: tr_elements[i].text for i in range(len(tr_elements))}
    city_ind_in_cities = False
    city_ind = ''
    input_text_part_1 = 'Введите номер города, в котором хотите пройти собеседование:\n'
    input_text_part_2 = '\n'.join([f'{ind} - {name}' for ind, name in cities.items()]) + '\n'
    while not city_ind_in_cities:
        city_ind = int(input(f'{input_text_part_1}{input_text_part_2}'))
        if city_ind in cities:
            city_ind_in_cities = True
    tr_elements[city_ind].find_element(By.TAG_NAME, 'input').click()
    sleep(5)
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id112:j_id169').click()
    return browser


def visa_category_selection(browser):
    """Выбор категории визы"""
    tr_elements = browser.find_elements(By.TAG_NAME, 'tr')
    visa_categories = {i: tr_elements[i].text for i in range(len(tr_elements))}
    visa_ind_in_visa_categories = False
    visa_ind = ''
    input_text_part_1 = 'Выберите номер визовой категории:\n'
    input_text_part_2 = '\n'.join([f'{ind} - {type}' for ind, type in visa_categories.items()]) + '\n'
    while not visa_ind_in_visa_categories:
        visa_ind = int(input(f'{input_text_part_1}{input_text_part_2}'))
        if visa_ind in visa_categories:
            visa_ind_in_visa_categories = True
    tr_elements[visa_ind].find_element(By.TAG_NAME, 'input').click()
    sleep(5)
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id109:j_id166').click()
    return browser


def visa_class_selection(browser):
    """Выбор класса визы"""
    table_elements = browser.find_elements(By.TAG_NAME, 'table')
    tr_elements = table_elements[1].find_elements(By.TAG_NAME, 'tr')
    visa_classes = {i: tr_elements[i].text for i in range(len(tr_elements))}
    visa_ind_in_visa_classes = False
    visa_ind = ''
    input_text_part_1 = 'Выберите номер визового класса:\n'
    input_text_part_2 = '\n'.join([f'{ind} - {type}' for ind, type in visa_classes.items()]) + '\n'
    while not visa_ind_in_visa_classes:
        visa_ind = int(input(f'{input_text_part_1}{input_text_part_2}'))
        if visa_ind in visa_classes:
            visa_ind_in_visa_classes = True
    tr_elements[visa_ind].find_element(By.TAG_NAME, 'input').click()
    sleep(5)
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:theForm:j_id178').click()
    return browser


if __name__ == '__main__':
    browser = starting_browser()
    browser = authorization(browser, **geting_login_data())
    browser.find_elements(By.TAG_NAME, 'a')[2].click()  # Новое обращение / Запись на собеседование
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:theForm:j_id176').click()  # Выбор неиммиграционной визы (по умолчанию)
    browser = city_selection(browser)
    browser = visa_category_selection(browser)
    browser = visa_class_selection(browser)
    browser.find_element(By.NAME, 'thePage:SiteTemplate:theForm:j_id1279').click()  # Персональные данные введены
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id856:continueBtn').click()  # Члены семьи добавлены в список
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id856:continueBtn').click()  # Члены семьи добавлены в список
    sleep(15)
    with open(f'{FILE_PATH}page.txt', 'w', encoding="utf-8") as file:
        file.write(browser.page_source)

# Делать ли паузы между переходами на страницы, чтобы не сразу бросаться в глаза как бот?
