import os
from datetime import date
from time import sleep

from dotenv import find_dotenv, load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from rucaptcha import RuCaptcha
from rucaptcha.exceptions import RuCaptchaError

load_dotenv(find_dotenv())

TIME_OUT = 10  # Максимальное время ожидания загрузки элемента (секунды)
MAX_ERROR_COUNT = 3  # Максимальное количество попыток при появлении ошибок
RUCAPTCHA_API_KEY = os.getenv('RUCAPTCHA_API_KEY')


def starting_browser():
    """Настройка и запуск браузера."""
    options = webdriver.ChromeOptions()
    # TODO: в конце - проверить работу в безоконном режиме (headless)
    # TODO: аргументы браузера можно принимать через параметр функции
    #  и при этом вычитывать их из переменных окружения,
    #  чтобы локально проверять в обычном режиме, а на сервере запускать в headless
    #  и при этом не трогать код ;)
    options.add_argument("window-size=800,600")
    browser = webdriver.Chrome(options=options)
    return browser


def waiting_picture(browser, picture_id, error_count=0):
    """Ожидание загрузки картинки с капчой"""
    for error_count in range(TIME_OUT):
        picture_size = browser.find_element(By.ID, picture_id).size
        if error_count >= TIME_OUT:
            raise Exception("Проблемы на стороне сервиса. "
                            "Капча. Не прогружается картинка.")
        elif int(picture_size["height"]) <= 40:
            sleep(1)


# TODO: добавить везде аннотации типов
def reading_captcha(picture):
    """Разгадывание капчи."""
    captcha = None
    answer_holder = RuCaptcha(RUCAPTCHA_API_KEY).solve(picture)
    for _ in range(MAX_ERROR_COUNT):
        try:
            captcha = answer_holder.wait_answer()
        except RuCaptchaError:
            pass
    if not captcha:
        raise RuCaptchaError("Проблемы на стороне сервиса. Капча. "
                             "Не удалось разгадать.")
    return captcha


def authorization(browser, answers, error_count=0):
    """Авторизация."""
    required_params = {
        "email": "Введите адрес электронной почты: \n",
        "password": "Введите пароль: \n",
    }
    login_data = {
        key: answers.get(key) or input(value) for key, value in required_params.items()
    }
    browser.get("https://cgifederal.secure.force.com/")
    element_id_or_name_part = (
        "loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:"
    )
    element_username_id = f"{element_id_or_name_part}username"
    element_username = browser.find_element(By.ID, element_username_id)
    element_username.send_keys(login_data["email"])

    element_password_id = f"{element_id_or_name_part}password"
    element_password = browser.find_element(By.ID, element_password_id)
    element_password.send_keys(login_data["password"])

    browser.find_element(By.NAME, f"{element_id_or_name_part}j_id167").click()

    element_picture_id = f"{element_id_or_name_part}theId"
    waiting_picture(browser, element_picture_id)
    element_picture = browser.find_element(By.ID, element_picture_id)
    picture_base64 = element_picture.screenshot_as_base64
    element_recaptcha_response_field = browser.find_element(
        By.ID,
        f"{element_id_or_name_part}recaptcha_response_field"
    )
    sleep(10)  # element_recaptcha_response_field.send_keys(reading_captcha(picture_base64))

    answers.update(login_data)

    element_login_button_id = f"{element_id_or_name_part}loginButton"
    browser.find_element(By.ID, element_login_button_id).click()

    error_id_part = "error:j_id132:j_id133:0:j_id134:j_id135:j_id137"
    if error_id_part in browser.page_source:
        error_count += 1
        error_text = browser.find_element(
            By.ID,
            f"{element_id_or_name_part}{error_id_part}"
        ).text
        if "Captcha." in error_text and error_count < MAX_ERROR_COUNT:
            browser, answers = authorization(browser, answers, error_count)
        elif error_count >= MAX_ERROR_COUNT:
            raise Exception("Проблемы на стороне сервиса. Капча.")
        else:
            raise Exception(error_text)
    return browser, answers


def city_selection(browser, answers):
    """Выбор города."""
    tr_elements = browser.find_elements(By.TAG_NAME, "tr")
    cities = {i: tr_elements[i].text for i in range(len(tr_elements))}
    city_ind = None
    try:
        city_ind = [*cities.values()].index(answers["city"])
    except (ValueError, KeyError):
        input_text_part_1 = (
            "Введите номер города, в котором хотите пройти собеседование:\n"
        )
        input_text_part_2 = (
            "\n".join([f"{ind} - {name}" for ind, name in cities.items()])
            + "\n"
        )
        city_ind = int(input(f"{input_text_part_1}{input_text_part_2}"))
    try:
        tr_elements[city_ind].find_element(By.TAG_NAME, "input").click()
    except IndexError:
        raise Exception(f"Город под номером {city_ind} недоступен")
    answers.update({"city": cities[city_ind]})
    sleep(5)
    browser.find_element(By.NAME, "j_id0:SiteTemplate:j_id112:j_id169").click()
    return browser, answers


