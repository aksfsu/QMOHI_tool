from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import qmohi.src.metric_calc.navigation_metric.constants as constants
import copy

driver = None

# Setting up selenium driver
def set_up_selenium_driver(driver_path):
    global driver

    options = Options()
    # Runs Chrome in headless mode
    options.add_argument(constants.mode)

    # Run web driver with the driver_path provided by user
    driver = webdriver.Chrome(driver_path, chrome_options = options)
    driver.set_page_load_timeout(60)


class Node:

    def __init__(self, url, level, target_urls, trace):
        self.url = url
        self.redirected_url = self.get_redirected_url(self.url)
        trace.append(url)
        self.trace = trace
        self.child_pages = self.get_hyperlinks()
        self.level = level
        # Copy in separate variable as target URLs is gets appended every time
        goal_urls = copy.copy(target_urls)
        self.target_urls = self.get_all_forms_of_target_urls(goal_urls)
        self.hit = self.check_for_target()
        constants.visited_urls.extend(self.child_pages)

    # Get all the hyperlinks on current web page
    def get_hyperlinks(self):
        hyperlinks = []

        try:
            elems = driver.find_elements_by_xpath('//a[@href]')

            for elem in elems:
                next_url = elem.get_attribute("href")
                # Spilt URL wtih # to remove unwanted part
                splitted_url = next_url.rsplit('#', 1)
                next_url = splitted_url[0]

                # 1st condition for checking if root url is a substring of next url
                # 2nd condition for checking if next url is already present in the visited urls or no
                # 3rd condition for checking if url is pdf
                # 4th condition for checking if url is jpg
                # 5th condition for checking if url is png
                if (self.trace[0] in next_url) \
                        and (len(list(set(constants.visited_urls) & {next_url})) == 0) \
                        and not next_url.endswith(".pdf") and not next_url.endswith(".jpg") \
                        and not next_url.endswith(".png"):
                    hyperlinks.append(next_url)

        except Exception as e:
            print("Error in URL redirection!")
            print(e)

        hyperlinks = list(set(hyperlinks))
        return hyperlinks

    def get_redirected_url(self, url):
        # Try getting redirected URL
        try:
            driver.get(url)
            return driver.current_url

        except WebDriverException as e:
            print("Web driver exception in selenium :", e.msg)

        # Tf there is some error in URL redirection
        except Exception as e:
            print("Error in URL redirection!")
            print(e)

        return url

    # To get all forms of target URLs
    def get_all_forms_of_target_urls(self, target_urls):
        redirected_target_urlself = []
        http_https_combination = []
        for url in target_urls:
            redirected_target_urlself.append(self.get_redirected_url(url))

            # To handle mismatch in http and https. Both urls point to the same page.
            if "https://" in url:
                # Check https first as http will show true in both cases
                http_https_combination.append(url.replace("https://", "http://"))
            elif "http://" in url:
                http_https_combination.append(url.replace("http://", "https://"))

        target_urls.extend(redirected_target_urlself)
        target_urls.extend(http_https_combination)
        target_urls = list(set(target_urls))

        return target_urls

    # Check if URL is present in target URLs
    def check_for_target(self):
        for url in self.target_urls:
            if (self.url == url) or (self.redirected_url == url):
                return self.level
        return -1
