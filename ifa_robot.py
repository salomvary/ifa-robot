import logging
import sys

logging.basicConfig(level=logging.INFO)

import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import geckodriver_autoinstaller
import code
import time
from form_data import elolap_data, folap_data, b_betetlap_data

geckodriver_autoinstaller.install()


def main():
    config = configparser.ConfigParser()
    config.read("ifa-robot.ini")

    try:
        driver = webdriver.Firefox()
        driver.get("https://ohp-20.asp.lgov.hu")

        nyitolap = Nyitolap(driver).wait_for_page().click_login_button()

        kau = (
            KAU(driver)
            .wait_for_page()
            # Clicking immediately does not work
            .sleep(5)
            .click_login_with_ugyfelkapu()
        )

        kau_login = (
            KAULogin(driver)
            .wait_for_page()
            .login(config["DEFAULT"]["username"], config["DEFAULT"]["password"],)
        )

        kau_login = Welcome(driver).wait_for_page().click_ugyinditas()

        ugyinditas = (
            Ugyinditas(driver)
            .wait_for_page()
            .select_case(
                "Saját néven (magánszemélyként)", "Adóügy", "idegenforgalmi adó"
            )
        )

        ugyinditas_results = (
            UgyinditasResults(driver).wait_for_page().click_last_fill_button()
        )

        form = (
            Form(driver)
            .wait_for_page()
            # Wait form the form to fully load
            .wait_for_progress_dialog_invisible()
            # Dismiss non-actianable dialogs
            .dismiss_alert()
            # Fill the form automatically
            .fill_fields(elolap_data)
            .click_next_chapter()
            .fill_fields(folap_data)
            .click_next_chapter()
            .fill_fields(b_betetlap_data)
        )

        form_complete = False

        while not form_complete:

            input("Fill in the form, hit ENTER when you are done > ")

            form.click_more().click_submit().confirm_submit_dialog()

            if form.has_errors():
                print("Looks like the form has some errors :(")
            else:
                form_complete = True

        # Avoid "can't access dead object" exception by switching back to the main frame
        driver.switch_to.default_content()

        add_attachments = (
            AddAttachmentsSubmit(driver)
            # This is very slow
            .wait_for_page(60).click_submit_button()
        )

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


def by_partial_button_text(text: str):
    return (By.XPATH, f'//button[contains(text(), "{text}")] | //input[(@type="submit" or @type="button" or @type="reset" or @type="search") and contains(@value, "{text}")]')

class Page:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_page(self, timeout=10):
        self.wait_until(timeout, self.CONDITION)
        logging.info(f"{self.name} loaded")

        return self

    def wait_until(self, timeout, condition):
        should_try = True

        while should_try:
            try:
                WebDriverWait(self.driver, timeout).until(condition)
                should_try = False
            except:
                print(
                    f"Waiting for this condition timed out after {timeout}: ${condition}."
                )
                answer = input("Would you like to try again? [Y/n]> ")
                should_try = answer.lower() == "y"
                if not should_try:
                    sys.exit(1)


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

    UGYFELKAPU_BUTTTON = by_partial_button_text("Ügyfélkapu")

    CONDITION = expected_conditions.presence_of_element_located(UGYFELKAPU_BUTTTON)

    def click_login_with_ugyfelkapu(self):
        element = self.driver.find_element(*KAU.UGYFELKAPU_BUTTTON)
        element.click()

        return self


class KAULogin(Page):
    name = "KAÜ Login"

    LOGIN_BUTTON = (By.XPATH, '//button[contains(text(), "bejelentkezés")]')
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
        Select(self.driver.find_element(*self.SZEREPKOR_SELECT)).select_by_visible_text(
            szerepkor
        )

        Select(self.driver.find_element(*self.SECTOR_SELECT)).select_by_visible_text(
            sector
        )

        Select(self.driver.find_element(*self.CASE_TYPE_SELECT)).select_by_visible_text(
            case_type
        )

        self.driver.find_element(*self.SUBMIT_BUTTON).click()

        return self


class UgyinditasResults(Page):
    name = "Ügyindítás találatok"

    FILL_BUTTON = (By.XPATH, '//button[contains(text(), "Online kitöltés")]')

    CONDITION = expected_conditions.presence_of_element_located(FILL_BUTTON)

    def click_last_fill_button(self):
        buttons = self.driver.find_elements(*self.FILL_BUTTON)
        buttons[-1].click()

        return self