def visa_category_selection(browser, answers):
    """Выбор категории визы."""
    visa_category_supported = [
        ("Виза B1/B2 (туризм, посещение родственников, деловые поездки "
         "и не срочное медицинское лечение)"),
        ("Визы для студентов и участников программ обмена (первичные "
         "обращения и обращения без прохождения личного собеседования)"),
        ("Визы для студентов и участников программ обмена "
         "(которым ранее было отказано в визе)"),
    ]
    tr_elements = browser.find_elements(By.TAG_NAME, "tr")
    visa_categories = {i: tr_elements[i].text for i in range(len(tr_elements))}
    try:
        visa_ind = [*visa_categories.values()].index(answers["visa_category"])
    except (ValueError, KeyError):
        input_text_part_1 = "Выберите номер визовой категории:\n"
        input_text_part_2 = (
            "\n".join([f"{ind} - {type}" for ind, type in visa_categories.items()])
            + "\n"
        )
        visa_ind = int(input(f"{input_text_part_1}{input_text_part_2}"))
    try:
        tr_elements[visa_ind].find_element(By.TAG_NAME, "input").click()
        if tr_elements[visa_ind].text not in visa_category_supported:
            raise Exception(
                f"Сервис не работает с категорией виз под номером {visa_ind}"
            )
    except IndexError:
        raise Exception(f"Нет категории с номером {visa_ind}")
    answers.update({"visa_category": visa_categories[visa_ind]})
    sleep(5)
    browser.find_element(By.NAME, "j_id0:SiteTemplate:j_id109:j_id166").click()
    return browser, answers


def visa_class_selection(browser, answers):
    """Выбор класса визы."""
    visa_class_supported = [
        "B1 - Виза для деловых поездок",
        "B1/B2 - Виза для деловых и туристических поездок",
        "B2 - Виза для туристических поездок и лечения",
        ("F-1 - Студенческая виза для академических "
         "или языковых программ обучения"),
        "F-2 - Виза для супруга(и)/ребенка держателя визы F-1",
    ]
    table_elements = browser.find_elements(By.TAG_NAME, "table")
    tr_elements = table_elements[1].find_elements(By.TAG_NAME, "tr")
    visa_classes = {i: tr_elements[i].text for i in range(len(tr_elements))}
    try:
        visa_ind = [*visa_classes.values()].index(answers["visa_class"])
    except (ValueError, KeyError):
        input_text_part_1 = "Выберите номер визового класса:\n"
        input_text_part_2 = (
            "\n".join([f"{ind} - {type}" for ind, type in visa_classes.items()]) + "\n"
        )
        visa_ind = int(input(f"{input_text_part_1}{input_text_part_2}"))
    try:
        tr_elements[visa_ind].find_element(By.TAG_NAME, "input").click()
        if tr_elements[visa_ind].text not in visa_class_supported:
            raise Exception(
                f"Сервис не работает с категорией виз под номером {visa_ind}"
            )
    except IndexError:
        raise Exception(f"Нет категории с номером {visa_ind}")
    answers.update({"visa_class": visa_classes[visa_ind]})
    sleep(5)
    browser.find_element(By.NAME, "j_id0:SiteTemplate:theForm:j_id178").click()
    return browser, answers


def answering_questions(browser, answers):
    """Ответы на вопросы."""
    sleep(5)
    current_url = browser.current_url
    bottom_answer = {
        "YES": "j_id0:SiteTemplate:j_id110:j_id177",
        "NO": "j_id0:SiteTemplate:j_id110:j_id176",
    }
    questions_and_answers = {
        "Вы старше 80 лет?": "NO",
        "Вы младше 14 лет?": "NO",
        "Оплатили ли Вы сбор SEVIS?": "YES",
    }
    while "selectdropboxquestions" in current_url:
        question = browser.find_element(
            By.CLASS_NAME,
            "ui-state-highlight"
        ).text.strip()
        try:
            answer = questions_and_answers[question]
        except KeyError:
            answer = ["YES", "NO"][
                int(input(f"{question}\n 0 - YES\n 1 - NO\n"))
            ]
        browser.find_element(By.NAME, bottom_answer[answer]).click()
        sleep(5)
        current_url = browser.current_url
    return browser


