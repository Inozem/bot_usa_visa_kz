from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By

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


def authorization(browser, email, password):
    """Авторизация и выбор неиммиграционной визы"""
    browser.get('https://cgifederal.secure.force.com/')
    sleep(3)
    element_id_or_name_part = 'loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:'
    browser.find_element(By.ID, f'{element_id_or_name_part}username').send_keys(email)
    browser.find_element(By.ID, f'{element_id_or_name_part}password').send_keys(password)
    browser.find_element(By.NAME, f'{element_id_or_name_part}j_id167').click()
    sleep(10)  # Вместо паузы сделать выполнение следующей функции только после загрузки капчи
    browser.find_element(By.ID, f'{element_id_or_name_part}theId').screenshot(f'{FILE_PATH}screenie.png')
    # Добавить функцию обработки капчи
    browser.find_element(By.ID, f'{element_id_or_name_part}loginButton').click()
    error_id_part = 'error:j_id132:j_id133:0:j_id134:j_id135:j_id137'
    if error_id_part in browser.page_source:
        error_text = browser.find_element(By.ID, f'{element_id_or_name_part}{error_id_part}').text
        print(error_text)
        login_data = {'email': email, 'password': password}
        if 'Captcha.' not in error_text:
            login_data = geting_login_data()
        browser = authorization(browser, **login_data)
    browser.find_elements(By.TAG_NAME, 'a')[2].click()  # Новое обращение / Запись на собеседование
    browser.find_element(By.NAME, 'j_id0:SiteTemplate:theForm:j_id176').click()  # Выбор неиммиграционной визы (по умолчанию)
    return browser


def city_selection(browser):
    """Выбор города"""
    # Выбор города можно упростить, если не считывать список городов с сайта, а выдавать их списком.
    # Но тогда в случае изменения списка городов или их порядка, нужно будут вносить изменения в бота вручную.
    # Во втором случае запрос города можно будет вынести к запросам мыла и пароля.
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


if __name__ == '__main__':
    browser = starting_browser()
    browser = authorization(browser, **geting_login_data())
    browser = city_selection(browser)
    sleep(15)
    with open(f'{FILE_PATH}page.txt', 'w', encoding="utf-8") as file:
        file.write(browser.page_source)


# Делать ли паузы между переходами на страницы?
