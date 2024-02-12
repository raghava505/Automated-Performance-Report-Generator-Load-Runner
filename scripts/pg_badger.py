import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta
import os
import pytz


current_time = datetime.now()
current_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
print("Formatted current time:", current_time)

def get_links(elastic_url,start_time_ist_str, end_time_ist_str):
    url = f"http://{elastic_url}:5602/ondemand"

    resp = requests.get(url, verify=False)
    return_links=[]
    if resp.status_code == 200:
        dbs={"configdb","statedb"}
        for db in dbs :
            start_end_string=f"{current_time}_{start_time_ist_str.replace('T','_')}_to_{end_time_ist_str.replace('T','_')}"
            report_name=f"{start_end_string}_{db}"
            # report_name=f"sprint_{db}"
            print(report_name)
            form_data={
                    "start": start_time_ist_str,
                    "end": end_time_ist_str,
                    "filename": report_name,
                    "database": db
                    }
            response = requests.post(url, data=form_data, verify=False)
            print
            if response.status_code == 200:
                sleep(10)
                report_link=f'http://{elastic_url}:5602/reports/view?file=/data/ondemand_reports/{report_name}/postgres.html'

                print(report_link)   
                return_links[db]=report_link
            else:
                print(f"Error generating report for db {db}: {response.status_code}")
    else:
        print(f"Error accessing the page: {resp.status_code}")
    return return_links


def take_screenshots_and_save(report_links,BASE_PGBADGER_IMAGES_PATH):
    return_res={}
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=9999,9999')
    driver = webdriver.Chrome(options=chrome_options)
    for db,report_link in report_links:
        driver.get(report_link)
        partial_id = "menu"
        elements = driver.find_elements(by=By.XPATH, value=f"//ul[@class='nav navbar-nav']//li[contains(@id, '{partial_id}')]")
        stats_dict = {"Global Stats": "global-stats", "SQL Traffic": "sql-traffic", "Select Traffic": "select-traffic", "Write Traffic": "write-traffic", "Queries duration": "duration-traffic", "Prepared queries ratio": "prepared-queries-ratio", "General Activity": "general-activity", "Established connections": "established-connections", "Connections per database": "connections-per-database", "Connections per user": "connections-per-user", "Connections per host": "connections-per-host", "Simultaneous sessions": "simultaneous-sessions", "Histogram of sessions times": "histogram-session-times", "Sessions per database": "sessions-per-database", "Sessions per user": "sessions-per-user", "Sessions per host": "sessions-per-host", "Sessions per application": "sessions-per-app", "Checkpoints buffers": "checkpoints-buffers", "Checkpoints files": "checkpoints-files", "Checkpoints distance": "checkpoints-distance", "Checkpoint activity": "checkpoint-activity", "Checkpoint causes": "checkpoints-cause", "Size of temporary files": "tempfiles-size", "Number of temporary files": "tempfiles-number", "Temporary files activity": "tempfiles-activity", "Vacuums distribution": "vacuums-count", "Vacuums activity": "vacuums-activity", "Analyzes per Tables": "analyzes-per-table", "Vacuums per Tables": "vacuums-per-table", "Tuples removed": "tuples-removed-per-table", "Page removed": "pages-removed-per-table", "Locks by type": "locks-type", "Most frequent waiting queries (N)": "queries-most-frequent-waiting", "Queries that waited the most": "queries-that-waited-most", "Queries by type": "queries-by-type", "Queries by database": "queries-by-database", "Queries by user": "queries-by-user", "Duration by user": "duration-by-user", "Queries by host": "queries-by-host", "Queries by application": "queries-by-application", "Number of cancelled queries": "queries-cancelled-number", "Histogram of query times": "histogram-query-times", "Slowest individual queries": "slowest-individual-queries", "Time Consuming queries (N)": "time-consuming-queries", "Most frequent queries (N)": "most-frequent-queries", "Normalized slowest queries": "normalized-slowest-queries", "Time consuming prepare": "time-consuming-prepare", "Time consuming bind": "time-consuming-bind", "Log levels": "log-levels", "Events distribution": "minutes-errors-levels", "Most frequent errors/events (keys)": "most-frequent-errors-events"}
        for element in elements:
            try:
                ul_element = WebDriverWait(element, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//ul[@class='dropdown-menu'][li/a[@href]]"))
                )
                element.click()

                dropdown_options = ul_element.find_elements(By.TAG_NAME, 'li')
                option_texts = [option.text for option in dropdown_options if option.text != ""]
                
                for option_text in option_texts:
                    print("Extracting details for : " , option_text)
                    option = ul_element.find_element(By.XPATH, f"./li[a[text()='{option_text}']]")
                    try:
                        option.click()
                    except:
                        print("this block is interactive")
                    sleep(2)

                    if option_text in stats_dict:
                        id = stats_dict[option_text]
                        try:
                            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id)))
                            # Additional strategies for headless mode
                            driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            actions = ActionChains(driver)
                            actions.move_to_element(element).click().perform()
                        except Exception as e:
                            print(f"Error clicking element: {e}")
                            element = driver.find_element_by_id(id)
                        sleep(20)
                        screenshot_path = f'{BASE_PGBADGER_IMAGES_PATH}/{id}_{db}.png'
                        return_res[id]={}
                        # print(f"Saving '{option_text}' details to path {screenshot_path}")
                        element.screenshot(screenshot_path)
                    else:
                        print("not found", option_text)

            except TimeoutException:
                print("Dropdown menu not found within the specified time.")
        driver.quit()

    return return_res

def return_pgbadger_results(start_time_utc,end_time_utc,elastic_url,images_path):
    format_data = "%Y-%m-%dT%H:%M"

    start_time = start_time_utc - timedelta(minutes=10)
    start_time = start_time.strftime(format_data)
    end_time = end_time_utc + timedelta(minutes=10) + timedelta(hours=1)
    end_time = end_time.strftime(format_data)

    print("Converted start time UTC string is : " , start_time)
    print("Converted end time UTC string is : " , end_time)
    links=get_links(elastic_url , start_time, end_time)
    res=take_screenshots_and_save(links,images_path)
    return res

   

if __name__=="__main__":
    start_time_ist_str="2024-02-11 14:00"
    end_time_ist_str="2024-02-12 00:00"
    elastic_url="192.168.129.52"

    BASE_PGBADGER_IMAGES_PATH = os.path.join("/Users/masabathulararao/Documents/Loadtest",'pgbadger_im')
    os.makedirs(BASE_PGBADGER_IMAGES_PATH,exist_ok=True)

    ist_timezone = pytz.timezone('Asia/Kolkata')
    utc_timezone = pytz.utc

    format_data = "%Y-%m-%d %H:%M"
    start_ist_time = ist_timezone.localize(datetime.strptime(start_time_ist_str, format_data))
    end_ist_time = ist_timezone.localize(datetime.strptime(end_time_ist_str, format_data))

    start_utc_time = start_ist_time.astimezone(utc_timezone)
    end_utc_time = end_ist_time.astimezone(utc_timezone)

    res = return_pgbadger_results(start_utc_time,end_utc_time,elastic_url,BASE_PGBADGER_IMAGES_PATH)
    print(res)
   