class Form(Page):
    name = "Űrlap"

    NEXT_CHAPTER_BUTTON = (By.PARTIAL_LINK_TEXT, "Következő fejezet")
    MORE_BUTTON = (By.PARTIAL_LINK_TEXT, "További műveletek")
    SUBMIT_FORM_BUTTON = (By.PARTIAL_LINK_TEXT, "Az űrlap beküldése")
    MAIN_FRAME = (By.ID, "iform-iframe")

    CONDITION = expected_conditions.presence_of_element_located(NEXT_CHAPTER_BUTTON)
    IFRAME_CONDITION = expected_conditions.frame_to_be_available_and_switch_to_it(
        MAIN_FRAME
    )

    def wait_for_page(self):
        self.wait_until(10, self.IFRAME_CONDITION)
        super().wait_for_page(30)

        return self

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
        return ModalDialog(self.driver, wait_for_visible_timeout=5)
    
    def has_dialog(self):
        try:
            ModalDialog(self.driver)
            return True
        except:
            return False

    def wait_for_progress_dialog_invisible(self):
        current_dialog = self.get_dialog()
        if current_dialog:
            logging.info(
                f"Dialog visible:\nheader: '{current_dialog.get_header()}'\nbody:\n{current_dialog.get_body()}"
            )

            if "feldolgozás folyamatban" in current_dialog.get_header().lower():
                current_dialog.wait_for_invisible(30)
        return self

    def dismiss_alert(self):
        dialog = AlertDialog(self.driver)
        if "Az Alaprendelkezés lekérdezése eredménytelen volt" in dialog.get_content():
            dialog.click_button("Bezárás")
            logging.info("Dismissed expected alert")
        else:
            logging.warning(f"Unexpected alert visible: '{dialog.get_content}'")

        return self

    def fill_fields(self, fields):
        for selector, value in fields.items():
            input = self.driver.find_element(By.CSS_SELECTOR, selector)
            logging.info(
                f"Setting form field {selector} ({input.tag_name}) to '{value}'"
            )
            if input.tag_name == "SELECT":
                Select(input).select_by_value(value)
            elif input.get_attribute("data-mask"):
                # Typing into "mask" inputs (eg. tax id) does not work without extra treatment
                self.type_mask(input, value)
            else:
                input.send_keys(value)
            # Interacting with inputs might bring up the progress dialog which
            # obscures the "next chapter buttons". Wait until it goes away
            if self.has_dialog():
                self.wait_for_progress_dialog_invisible()

        return self

    def type_mask(self, input, value):
        # Move to the input and focus it
        input.click()
        # Mask input only works if the cursor is at the beginning
        input.send_keys(Keys.HOME)
        for c in value:
            # Batch-performing with ActionChain did not work here
            ActionChains(self.driver).key_down(c).perform()

    def confirm_submit_dialog(self):
        dialog = self.get_dialog()
        dialog_body = dialog.get_body()
        dialog.click_button("Igen")

        logging.info("Confirmed dialog with the following text:" + dialog_body)

        return self

    def has_errors(self):
        dialog = self.get_dialog()
        return "hibalista" in dialog.get_header().lower()


class AddAttachmentsSubmit(Page):
    name = "Csatolmányok hozzáadása"

    SUBMIT_BUTTON = (By.XPATH, '//button[contains(text(), "Beküldés")]')
    # < button
    # id = "submitbutton"
    # type = "submit"
    #
    # class ="btn btn-default btn-large btn-nav btn-pay" role="button" > Beküldés < / button >

    CONDITION = expected_conditions.presence_of_element_located(SUBMIT_BUTTON)

    def click_submit_button(self):
        button = self.driver.find_element(*self.SUBMIT_BUTTON)
        button.click()

        return self


# TODO
# Sikeres beküldés!


class ModalDialog(Page):
    ALERTDIALOG = (By.XPATH, "//*[@role='alertdialog']")
    MODAL_BODY = (By.CLASS_NAME, "modal-body")
    MODAL_HEADER = (By.CLASS_NAME, "modal-header")

    CONDITION = expected_conditions.presence_of_element_located(ALERTDIALOG)

    def __init__(self, driver, wait_for_visible_timeout=0):
        self.driver = driver
        if wait_for_visible_timeout > 0:
            self.wait_until(wait_for_visible_timeout, self.CONDITION)
        self.element = self.driver.find_element(*self.ALERTDIALOG)

    def _select_button(self, text):
        return (By.XPATH, f'//button[contains(text(), "{text}")]')

    def get_body(self):
        return self.element.find_element(*self.MODAL_BODY).text

    def get_header(self):
        return self.element.find_element(*self.MODAL_HEADER).text

    def wait_for_invisible(self, timeout):
        self.wait_until(
            timeout, expected_conditions.invisibility_of_element(self.element)
        )
        return self

    def click_button(self, button_text):
        self.element.find_element(*self._select_button(button_text)).click()

        return self


# Another kind of dialog
class AlertDialog(Page):
    ALERTDIALOG = (By.XPATH, "//*[@role='dialog']")
    TITLE = (By.CLASS_NAME, "ui-dialog-title")
    CONTENT = (By.CLASS_NAME, "ui-dialog-content")

    def __init__(self, driver):
        self.driver = driver
        self.element = self.driver.find_element(*self.ALERTDIALOG)

    def _select_button(self, text):
        return (By.XPATH, f'//button[contains(., "{text}")]')

    def get_title(self):
        return self.element.find_element(*self.TITLE).text

    def get_content(self):
        return self.element.find_element(*self.CONTENT).text

    def click_button(self, button_text):
        self.element.find_element(*self._select_button(button_text)).click()

        return self


if __name__ == "__main__":
    main()