def status_selection(browser, answers):
    """Выбор статуса."""
    tr_elements = browser.find_elements(By.TAG_NAME, "tr")[1:]
    statuses = {
        i: tr_elements[i].text.split(" ")[0] for i in range(len(tr_elements))
    }
    status_ind = None
    try:
        status_ind = [*statuses.values()].index(answers["status"])
    except (ValueError, KeyError):
        input_text_part_1 = "Введите номер статуса:\n"
        input_text_part_2 = (
            "\n".join([f"{ind} - {name}" for ind, name in statuses.items()])
            + "\n"
        )
        status_ind = int(input(f"{input_text_part_1}{input_text_part_2}"))
    try:
        tr_elements[status_ind].find_element(By.TAG_NAME, "input").click()
    except IndexError:
        raise Exception(f"Статус под номером {status_ind} недоступен")
    answers.update({"status": statuses[status_ind]})
    sleep(5)
    browser.find_element(By.NAME, "j_id0:SiteTemplate:theForm:j_id170").click()
    return browser, answers


def registration(browser):
    browser.find_element(
        By.NAME,
        "thePage:SiteTemplate:theForm:j_id203:0:j_id205"
    ).click()
    sleep(5)  # Ожидание обновления данных на сайте

    # Отправка заявки на собеседование
    browser.find_element(
        By.NAME,
        "thePage:SiteTemplate:theForm:addItem"
    ).click()

    info_title = browser.find_element(By.CLASS_NAME, "apptSchedMsg").text
    info = [info_title]
    try:
        info_string_titles = [
            "Адрес:",
            "Дата собеседования:",
            "Время собеседования:"
        ]
        info_table = browser.find_element(By.CLASS_NAME, "appTable")
        info_table_strings = info_table.find_elements(By.TAG_NAME, "tr")
        for string in info_table_strings:
            for title in info_string_titles:
                if title in string.text:
                    info_string_value = string.find_elements(
                        By.TAG_NAME,
                        "td"
                    )[1].text
                    info.append(f"{title} {info_string_value}")
    except NoSuchElementException:
        info.append(
            "Что-то пошло не так."
            "Возможно запись на собеседование не была завершена."
            "Для получения более подробной информации обратитесь в "
            "поддержку."
        )
    return "\n".join(info)


def getting_all_free_dates(browser):
    # TODO: чтобы не зависеть от языка (может не быть в выборе русского)
    #  предлагаю просто разбирать календарную страницу как есть
    #  и по номерам месяцев формировать дату (месяц в параметре onclick сидит)
    free_dates = []
    months = [
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ]
    next_year = date.today().year + 1
    next_month = (date.today().month + 1) % 12
    this_day = date.today().day
    last_free_date = date(next_year, next_month, this_day)
    too_late = False
    while not too_late:
        calendar_first_month = browser.find_element(
            By.CLASS_NAME, "ui-datepicker-group-first"
        )
        month, year = calendar_first_month.find_element(
            By.CLASS_NAME, "ui-datepicker-header"
        ).text.split(" ")
        month = months.index(month.split("\n")[1]) + 1
        year = int(year)
        weeks = calendar_first_month.find_elements(By.TAG_NAME, "tr")
        for week in weeks:
            days = week.find_elements(By.TAG_NAME, "td")
            for day in days:
                try:
                    day.find_element(By.TAG_NAME, "a")
                    checking_date = date(year, month, int(day.text))
                    free_dates.append(checking_date.strftime("%d.%m.%Y"))
                    if checking_date >= last_free_date:
                        too_late = True
                except NoSuchElementException:
                    pass
        browser.find_element(By.CLASS_NAME, "ui-datepicker-next").click()
    return free_dates


