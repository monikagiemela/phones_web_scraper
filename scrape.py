import sys
from urllib.parse import urlparse
from Scrappie import Scrappie


def main():    
    scrappie = Scrappie()
    scrappie.base_url = sys.argv[1]
    scrappie.match_phone_numbers(scrappie.base_url)
    result = scrappie.assess_phone_numbers_dict()
    if result:
        print(result)
        return result
    scrappie.crawled_urls.append(scrappie.base_url)
    scrappie.urls.append(scrappie.base_url)
    domain = urlparse(scrappie.base_url).netloc
    scrappie.get_landing_page()    
    scrappie.match_phone_numbers(scrappie.landing_page_url)
    result = scrappie.assess_phone_numbers_dict()
    if result:
        print(result)
        return result
    scrappie.crawled_urls.append(scrappie.landing_page_url)
    scrappie.urls.append(scrappie.landing_page_url)
    result = scrappie.crawl_urls(domain, scrappie.base_url)
    print(result)
    return result

    
if __name__ =="__main__":
    main()