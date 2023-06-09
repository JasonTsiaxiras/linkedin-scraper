from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains

def navigate_login(url,driver):
    driver.get(url)
    folder = driver.find_element_by_xpath("//*[@id='artdeco-global-alert-container']/div/section/div/div[2]/button[1]")
    folder.click()
    folder2 = driver.find_element_by_xpath("/html/body/nav/div/a[2]")
    folder2.click()

    f = open("logindetails.txt", "r")
    lines = f.readlines()
    f.close()
    username = lines[0].strip()
    password = lines[1]

    element_user = driver.find_element_by_id('username')
    element_user.send_keys(username)
    element_password = driver.find_element_by_id('password')
    element_password.send_keys(password)
    element_aanmelden = driver.find_element_by_xpath("//*[@id='organic-div']/form/div[3]/button")
    element_aanmelden.click()

    return driver

def enter_keyword(keyword, driver):
    job_search = driver.find_element_by_xpath("//*[starts-with(@id, 'jobs-search-box-keyword-id-')]")
    job_search.send_keys(keyword+"\n")
    return driver

def click_on_24_hours(driver):
    element = driver.find_element_by_class_name("search-reusables__filter-list")
    doc = BeautifulSoup(element.get_attribute('innerHTML'), 'html.parser')
    ember_id = doc.find("div", {"id": "hoverable-outlet-plaatsingsdatum-filter-value"}).parent.get('id')
    driver.find_element_by_id(ember_id).click()
    a = ActionChains(driver)
    m = driver.find_element_by_id("timePostedRange-r86400")
    a.move_to_element(m).click(m).perform()
    driver.find_element_by_id(ember_id).click()

    return driver

def scroll_load_job_cards(driver):

    scrollable_element = driver.find_element_by_class_name("jobs-search-results-list")
    scroll_length = scrollable_element.size['height']/2

    for i in range(0,15):
        driver.execute_script("arguments[0].scroll(0,"+str(i*scroll_length)+");", scrollable_element)
        time.sleep(0.5)
    return driver

def get_li_tags(driver):
    html__ = driver.find_element_by_class_name("jobs-search-results-list").get_attribute('innerHTML')
    doc__ = BeautifulSoup(html__, 'html.parser')
    li_tags = doc__.find_all('li',attrs={'class': lambda e: e.startswith('artdeco-pagination__indicator') if e else False})
    return li_tags

def page_numbers(li_tags):
    current_page = [x for x in li_tags if "active selected ember-view" in str(x)][0]
    current_page_number = str(current_page).split('data-test-pagination-page-btn="')[1].split('" id=')[0]
    next_page_number = str(int(current_page_number)+1)
    last_page_number = str(li_tags[-1]).split('data-test-pagination-page-btn="')[1].split('" id=')[0]

    return current_page_number, next_page_number, last_page_number

# def page_ember(li_tags, page_num):
#     string_tag = str([x for x in li_tags if f'data-test-pagination-page-btn="{page_num}"' in str(x)][0])
#     ember = string_tag.split('id="')[1].split('">')[0]
#     return ember

def page_ember(li_tags, page_num):
    string_tag = str([x for x in li_tags if f'aria-label="Pagina {page_num}"' in str(x)][0])
    ember = string_tag.split('id="')[1].split('">')[0]
    return ember

def get_ids_on_page(driver):
    html_ = driver.page_source
    doc = BeautifulSoup(html_,"html.parser")
    html_class = 'disabled ember-view job-card-container__link job-card-list__title'
    tags = doc.find_all("a", {"class" : html_class})
    job_ids = [x['href'].split('/')[3] for x in tags]
    return job_ids

def save_id_data(search_keyword,scrape_date,job_ids):
    search_keywords = [search_keyword] * len(job_ids)
    scrape_dates = [scrape_date] * len(job_ids)
    df = pd.DataFrame(data={'job_id':job_ids,'search_keyword':search_keywords,'id_scrape_date':scrape_dates})

    with open(f'{scrape_date}', 'a+') as f:
        df.to_csv(f, header=True, index=False)
        f.close()

    return

#Below are functions for the retrieve job data script

def load_ids(date='2023-05-03'):
    df = pd.read_csv(date)
    return df

def navigate_job(job_id,driver):
    """driver should be logged in and cookie accepted"""
    
    url = f"https://www.linkedin.com/jobs/view/{job_id}"
    driver.get(url)
    return driver

def get_job_description_html_text(driver):
    description_element = driver.find_element_by_id("job-details")
    description_html = description_element.get_attribute('innerHTML')
    
    doc = BeautifulSoup(description_html,"html.parser")
    description_text = doc.get_text(separator=' ')
    
    return description_html, description_text

def get_primary_card(driver):
    primary_element = driver.find_element_by_class_name("jobs-unified-top-card__primary-description")
    primary_html = primary_element.get_attribute('innerHTML')
    doc = BeautifulSoup(primary_html,"html.parser")
    primary = doc.get_text(separator='')
    return primary

def clean_primary(primary):
    primary_data = [x.lstrip() for x in primary.split('\n') if ((len(x) > 0) & (~x.isspace()))]
    return primary_data

def get_secondary_card(driver):
    els = driver.find_elements_by_class_name('jobs-unified-top-card__job-insight')
    sec = [BeautifulSoup(el.get_attribute('innerHTML'), 'html.parser').text.replace('\n','') for el in els]
    return sec

def get_skills(driver):
    a = ActionChains(driver)
    m = driver.find_element_by_class_name('jobs-unified-top-card__job-insight-text-button')
    a.move_to_element(m).click(m).perform()

    elem_skills = driver.find_element_by_class_name('job-details-skill-match-status-list')
    html_skills = elem_skills.get_attribute('innerHTML')
    doc_skills = BeautifulSoup(html_skills, 'html.parser')
    text_skills = doc_skills.text
    skills_list = [x.lstrip() for x in text_skills.split('\n') if (((len(x) > 0) & (~x.isspace())) & (x.lstrip() != 'Toevoegen'))]
    
    return skills_list