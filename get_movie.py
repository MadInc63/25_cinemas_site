from bs4 import BeautifulSoup
from threading import Thread
from werkzeug.contrib.cache import FileSystemCache
import requests


cache = FileSystemCache('static/cache/', threshold=100, default_timeout=24*60*60)


def get_film_info(film):
    title = film.get('film_title')
    film_page = fetch_film_page(title)
    additional_information = parse_film_info(film_page.text)
    film.update(additional_information)


def list_of_films():
    number_of_top_films = 10
    afisha_page_url = 'https://www.afisha.ru/msk/schedule_cinema/'
    afisha_page_raw = fetch_page(afisha_page_url)
    showing_films = parse_afisha_list(afisha_page_raw.text)
    threads_list = []
    for film in showing_films:
        thread = Thread(
            target=get_film_info,
            name='Thread {}'.format(film.get('film_title')),
            args=(film, )
        )
        thread.start()
        threads_list.append(thread)
    for thread in threads_list:
        thread.join()
    sorted_film_list = (sorted(
        showing_films, key=lambda item: item['film_rating'], reverse=True
    ))
    return sorted_film_list[:number_of_top_films]


def fetch_page(url, params=None):
    unique_url = url + str(params)
    if cache.get(unique_url) is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/64.0.3282.140 Safari/537.36',
            'Accept-Language': 'ru,en;q=0.9'
        }
        cache.set(
            unique_url,
            requests.get(url, params=params, headers=headers)
        )
    return cache.get(unique_url)


def parse_afisha_list(raw_html):
    films_information = []
    min_showing_cinemas_count = 30
    soup = BeautifulSoup(raw_html, 'html.parser')
    tags = soup.find_all(class_='m-disp-table')
    for tag in tags:
        film_title = tag.h3.string
        film_url = tag.h3.a.get('href')
        cinemas_count = len(
            tag.next_sibling.next_sibling.find_all(class_='b-td-item')
        )
        if min_showing_cinemas_count < cinemas_count:
            films_information.append(
                {
                    'film_title': film_title,
                    'film_url': film_url,
                    'cinemas_count': cinemas_count
                }
            )
    return films_information


def fetch_film_page(film_title):
    url = 'https://www.kinopoisk.ru/index.php'
    params = {'kp_query': film_title, 'first': 'yes', 'what': ''}
    response = fetch_page(url, params)
    return response


def parse_film_info(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    try:
        film_cover_url = soup.select_one('.popupBigImage').img.get('src')
        film_rating = soup.find(class_='rating_ball').string
        film_rating_count = soup.find(
            class_='ratingCount'
        ).string.replace(u'\xa0', '')
        actors_tag = soup.find('div', id='actorList').find('ul').select('a')
        film_actors = ', '.join(str(element.string) for element in actors_tag[:-1])
        year_tag = soup.find('table', class_='info').select('a[href*=year]')
        film_year = ', '.join(str(element.string) for element in year_tag)
        country_tag = soup.find('table', class_='info').select('a[href*=country]')
        film_country = ', '.join(str(element.string) for element in country_tag)
        genre_tag = soup.find('table', class_='info').select('a[href*=genre]')
        film_genre = ', '.join(str(element.string) for element in genre_tag)
    except AttributeError:
        film_cover_url = None
        film_rating = 0.0
        film_rating_count = 0
        film_actors = None
        film_year = None
        film_country = None
        film_genre = None
    additional_film_information = {
        'film_cover_url': film_cover_url,
        'film_rating': float(film_rating),
        'film_rating_count': int(film_rating_count),
        'film_actors': film_actors,
        'film_year': film_year,
        'film_country': film_country,
        'film_genre': film_genre
    }
    return additional_film_information
