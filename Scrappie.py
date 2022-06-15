import re
import requests
from bs4 import BeautifulSoup
import phonenumbers
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Scrappie:
    def __init__(self):
        self.urls = []
        self.crawled_urls = []
        self.base_url = ""
        self.landing_page_url = ""
        self.phone_numbers = {}
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    def assess_phone_numbers_dict(self):
        """
        Assess whether phone_numbers contais enough data to infer 
        the main phone number. Create a dictionary with the frequency of the times 
        a given number was found. If there is only one phone number in the dict - 
        it will be checked this number was found more than one time. If there is
        more than one phone number - it will check if there is a phone number
        which has a unique maximum value and will return the phone number that 
        appreared most often on the website, otherwise empty string will be returned.
        
        :return the main phone number found on a website or empty string.
        """
        if len(self.phone_numbers) == 0:
            return ""
        if len(self.phone_numbers) == 1:
            key0 = list(self.phone_numbers.keys())[0]
            if self.phone_numbers[key0] > 1:
                return key0
            else:
                return ""
        if len(self.phone_numbers) > 1:
            all_values = self.phone_numbers.values()
            if len(all_values) == len(set(all_values)):
                return max(self.phone_numbers, key=self.phone_numbers.get)
            else:
                return ""

    def crawl_urls(self, domain, url) -> str:
        """
        Get a list of urls and crawl each URL recursively.

        :param domain: Domain to which param 'url' must belong.
        :param url: URL of a webpage to be crawled.
        :return The most frequent phone number.
        """            
        self.crawled_urls.append(url)
        self.driver.get(url)
        html = self.driver.page_source.encode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        current_page_a_tags = soup.findAll("a")
        for a_tag in current_page_a_tags:
            href = a_tag.get("href")
            href = self.is_url(href)
            if href and href not in self.urls and href not in self.crawled_urls:
                if self.has_keyword(href):
                    self.urls.append(href)
                    self.match_phone_numbers(href)
                    result = self.assess_phone_numbers_dict()
                    if result:
                        return result
                self.crawled_urls.append(url)                            
        self.prioritarize_urls()
        for url in set(self.urls):        
            if (urlparse(url).netloc == domain) and (url not in self.crawled_urls):
                if len(self.crawled_urls) > 100:
                    if self.phone_numbers:
                        result = self.assess_phone_numbers_dict()
                        if result:
                            return result
                        else:
                            return list(self.phone_numbers.keys())[0]                        
                    else:
                        return "Phone number not found" 
                self.crawl_urls(domain, url)
                
    def get_landing_page(self):
        """
        Filter landing page from a base url.

        :return: bool    
        """
        landing_url_regex = "(https?://[A-Za-z_0-9.-]+).*"
        self.landing_page_url = re.search(landing_url_regex, self.base_url).group(1)
    
    def get_soup_text(self, url):
        """
        Get text content of a page.
        
        :param url: URL of a web page whose text is requested.
        :return: Text of a web page.
        """
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException:
            pass
        else:
            return BeautifulSoup(response.text, "html.parser").get_text(separator=";", strip=True)
    
    def is_url(self, href) -> str:
        """
        Check if a URL's format is valid.
        Retrun formated string.
        If URL cannot not be formated into a valid URL, return an empty string.

        :param url: URL string to be validated.
        :param domain: Domain to which param 'url' should belong.
        :return: Formated URL string or an empty string.
        """        
        if href == "" or href is None:
            href = ""
        elif href.endswith((".png", ".jpg", ".css", ".gif", ".pdf", ".ico", ".feed", ".json", ".js", ".svg", ".php")):
            href = ""
        elif href.endswith((".png/", ".jpg/", ".css/", ".gif/", ".pdf/", ".ico/", ".feed/", ".json/", ".js/", ".svg/", ".php/")):
            href = ""
        else:
            href = urljoin(self.landing_page_url, href)
            parsed_href = urlparse(href)
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not href.startswith("http"):
                href = ""
            if not (parsed_href.netloc and parsed_href.scheme):
                href = ""
            bad_words = ("linkedin", "instagram", "twitter", "facebook", "spotify")
            for bad_word in bad_words:
                if bad_word in href:
                    href = ""                       
        return href

    def has_keyword(self, url):
        """
        Check if a URL contains a keyword that suggests that it is probable to
        to find a phone number on this web page.

        :param url: URL to eveluated.
        :return bool
        """ 
        keywords = ("contact", "kontakt", "about", "nas", "company", "address", "adres")
        for keyword in keywords:
            if keyword in url.lower():
                return True
            else:
                continue  
        return False        
    
    def prioritarize_urls(self):
        """
        Sort URLs by in place their length. It is deemed that shorter URLs are 
        of higher priority.
        """
        self.urls.sort(key=lambda url: len(url))
    
    def match_phone_numbers(self, url):
        """
        Find phone numbers in the text of a web page. 
        Using Google Phone Numbers Library: https://pypi.org/project/phonenumbers/ .
        Found phone number is saved to the phone_numbers dictionary.

        :param url: URL of a web page to be parsed.
        """
        soup_text = self.get_soup_text(url)
        for match in phonenumbers.PhoneNumberMatcher(soup_text, None):
            match = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
            if match in self.phone_numbers:
                self.phone_numbers[match] += 1
            else:
                self.phone_numbers[match] = 1