def searching_free_date(browser, answers, error_count=0):
    """Поиск свободных дат."""
    element_picture_id = "thePage:SiteTemplate:recaptcha_form:captcha_image"
    waiting_picture(browser, element_picture_id)
    element_picture = browser.find_element(By.ID, element_picture_id)
    picture_base64 = element_picture.screenshot_as_base64
    element_recaptcha_response_field = browser.find_element(
        By.ID,
        "thePage:SiteTemplate:recaptcha_form:recaptcha_response_field"
    )
    element_recaptcha_response_field.send_keys(reading_captcha(picture_base64))

    browser.find_element(
        By.NAME,
        "thePage:SiteTemplate:recaptcha_form:j_id130"
    ).click()
    if (
        "Перепечатайте слова отображенные ниже" in browser.page_source
        and error_count < MAX_ERROR_COUNT
    ):
        error_count += 1
        browser, answers = searching_free_date(browser, answers, error_count)
    elif error_count >= MAX_ERROR_COUNT:
        raise Exception("Проблемы на стороне сервиса. Капча.")

    try:
        months = [
            "Январь",
            "Февраль",
            "Март",
            "Апрель",
            "Май",
            "Июнь",
            "Июль",
            "Август",
            "Сентябрь",
            "Октябрь",
            "Ноябрь",
            "Декабрь",
        ]
        dates = answers["dates"].split(" - ")
        first_date = date(*[int(d) for d in dates[0].split(".")][::-1])
        last_date = date(*[int(d) for d in dates[1].split(".")][::-1])
        earliest_date = ""
        while True:
            sleep(5)
            calendar_first_month = browser.find_element(
                By.CLASS_NAME, "ui-datepicker-group-first"
            )
            month, year = calendar_first_month.find_element(
                By.CLASS_NAME, "ui-datepicker-header"
            ).text.split(" ")
            month = months.index(month.split("\n")[1]) + 1
            year = int(year)
            weeks = calendar_first_month.find_elements(By.TAG_NAME, "tr")
            for week in weeks:
                days = week.find_elements(By.TAG_NAME, "td")
                for day in days:
                    try:
                        day.find_element(By.TAG_NAME, "a")
                        checking_date = date(year, month, int(day.text))
                        if not earliest_date:
                            earliest_date = checking_date.strftime("%d.%m.%Y")
                        if first_date <= checking_date <= last_date:
                            day.click()
                            return registration(browser)
                        elif checking_date > last_date:
                            return f"Нет подходящих дат. Самая ранняя свободная дата: {int(day.text)}.{month}.{year}"
                    except (NoSuchElementException):
                        pass
            browser.find_element(By.CLASS_NAME, "ui-datepicker-next").click()
    except KeyError:
        return registration(browser)


def main(answers):
    browser = starting_browser()
    browser, answers = authorization(browser, answers)

    # Выбор русского языка
    Select(
        browser.find_element(
            By.NAME,
            "j_id0:SiteTemplate:j_id14:j_id15:j_id26:j_id27:j_id28:j_id30"
        )
    ).select_by_visible_text("Russian")

    # Новое обращение / Запись на собеседование
    browser.find_elements(By.TAG_NAME, "a")[2].click()

    # Выбор неиммиграционной визы (по умолчанию)
    browser.find_element(
        By.NAME, "j_id0:SiteTemplate:theForm:j_id176"
    ).click()

    browser, answers = city_selection(browser, answers)
    browser, answers = visa_category_selection(browser, answers)
    browser, answers = visa_class_selection(browser, answers)

    # Персональные данные введены / Далее
    browser.find_element(
        By.NAME,
        "thePage:SiteTemplate:theForm:j_id1279"
    ).click()

    # Члены семьи добавлены в список / Далее
    browser.find_element(
        By.NAME,
        "j_id0:SiteTemplate:j_id856:continueBtn"
    ).click()

    browser = answering_questions(browser, answers)

    # Информация о доставке документов / Далее
    browser.find_element(
        By.NAME,
        "thePage:SiteTemplate:theForm:Continue"
    ).click()
    sleep(5)

    # Информация о визовом сборе (всплывающее окно) / Далее
    browser.find_element(
        By.CLASS_NAME,
        "ui-button-text-only"
    ).click()
    sleep(5)

    # Регистрация номера платежа / Далее
    browser.find_element(
        By.NAME,
        "j_id0:SiteTemplate:theForm:continue_btn"
    ).click()

    browser, answers = status_selection(browser, answers)
    if answers["find_all_free_dates"]:
        return "\n".join(getting_all_free_dates(browser))
    else:
        return searching_free_date(browser, answers)


if __name__ == "__main__":
    answers = {
        "email": os.getenv("CGIFEDERAL_EMAIL"),
        "password": os.getenv("CGIFEDERAL_PASSWORD"),
        "city": os.getenv("CGIFEDERAL_CITY"),
        "visa_category": os.getenv("CGIFEDERAL_VISA_CATEGORY"),
        "visa_class": os.getenv("CGIFEDERAL_VISA_CLASS"),
        "status": os.getenv("CGIFEDERAL_STATUS"),
        "dates": os.getenv("CGIFEDERAL_DATES"),
        "find_all_free_dates": True,
    }
    main(answers)
    sleep(600)
