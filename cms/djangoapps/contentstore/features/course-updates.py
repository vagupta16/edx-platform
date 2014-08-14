# pylint: disable=C0111
# pylint: disable=W0621

from lettuce import world, step
from selenium.webdriver.common.keys import Keys
from nose.tools import assert_in  # pylint: disable=E0611


@step(u'I go to the course updates page')
def go_to_updates(_step):
    menu_css = 'li.nav-course-courseware'
    updates_css = 'li.nav-course-courseware-updates a'
    world.css_click(menu_css)
    world.css_click(updates_css)


@step(u'I add a new update with the text "([^"]*)"$')
def add_update(_step, text):
    update_css = 'a.new-update-button'
    world.css_click(update_css)
    change_text(text)
    save_update()


@step(u'I should see the update "([^"]*)"$')
def check_update(_step, text):
    update_css = 'div.update-contents'
    update_html = world.css_find(update_css).html
    assert_in(text, update_html)


@step(u'I should not see the update "([^"]*)"$')
def check_no_update(_step, text):
    update_css = 'div.update-contents'
    assert world.is_css_not_present(update_css)


@step(u'I modify the text to "([^"]*)"$')
def modify_update(_step, text):
    button_css = 'div.post-preview a.edit-button'
    world.css_click(button_css)
    change_text(text)
    save_update()


@step(u'I change the update from "([^"]*)" to "([^"]*)"$')
def change_existing_update(_step, before, after):
    verify_text_in_editor_and_update('div.post-preview a.edit-button', before, after)
    save_update()


@step(u'I delete the update$')
def click_button(_step):
    button_css = 'div.post-preview a.delete-button'
    world.css_click(button_css)


@step(u'I edit the date to "([^"]*)"$')
def change_date(_step, new_date):
    button_css = 'div.post-preview a.edit-button'
    world.css_click(button_css)
    date_css = 'input.date'
    date = world.css_find(date_css)
    for i in range(len(date.value)):
        date._element.send_keys(Keys.END, Keys.BACK_SPACE)
    date._element.send_keys(new_date)
    save_css = 'a.save-button'
    world.css_click(save_css)


@step(u'I should see the date "([^"]*)"$')
def check_date(_step, date):
    date_css = 'span.date-display'
    assert_in(date, world.css_html(date_css))


@step(u'I modify the handout to "([^"]*)"$')
def edit_handouts(_step, text):
    edit_css = 'div.course-handouts > a.edit-button'
    world.css_click(edit_css)
    change_text(text)
    save_handout()


@step(u'I see the handout "([^"]*)"$')
def check_handout(_step, handout):
    handout_css = 'div.handouts-content'
    assert_in(handout, world.css_html(handout_css))


def change_text(text):
    script = """
    var editor = tinyMCE.activeEditor;
    editor.setContent(arguments[0]);"""
    world.browser.driver.execute_script(script, str(text))
    world.wait_for_ajax_complete()


def save_update():
    world.css_click('a.save-button')


def save_handout():
    world.css_click('a.action-save')


def verify_text_in_editor_and_update(button_css, before, after):
    world.css_click(button_css)
    text = world.browser.driver.execute_script(
        """
        var editor = tinyMCE.activeEditor;
        return editor.getContent({format: 'raw', no_events: 1});
        """
    )
    assert_in(before, text)
    change_text(after)


@step('I see a "(saving|deleting)" notification')
def i_see_a_mini_notification(_step, _type):
    saving_css = '.wrapper-notification-mini'
    assert world.is_css_present(saving_css)
