import os
import re
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import bs4
import datetime
current_time_stamp = datetime.datetime.now()
date_stamp = current_time_stamp.strftime("%Y%m%d")
csv_output_file = os.path.join("property_listings.csv")
tmp_data = "tmp_data"
os.makedirs("tmp_data", exist_ok=True)

"""
https://www.upwork.com/jobs/~014e9dede738fbd3e7

Please create a script to retrieve all the data from a site such as this utilizing python.

https://crystalplazaapartments.securecafe.com/onlineleasing/crystal-plaza-apartments/availableunits.aspx?myOlePropertyId=1236440
https://crystaltowersapartments.securecafe.com/onlineleasing/crystal-towers-apartments/availableunits.aspx?myOlePropertyId=1236433
https://buchananapts.securecafe.com/onlineleasing/the-buchanan-apartments/availableunits.aspx?myOlePropertyId=1236438

Script should not receive a 403 error and be able to return the following fields:

- Floor Plan
- Apartment #
- Bed Count
- Bath Count
- Area (size)
- Price
- Date Available

The deliverable is a script; not the results of the script.
"""


def parse_content(apts_name, html_data):
    """ Parse the html content """
    soup_page = bs4.BeautifulSoup(html_data, features="html.parser")
    div_section = soup_page.find_all(id="OuterDiv")
    div_section_text = str(div_section)

    div_section_text = div_section_text.replace("\t", "")
    div_section_text = div_section_text.replace("</div>", "</div> ###### ")
    div_section_text = div_section_text.replace("<th ", "\n<th ")
    div_section_text = div_section_text.replace("<td ", "\n<td ")

    floor_plans = 0
    bed_rooms = ""
    bath_rooms = ""
    apt_number = ""
    sq_feet = ""
    rent_cost = ""
    content_string = ""
    for html_line in div_section_text.split("\n"):
        html_line = html_line.rstrip()
        if "<h3><span>Floor Plan</span>" in html_line:
            floor_plans += 1
            fp_info = html_line.split("Apartment Details and Selection for Floor Plan: ")
            fp = cleanhtml(fp_info[1])

            beds_bath = fp.split(" - ")[1]
            bed_rooms = beds_bath.split(", ")[0].replace("Bedrooms", "").replace("Bedroom", "").strip()
            bath_rooms = beds_bath.split(", ")[1].replace("Bathrooms", "").replace("Bathroom", "").strip()
            sq_feet = fp.split(" SF ")[0].split(" ")[-1].replace(",", "").strip()
        elif '<th class=' not in html_line:

            if 'data-label="Apartment"' in html_line:
                apt_number = html_line.split("</td>")[0].split(">")[1]
            elif 'data-label="Rent"' in html_line:
                rent_cost = html_line.split("</td>")[0].split(">")[1].replace(",", "")
            elif 'data-label="Date Available"' in html_line:
                date_available = html_line.replace("</span></td>", "").split(">")[2]

                new_str = (date_stamp + "," +
                           apts_name + "," +
                           sq_feet + "," +
                           bed_rooms + "," +
                           bath_rooms + "," +
                           apt_number + "," +
                           rent_cost + "," +
                           date_available)
                content_string += new_str + "\n"
                apt_number = ""
                rent_cost = ""

    return content_string


def download_then_parse(__urls):
    new_data = ""
    driver = False
    for url in __urls:
        page_name = url.split("?myOlePropertyId=")[1]
        apt_site = url.split("/")[4].replace("-apartments", "")

        content_file = date_stamp + "_" + apt_site + "_" + page_name + ".html"
        html_tmp = os.path.join(tmp_data, content_file)
        if not os.path.exists(html_tmp):
            options = FirefoxOptions()
            options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)
            print("Getting:".ljust(30), content_file)
            driver.get(url)
            WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, "OuterDiv")))
            html_source = driver.page_source
            with open(html_tmp, "w", encoding="utf-8") as h_out:
                h_out.write(html_source)
        else:
            print("Exists:".ljust(30), content_file)
            with open(html_tmp, "r", encoding="utf-8") as h_in:
                html_source = h_in.read()

        if len(html_source) > 1:
            csv_data = parse_content(apt_site, html_source)
            new_data += csv_data

    if driver:
        driver.quit()
    return new_data


def cleanhtml(raw_html):
    clean_html_regex = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    clean_text = re.sub(clean_html_regex, '', raw_html)
    return clean_text


def generate_report(new_csv_data):
    header = "00Date,Apts,SqFt.,BedRooms,BathRooms,AptNumbers,Rent,Available"

    if os.path.exists(csv_output_file):
        file_mode = "a"
    else:
        file_mode = "w"

    with open(csv_output_file, file_mode, encoding="utf-8") as csv_file:
        if file_mode == "w":
            csv_file.write(header + "\n")

        for line in new_csv_data.split("\n"):
            line = line.rstrip()
            if line:
                csv_file.write(line + "\n")

    tmp_list = []
    with open(csv_output_file, "r", encoding="utf-8") as csv_file:
        data = csv_file.readlines()
    for item in data:
        item = item.rstrip()
        if item not in tmp_list:
            tmp_list.append(item)

    n_tmp = sorted(set(tmp_list))
    x = 0
    with open(csv_output_file, "w", encoding="utf-8") as csv_file:
        for item in n_tmp:
            x += 1
            csv_file.write(item + "\n")
    return x


def main():

    urls = [
        "https://crystalplazaapartments.securecafe.com/onlineleasing/crystal-plaza-apartments/availableunits.aspx?myOlePropertyId=1236440",
        "https://crystaltowersapartments.securecafe.com/onlineleasing/crystal-towers-apartments/availableunits.aspx?myOlePropertyId=1236433",
        "https://buchananapts.securecafe.com/onlineleasing/the-buchanan-apartments/availableunits.aspx?myOlePropertyId=1236438"
    ]
    csv_data = download_then_parse(urls)
    rows = generate_report(csv_data)

    print("csv_output_file:".ljust(30), csv_output_file)
    print("lines_of_data:".ljust(30), rows)


if __name__ == '__main__':
    main()
