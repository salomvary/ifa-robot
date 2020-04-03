import logging

logging.basicConfig(level=logging.INFO)

import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
import geckodriver_autoinstaller
import code
import time

geckodriver_autoinstaller.install()


def main():
    config = configparser.ConfigParser()
    config.read('ifa-robot.ini')

    try:
        driver = webdriver.Firefox()
        driver.get("https://ohp-20.asp.lgov.hu")

        nyitolap = (
            Nyitolap(driver)
                .wait_for_page()
                .click_login_button()
        )

        kau = (
            KAU(driver)
                .wait_for_page()
                # Clicking immediately does not work
                .sleep(1)
                .click_login_with_ugyfelkapu()
        )

        kau_login = (
            KAULogin(driver)
                .wait_for_page()
                .login(
                    config['DEFAULT']['username'],
                    config['DEFAULT']['password'],
                )
        )

        kau_login = (
            Welcome(driver)
                .wait_for_page()
                .click_ugyinditas()
        )

        ugyinditas = (
            Ugyinditas(driver)
                .wait_for_page()
                .select_case(
                    "Saját néven (magánszemélyként)",
                    "Adóügy",
                    "idegenforgalmi adó"
                )
        )

        ugyinditas_results = (
            UgyinditasResults(driver)
                .wait_for_page()
                .click_last_fill_button()
        )

        form = (
            Form(driver)
                .wait_for_page()
        )

        # TODO: wait form the form to fully load
        # TODO: dismiss non-actianable dialogs
        # TODO: fill the form automatically

        form_complete = False

        while not form_complete:

            input("Fill in the form, hit ENTER when you are done > ")

            form.click_more() \
                .click_submit() \
                .confirm_submit_dialog()

            if form.has_errors():
                print("Looks like the form has some errors :(")
            else:
                form_complete = True

        # TODO continue submitting form
        # TODO download results

    except Exception as e:
        logging.exception(e)
    finally:
        if driver:
            answer = input(
                "Type C and ENTER to start interactive console or hit ENTER to quit > "
            )

            if answer.lower() == "c":
                code.interact(local=locals())

            driver.quit()


class Page:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_page(self, timeout = 10):
        WebDriverWait(self.driver, timeout).until(self.CONDITION)
        logging.info(f"{self.name} loaded")

        return self

    def sleep(self, duration):
        time.sleep(duration)

        return self


class Nyitolap(Page):
    name = "Nyitólap"

    LOGIN_BUTTON = (By.PARTIAL_LINK_TEXT, "ÜGYINTÉZÉS BEJELENTKEZÉSSEL")

    CONDITION = expected_conditions.presence_of_element_located(LOGIN_BUTTON)

    def click_login_button(self):
        element = self.driver.find_element(*Nyitolap.LOGIN_BUTTON)
        element.click()

        return self


class KAU(Page):
    name = "KAÜ"

    UGYFELKAPU_BUTTTON = (By.XPATH, '//button[contains(text(), "Ügyfélkapu")]')

    CONDITION = expected_conditions.presence_of_element_located(UGYFELKAPU_BUTTTON)

    def click_login_with_ugyfelkapu(self):
        element = self.driver.find_element(*KAU.UGYFELKAPU_BUTTTON)
        element.click()

        return self


class KAULogin(Page):
    name = "KAÜ Login"

    LOGIN_BUTTON = (By.XPATH, '//button[contains(text(), "belépés")]')
    USERNAME_INPUT = (By.NAME, "felhasznaloNev")
    PASSWORD_INPUT = (By.NAME, "jelszo")

    CONDITION = expected_conditions.presence_of_element_located(LOGIN_BUTTON)

    def login(self, username, password):
        username_input = self.driver.find_element(*self.USERNAME_INPUT)
        password_input = self.driver.find_element(*self.PASSWORD_INPUT)
        login_button = self.driver.find_element(*self.LOGIN_BUTTON)

        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()

        return self


