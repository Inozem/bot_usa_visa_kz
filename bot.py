from time import sleep

from mechanize import Browser


def starting_browser():
    browser = Browser()
    browser.set_handle_robots(False)
    browser.addheaders = [
        ('Accept-Language', 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'),
        (
            'User-agent',
            ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             '(KHTML, like Gecko)Chrome/107.0.0.0 Safari/537.36')
        )
    ]
    return browser


def geting_login_data():
    login_input_text = {
        'email': 'Введите адрес электронной почты: \n',
        'password': 'Введите пароль: \n'
    }
    login_data = {key: input(value) for key, value in login_input_text.items()}
    return login_data


def authorization(browser, email, password):
    browser.open('https://cgifederal.secure.force.com/')
    browser.select_form(action=('https://cgifederal.secure.force.com/SiteLogin?refURL=http%3A%2F%2Fcgifederal.secure.force.com%2F'))
    print(browser.form)
    browser.form['loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:username'] = email
    browser.form['loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:password'] = password
    browser.find_control('loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:j_id167').selected = True
    return browser.submit()


if __name__ == '__main__':
    browser = starting_browser()
    page_account = authorization(browser, **geting_login_data())
    # sleep(10)
    print(page_account.geturl())
    page_code = str(page_account.read())  # .split('\\n')
    with open('C:/Users/inoze/Downloads/page.html', 'w') as output:  # Путь для сохранения файла прописать свой
        output.write(page_code)
        # for string in page_code:
            # output.write(string + '\n')
