from dotenv import load_dotenv, find_dotenv
import os
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

load_dotenv(find_dotenv())

MAX_ERROR_COUNT = 3
RUCAPTCHA_API_KEY = os.getenv('RUCAPTCHA_API_KEY')
FILE_PATH = 'C:/Users/inoze/Downloads/'  # Путь для сохранения файлов


def starting_browser():
    """Настройка и запуск браузера."""
    options = webdriver.ChromeOptions()
    # TODO: в конце - проверить работу в безоконном режиме (headless)
    options.add_argument("window-size=800,600")
    browser = webdriver.Chrome(options=options)
    return browser


# TODO: добавить везде аннотации типов
# TODO 2: на вход получать картинку в памяти и разгадывать ее с помощью rucaptcha
#  без сохранения в файл
def reading_captcha():
    """Разгадывание капчи."""
    captcha = ''
    captcha_file = {'file': open(f'{FILE_PATH}screenie.png', 'rb')}
    data = {'key': RUCAPTCHA_API_KEY, 'method': 'post'}
    response_post = requests.post('http://rucaptcha.com/in.php', files=captcha_file, data=data)
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


def authorization(browser, answers, error_count=0):
    """Авторизация."""
    required_params = {
        'email': 'Введите адрес электронной почты: \n',
        'password': 'Введите пароль: \n'
    }
    login_data = {key: answers.get(key) or input(value) for key, value in required_params.items()}
    browser.get('https://cgifederal.secure.force.com/')
    element_id_or_name_part = 'loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:'
    browser.find_element(By.ID, f'{element_id_or_name_part}username').send_keys(login_data['email'])
    browser.find_element(By.ID, f'{element_id_or_name_part}password').send_keys(login_data['password'])
    browser.find_element(By.NAME, f'{element_id_or_name_part}j_id167').click()
    sleep(10)  # Вместо паузы сделать выполнение следующей функции только после загрузки капчи
    # TODO: скриншот не производительно делать, нужно найти элемент img и в нем забрать ссылку
    #  эта ссылка - по сути закодированное изображение в (base64) - его в памяти (!)
    #  сохраняем и отправляем уже в сервис рекапчи
    browser.find_element(By.ID, f'{element_id_or_name_part}theId').screenshot(f'{FILE_PATH}screenie.png')
    sleep(10)  # browser.find_element(By.ID, f'{element_id_or_name_part}recaptcha_response_field').send_keys(reading_captcha())
    answers.update(login_data)
    browser.find_element(By.ID, f'{element_id_or_name_part}loginButton').click()
    error_id_part = 'error:j_id132:j_id133:0:j_id134:j_id135:j_id137'
    if error_id_part in browser.page_source:
        error_count += 1
        error_text = browser.find_element(By.ID, f'{element_id_or_name_part}{error_id_part}').text
        print(error_text)
        if 'Captcha.' in error_text and error_count < MAX_ERROR_COUNT:
            browser, answers = authorization(browser, answers, error_count)
        elif error_count >= MAX_ERROR_COUNT:
            raise Exception('Проблемы на стороне сервиса. Капча.')
        else:
            raise Exception(error_text)
    return browser, answers


# TODO: все функции на вход принимают answers, чтобы использовать значения из него
#  если значение не найдено - тогда спрашиваем у пользователя
#  при этом все ответы запоминаем и при возврате результата (успешного или с ошибками)
#  возвращаем актуальный словарь ответов
def city_selection(browser, answers):
    """Выбор города."""
    tr_elements = browser.find_elements(By.TAG_NAME, 'tr')
    cities = {i: tr_elements[i].text for i in range(len(tr_elements))}
    city_ind = None
    try:
        city_ind = [*cities.values()].index(answers['city'])
    except (ValueError, KeyError):
        input_text_part_1 = 'Введите номер города, в котором хотите пройти собеседование:\n'
        input_text_part_2 = '\n'.join([f'{ind} - {name}' for ind, name in cities.items()]) + '\n'
        city_ind = int(input(f'{input_text_part_1}{input_text_part_2}'))
    try:
        tr_elements[city_ind].find_element(By.TAG_NAME, 'input').click()
    except IndexError:
        raise Exception(f'Город под номером {city_ind} недоступен')
    answers.update({'city': cities[city_ind]})
    sleep(5)
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id112:j_id169').click()
    return browser, answers


