import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

app = Flask(__name__)

username = "je.guyot"
password = "LePreBar17.19!"

login_url = "https://e-learning.crfpa.pre-barreau.com/accounts/login/"
base_url = "https://e-learning.crfpa.pre-barreau.com"
default_protected_url = "/desk/periods/51/courses/4/detail/"  # URL par défaut au premier chargement

def get_session():
    """Crée une session authentifiée"""
    s = requests.Session()
    r = s.get(login_url)
    soup = BeautifulSoup(r.text, "html.parser")
    csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

    payload = {
        "username": username,
        "password": password,
        "csrfmiddlewaretoken": csrf
    }
    headers = {"Referer": login_url}
    s.post(login_url, data=payload, headers=headers)
    return s

def scrape_page(session, url):
    """Récupère le contenu HTML d'une page protégée"""
    r = session.get(url)
    return BeautifulSoup(r.content, "html.parser")

def parse_modules(soup):
    """Récupère la liste des modules et leur href"""
    main_list_course = []
    main_list_href = []
    module_div = soup.find('div', class_="module")
    if module_div:
        for a in module_div.find_all('a'):
            main_list_course.append(a.get_text(strip=True))
            main_list_href.append(a.get('href'))
    return main_list_course, main_list_href

def parse_courses(soup):
    """Récupère les cours et leurs sections"""
    data_dict = {}
    cours_data = soup.find_all('div', class_="course")
    for cours in cours_data:
        titre_tag = cours.find('div', class_="course_title")
        if not titre_tag:
            continue
        titre = titre_tag.get_text(strip=True)
        sections_list = []
        for c in cours.find_all("tr"):
            data_course = {}
            for dt in c.find_all("dt"):
                key = dt.get_text(strip=True)
                dd = dt.find_next_sibling("dd")
                if dd:
                    data_course[key] = dd.get_text(strip=True)
            if data_course:
                sections_list.append(data_course)
        data_dict[titre] = sections_list
    return data_dict

def get_main_title(soup):
    title_tag = soup.find('div', class_="course_main_title")
    return title_tag.get_text(strip=True) if title_tag else "Titre introuvable"

@app.route('/', methods=['GET'])
def index():
    # URL du module à scraper, par défaut la première page
    href = request.args.get('href', default_protected_url)
    protected_url = base_url + href

    # 1️⃣ Session authentifiée
    s = get_session()

    # 2️⃣ Scrape de la page
    soup = scrape_page(s, protected_url)

    # 3️⃣ Modules
    main_list_course, main_list_href = parse_modules(soup)
    modules = list(zip(main_list_course, main_list_href))

    # 4️⃣ Cours
    data_dict = parse_courses(soup)

    # 5️⃣ Titre principal
    main_title = get_main_title(soup)

    return render_template(
        'index.html',
        main_title=main_title,
        modules=modules,
        data=data_dict
    )

if __name__ == '__main__':
    app.run()