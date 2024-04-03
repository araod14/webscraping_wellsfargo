from playwright.sync_api import sync_playwright
from lxml import html as html
import requests
import pandas as pd
import datetime
import time

def extract_links():
    """
    This function extracts the links to the Wells Fargo private foundations from the search results page.
    Returns:
        A pandas dataframe containing the name, link, area of interest, state served, and other limitation of the foundations.
    """
    url = "https://www.wellsfargo.com/private-foundations/search-results/#searchtab"
    result = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.click('input[name="findByProgramArea"]')
        time.sleep(2)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        content = page.content()
        parsed = html.fromstring(content)
        links = parsed.xpath('//td[@scope="row"]/a')

        for i in range(len(links)):
            name = parsed.xpath(f'/html/body/div[1]/div[3]/div/div[1]/table/tbody/tr[{i+2}]/td[1]/a')[0]
            link = parsed.xpath(f'/html/body/div[1]/div[3]/div/div[1]/table/tbody/tr[{i+2}]/td[1]/a')[0]
            area = parsed.xpath(f'/html/body/div[1]/div[3]/div/div[1]/table/tbody/tr[{i+2}]/td[2]')[0]
            state_served = parsed.xpath(f'/html/body/div[1]/div[3]/div/div[1]/table/tbody/tr[{i+2}]/td[3]')[0]
            other_limitation = parsed.xpath(f'/html/body/div[1]/div[3]/div/div[1]/table/tbody/tr[{i+2}]/td[4]')[0]

            result.append({
                    "Name": name.text_content(),
                    "Link": link.get("href"),
                    "Area": area.text_content().strip().replace('\n','').replace('\t','').replace('  ',''),
                    "State Served": state_served.text_content().strip().replace('\n','').replace('\t',''),
                    "Other Limitation": other_limitation.text_content().strip().replace('\n','').replace('\t','')
                })

        df = pd.DataFrame(result)
        df['Link'] = 'https://www.wellsfargo.com' + df['Link']
        browser.close()
    return df

def extract_page_details(df):
    """
    This function extracts the details from the Wells Fargo private foundations webpages.
    Args:
        df (pandas.DataFrame): A dataframe containing the links to the foundation webpages.
    Returns:
        A pandas dataframe containing the foundation details.
    Raises:
        Exception: If there is an error while processing a url.
    """
    result = []
    urls_list = df['Link'].tolist()

    client = requests.Session()
    for url in urls_list:
        try:
            resp = client.get(url)
            page = resp.text
            parsed = html.fromstring(page)
            overview = parsed.xpath('//*[@id="overview"]')
            overview_list = [x for x in overview]
            grand_guideleines = parsed.xpath('//*[@id="grantguidelines"]')
            grand_guideleines_list = [x for x in grand_guideleines]
            foundation_info = parsed.xpath('//*[@id="foundationinformation"]')
            foundation_info_list = [x for x in foundation_info]
            result_dict = {}
            try:
                result_dict["Overview"] = overview_list[0].text_content().strip().replace('\n','').replace('\t','').replace('\r','')
            except:
                result_dict["Overview"] = ""
            try:
                result_dict["Grant Guidelines"] = grand_guideleines_list[0].text_content().strip().replace('\n','').replace('\t','').replace('\r','')
            except:
                result_dict["Grant Guidelines"] = ""
            try:
                result_dict["Foundation Information"] = foundation_info_list[0].text_content().strip().replace('\n','').replace('\t','').replace('\r','')
            except:
                result_dict["Foundation Information"] = ""
            result.append(result_dict)
        except Exception as e:
            print(f"Error processing url: {url}")
            print(e)
    df = pd.DataFrame(result)
    
    return df

if __name__ == "__main__":
    current_date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print("Extracting links...")
    df_links = extract_links()
    size = df_links.shape[0]
    print(f"Links extracted: {size}")
    print("Extracting details...")
    df_details = extract_page_details(df_links)
    print("Details extracted")
    df_total = pd.concat([df_links,df_details], axis=1)
    df_total.to_csv(f'wellsfargo.com-private-foundations{current_date_time}.csv', index=False)
    print("csv is ready")