class Welcome(Page):
    name = "Nyitólap bejelentkezve"

    UGYINDITAS_BUTTON = (By.PARTIAL_LINK_TEXT, "ÜGYINDÍTÁS")

    CONDITION = expected_conditions.presence_of_element_located(UGYINDITAS_BUTTON)

    def click_ugyinditas(self):
        ugyinditas_button = self.driver.find_element(*self.UGYINDITAS_BUTTON)
        ugyinditas_button.click()

        return self


class Ugyinditas(Page):
    name = "Ügyindítás"

    SUBMIT_BUTTON = (By.XPATH, '//button[contains(text(), "Űrlap keresés")]')
    SZEREPKOR_SELECT = (By.NAME, "kepviselet.szerepkor")
    SECTOR_SELECT = (By.NAME, "sector")
    CASE_TYPE_SELECT = (By.NAME, "caseType")

    CONDITION = expected_conditions.presence_of_element_located(SUBMIT_BUTTON)

    def select_case(self, szerepkor, sector, case_type):
        Select(self.driver \
            .find_element(*self.SZEREPKOR_SELECT)) \
            .select_by_visible_text(szerepkor)

        Select(self.driver \
            .find_element(*self.SECTOR_SELECT)) \
            .select_by_visible_text(sector)

        Select(self.driver \
            .find_element(*self.CASE_TYPE_SELECT)) \
            .select_by_visible_text(case_type)

        self.driver \
            .find_element(*self.SUBMIT_BUTTON) \
            .click()

class UgyinditasResults(Page):
    name = "Ügyindítás találatok"

    FILL_BUTTON = (By.XPATH, '//button[contains(text(), "Online kitöltés")]')

    CONDITION = expected_conditions.presence_of_element_located(FILL_BUTTON)

    def click_last_fill_button(self):
        buttons = self.driver.find_elements(*self.FILL_BUTTON)
        buttons[-1].click()

class Form(Page):
    name = "Űrlap"

    NEXT_CHAPTER_BUTTON = (By.PARTIAL_LINK_TEXT, "Következő fejezet")
    MORE_BUTTON = (By.PARTIAL_LINK_TEXT, "További műveletek")
    SUBMIT_FORM_BUTTON = (By.PARTIAL_LINK_TEXT, "Az űrlap beküldése")
    MAIN_FRAME = (By.ID, "iform-iframe")

    CONDITION = expected_conditions.presence_of_element_located(NEXT_CHAPTER_BUTTON)
    IFRAME_CONDITION = expected_conditions.frame_to_be_available_and_switch_to_it(MAIN_FRAME)

    def wait_for_page(self):
        WebDriverWait(self.driver, 10).until(self.IFRAME_CONDITION)
        return super().wait_for_page(30)

    def click_next_chapter(self):
        self.driver.find_element(*self.NEXT_CHAPTER_BUTTON).click()

        return self

    def click_more(self):
        self.driver.find_element(*self.MORE_BUTTON).click()

        return self

    def click_submit(self):
        self.driver.find_element(*self.SUBMIT_FORM_BUTTON).click()

        return self

    def get_dialog(self):
        return ModalDialog(self.driver)

    def confirm_submit_dialog(self):
        dialog = self.get_dialog()
        dialog_body = dialog.get_body()
        dialog.click_button("Igen")

        logging.info(
            "Confirmed dialog with the following text:" +
            dialog_body
        )

        return self

    def has_errors(self):
        dialog = self.get_dialog()
        return "hibalista" in dialog.get_header().lower()


class ModalDialog:

    ALERTDIALOG = (By.XPATH, "//*[@role='alertdialog']")
    MODAL_BODY = (By.CLASS_NAME, 'modal-body')
    MODAL_HEADER = (By.CLASS_NAME, 'modal-header')

    def __init__(self, driver):
        self.driver = driver
        self.element = self.driver.find_element(*self.ALERTDIALOG)

    def _select_button(self, text):
        return (By.XPATH, f'//button[contains(text(), "{text}")]')

    def get_body(self):
        return self.element.find_element(*self.MODAL_BODY).text

    def get_header(self):
        return self.element.find_element(*self.MODAL_HEADER).text

    def click_button(self, button_text):
        self.element.find_element(*self._select_button(button_text)).click()

        return self

if __name__ == "__main__":
    main()