def visa_category_selection(browser, answers):
    """Выбор категории визы."""
    visa_category_supported = [
        'Виза B1/B2 (туризм, посещение родственников, деловые поездки и не срочное медицинское лечение)',
        'Визы для студентов и участников программ обмена (первичные обращения и обращения без прохождения личного собеседования)',
        'Визы для студентов и участников программ обмена (которым ранее было отказано в визе)'
    ]
    tr_elements = browser.find_elements(By.TAG_NAME, 'tr')
    visa_categories = {i: tr_elements[i].text for i in range(len(tr_elements))}
    visa_ind = None
    try:
        visa_ind = [*visa_categories.values()].index(answers['visa_category'])
    except (ValueError, KeyError):
        input_text_part_1 = 'Выберите номер визовой категории:\n'
        input_text_part_2 = '\n'.join([f'{ind} - {type}' for ind, type in visa_categories.items()]) + '\n'
        visa_ind = int(input(f'{input_text_part_1}{input_text_part_2}'))
    try:
        tr_elements[visa_ind].find_element(By.TAG_NAME, 'input').click()
        if tr_elements[visa_ind].text not in visa_category_supported:
            raise Exception(f'Сервис не работает с категорией виз под номером {visa_ind}')
    except IndexError:
        raise Exception(f'Нет категории с номером {visa_ind}')
    answers.update({'visa_category': visa_categories[visa_ind]})
    sleep(5)
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id109:j_id166').click()
    return browser, answers


def visa_class_selection(browser, answers):
    """Выбор класса визы."""
    visa_class_supported = [
        'B1 - Виза для деловых поездок',
        'B1/B2 - Виза для деловых и туристических поездок',
        'B2 - Виза для туристических поездок и лечения',
        'F-1 - Студенческая виза для академических или языковых программ обучения',
        'F-2 - Виза для супруга(и)/ребенка держателя визы F-1',
    ]
    table_elements = browser.find_elements(By.TAG_NAME, 'table')
    tr_elements = table_elements[1].find_elements(By.TAG_NAME, 'tr')
    visa_classes = {i: tr_elements[i].text for i in range(len(tr_elements))}
    visa_ind = None
    try:
        visa_ind = [*visa_classes.values()].index(answers['visa_class'])
    except (ValueError, KeyError):
        input_text_part_1 = 'Выберите номер визового класса:\n'
        input_text_part_2 = '\n'.join([f'{ind} - {type}' for ind, type in visa_classes.items()]) + '\n'
        visa_ind = int(input(f'{input_text_part_1}{input_text_part_2}'))
    try:
        tr_elements[visa_ind].find_element(By.TAG_NAME, 'input').click()
        if tr_elements[visa_ind].text not in visa_class_supported:
            raise Exception(f'Сервис не работает с категорией виз под номером {visa_ind}')
    except IndexError:
        raise Exception(f'Нет категории с номером {visa_ind}')
    answers.update({'visa_class': visa_classes[visa_ind]})
    sleep(5)
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:theForm:j_id178').click()
    return browser, answers





if __name__ == '__main__':
    # TODO: сделать функцию, которая на вход принимает словарь с параметрами (ответами)
    #  примеры такого словаря:

    # пустой словарь - первый запуск еще никаких ответов система не запомнила
    # answers = {}

    # частичная информация, в таком случае вопросы будут только там, где нет ответов
    # answers = {
    #     'email': 'my.email@gmail.com',
    #     'password': 'the-best-password',
    # }

    # полная информация, все должно в автоматическом режиме пройти
    answers = {
        'email': os.getenv('CGIFEDERAL_EMAIL'),
        'password': os.getenv('CGIFEDERAL_PASSWORD'),
        'city': os.getenv('CGIFEDERAL_CITY'),
        'visa_category': os.getenv('CGIFEDERAL_VISA_CATEGORY'),
        'visa_class': 'a' # os.getenv('CGIFEDERAL_VISA_CLASS'),
    }

    browser = starting_browser()
    browser, answers = authorization(browser, answers)
    browser.find_elements(By.TAG_NAME, 'a')[2].click()  # Новое обращение / Запись на собеседование
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:theForm:j_id176').click()  # Выбор неиммиграционной визы (по умолчанию)
    browser, answers = city_selection(browser, answers)
    browser, answers = visa_category_selection(browser, answers)
    browser, answers = visa_class_selection(browser, answers)
    print(answers)
    browser.find_element(By.NAME, 'thePage:SiteTemplate:theForm:j_id1279').click()  # Персональные данные введены
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:j_id856:continueBtn').click()  # Члены семьи добавлены в список
    sleep(15)
    # TODO: успех - это созданная запись + доступные окна для записи
    #  (то есть надо распарсить последнюю страницу)
    with open(f'{FILE_PATH}page.txt', 'w', encoding="utf-8") as file:
        file.write(browser.page_source)
