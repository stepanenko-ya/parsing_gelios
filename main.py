from bs4 import BeautifulSoup
import requests
from random import choice
from fake_useragent import UserAgent
from proxy import proxy
from configs import conn, db
import html

user = UserAgent()


schema_name = "gelius_UA"


def get_html(url):
    x = True
    while x:
        random_proxy = choice(proxy)
        prox = {"http": "http://" + random_proxy,
                "https": "http://" + random_proxy}
        try:
            req = requests.get(url=url,
                               headers={"User-Agent": user.chrome},
                               proxies=prox,
                               timeout=7)
        except Exception as ex:
            print(f"Retry, {ex}")
        else:
            if req.status_code == 200:
                x = False
                return req.text


def pars_links(content):
    soup = BeautifulSoup(content, "html.parser")
    catalogs = soup.find(id="navBar").find_all('a')
    cat_list = [cat.get('href') for cat in catalogs]
    return cat_list[:-2]


def pars_pagination(first_urls):
    gasket = "page-"
    for first_url in first_urls:
        file_page_result = open("pagination.txt", "a+")
        content = get_html(first_url)
        soup_pagination = BeautifulSoup(content, "html.parser")
        count_pages = soup_pagination.find(class_="pagination").find_all("li")
        if count_pages:
            count_page = count_pages[-1].find('a').get("href")
            last_page = count_page.split("page-")[1]
            for page in range(1, int(last_page) + 1):
                file_page_result.write(first_url+gasket+str(page)+"\n")
        else:
            file_page_result.write(first_url + "\n")
        file_page_result.close()


def items_link():
    page_links = open("pagination.txt").readlines()
    with open("item_links.txt", "a+") as it_links_file:
        for page_link in page_links:
            content_items = get_html(page_link.strip())
            soup_items = BeautifulSoup(content_items, "html.parser")
            items = soup_items.find_all("div", class_="product-item__body pb-xl-2")
            for item in items:
                item_link = item.find('h5').find("a").get("href")
                it_links_file.write(f"{item_link}\n")


def creating():
    db.execute(f"create schema {schema_name}")
    conn.commit()

    db.execute(f"create table {schema_name}.items (TransactionID int IDENTITY (1,1) NOT NULL, vendor_code NVARCHAR(max), "
               f"name NVARCHAR(max), url NVARCHAR(max), category NVARCHAR(max), description NVARCHAR(max))")
    conn.commit()

    db.execute(f"create table {schema_name}.photos (TransactionID int IDENTITY (1,1) NOT NULL,  vendor_code NVARCHAR(max),"
               f" photo NVARCHAR(max))")
    conn.commit()

    db.execute(f"create table {schema_name}.params (TransactionID int IDENTITY (1,1) NOT NULL,  vendor_code NVARCHAR(max),"
               f" param_name NVARCHAR(max),param_value NVARCHAR(max))")
    conn.commit()


def uniq_urls():
    all_items = open('item_links.txt').readlines()
    with open('UNIQ.txt', "w") as uniq_file:
        uniq_items = list(set(all_items))
        uniq_file.write("".join(uniq_items))


def items_pars():
    uniq_urls = open("ukr_urls.txt").readlines()
    for uniq_url in uniq_urls:
        item_html = get_html(uniq_url.strip())
        item_soup = BeautifulSoup(item_html, "html.parser")

        breadcrumb = html.escape(
            item_soup.find(class_="my-md-3").get_text().strip().replace("\n",
                                                                        '-'))

        name = html.escape(item_soup.find(class_="mb-2").find(
            class_="text-lh-1dot2").get_text())

        vendor_code = item_soup.find(class_="mb-2").find(
            "span",
            class_="sku").get_text().split(":")[1].strip()

        description = item_soup.find(id="fullcontent")
        if description:
            descript = html.escape(item_soup.find(id="fullcontent").get_text()
                                   .strip())
        else:
            descript = ""
        db.execute(f"INSERT INTO {schema_name}.items (vendor_code, name, url, category, description)"
                   f" VALUES(N'{vendor_code}', N'{name}',N'{uniq_url.strip()}', N'{breadcrumb}', N'{descript}')")
        conn.commit()

        parameter = item_soup.find("div", id="Jpills-three-example1")
        if parameter:
            params = parameter.find_all("tr")
            for param in params:
                param_name = html.escape(param.find_all("td")[0].get_text())
                param_value = html.escape(param.find_all("td")[1].get_text())

                db.execute(f"INSERT INTO {schema_name}.params (vendor_code, param_name, param_value)"
                           f" VALUES(N'{vendor_code}', N'{param_name}',N'{param_value}')")
                conn.commit()

        photos = item_soup.find_all(class_="img-fluid fixosnova")
        if photos:
            for photo in photos:
                img = photo.get("src")
                db.execute(f"INSERT INTO {schema_name}.photos (vendor_code, photo)"
                           f" VALUES(N'{vendor_code}', N'{img}')")
                conn.commit()


if __name__ == '__main__':
    content = get_html("https://gelius.ua/trends/")
    categories = pars_links(content)
    pars_pagination(categories)
    items_link()
    creating()
    uniq_urls()
    items_pars()



