import asyncio
import itertools
import networkx as nx
import os
import re
from math import inf
from imdb_helper_functions import create_visited_pairs_checkpoint,\
    get_all_pages, get_correct_url, get_graph, get_results_csv,\
    get_soup, get_pages_for_description, read_graph_from_checkpoint,\
    read_labels_from_checkpoint, read_visited_pairs_from_checkpoint,\
    set_is_full_movie_is_realised


MAX_DEPTH_SEARCH = 3
ACTORS_SEARCH_LIMIT = 5
MOVIES_SEARCH_LIMIT = 5
DISTANCE_STEP = 0.5
HEADERS = {'Accept-Language': 'en', 'X-FORWARDED-FOR': '2.21.184.0'}


def get_actors_by_movie_soup(
        cast_page_soup,
        num_of_actors_limit=None
):
    all_actors = cast_page_soup.find_all(
        'td',
        attrs={'class': 'primary_photo'},
        limit=num_of_actors_limit
    )
    actors_list = []
    for actor in all_actors:
        link = actor.find('a')['href']
        actors_list.append(
            (actor.find('img')['title'],
             f'https://www.imdb.com{link}'))
    return actors_list


def get_movies_by_actor_soup(
        actor_page_soup,
        num_of_movies_limit=None
):
    all_movies = actor_page_soup.find_all(
        'div',
        attrs={'id': re.compile(r'(act(or|ress)-tt\d+)')}
    )
    movie_list = []
    for movie in all_movies:
        if set_is_full_movie_is_realised(movie):
            link = movie.find('a')['href']
            movie_list.append(
                (movie.b.text,
                 f'https://www.imdb.com{link}')
            )
        if num_of_movies_limit and len(movie_list) == num_of_movies_limit:
            break
    return movie_list


def get_movie_distance(actor_start_url,
                       actor_end_url,
                       num_of_actors_limit=None,
                       num_of_movies_limit=None,
                       num_of_depth_level_limit=None):
    actor_start_url = get_correct_url(actor_start_url)
    actor_end_url = get_correct_url(actor_end_url)

    if os.path.exists('visited_pairs.dump'):
        visited_pairs = read_visited_pairs_from_checkpoint()
        if (actor_start_url, actor_end_url) in visited_pairs:
            G_all_actors = read_graph_from_checkpoint()
            if actor_start_url in G_all_actors.nodes() and \
                    actor_end_url in G_all_actors.nodes() and \
                    nx.has_path(G_all_actors, actor_start_url, actor_end_url):
                return int(nx.shortest_path_length(G_all_actors,
                                                   actor_start_url,
                                                   actor_end_url)
                           * DISTANCE_STEP)
            return inf

    get_graph(actor_start_url,
              actor_end_url,
              get_actors_by_movie_soup,
              get_movies_by_actor_soup,
              num_of_actors_limit,
              num_of_movies_limit,
              num_of_depth_level_limit)

    G_all_actors = read_graph_from_checkpoint()
    if os.path.exists('visited_pairs.dump'):
        visited_pairs = read_visited_pairs_from_checkpoint()
    else:
        visited_pairs = []
    visited_pairs.append((actor_start_url, actor_end_url))
    create_visited_pairs_checkpoint(visited_pairs)

    if actor_start_url in G_all_actors.nodes() and\
            actor_end_url in G_all_actors.nodes() and\
            nx.has_path(G_all_actors, actor_start_url, actor_end_url):
        return int(nx.shortest_path_length(G_all_actors,
                                           actor_start_url,
                                           actor_end_url) * DISTANCE_STEP)

    return inf


def get_movie_descriptions_by_actor_soup(actor_page_soup):
    descriptions = []
    movies = get_movies_by_actor_soup(actor_page_soup)
    movies_urls = list(map(lambda x: x[1], movies))
    loop = asyncio.get_event_loop()
    movies_html = loop.run_until_complete(
        get_pages_for_description(movies_urls)
    )
    for movie in movies_html:
        soup = get_soup(movie[1])
        description = soup.find(
            'div',
            attrs={'class': 'ipc-html-content ipc-html-content--base'}
        )
        if description:
            descriptions.append(description.text)
    return descriptions


def main(urls,
         num_of_actors_limit=None,
         num_of_movies_limit=None,
         num_of_depth_level_limit=None):
    all_pairs = itertools.permutations(urls, 2)
    for pair in all_pairs:
        distance = get_movie_distance(pair[0],
                                      pair[1],
                                      num_of_actors_limit,
                                      num_of_movies_limit,
                                      num_of_depth_level_limit)
        print(f'from: {pair[0]}, '
              f'to: {pair[1]}, '
              f'distance = {distance}')

    get_results_csv(urls)

    labels = read_labels_from_checkpoint()

    loop = asyncio.get_event_loop()
    urls_actors_pages = loop.run_until_complete(get_all_pages(urls))
    for actor in urls_actors_pages:
        actor_name = labels[actor[0]]
        soup = get_soup(actor[1])
        descriptions = get_movie_descriptions_by_actor_soup(soup)
        with open(f'{actor_name}.txt', 'w', encoding='utf-8') as file:
            for el in descriptions:
                file.write(f'{el}\n')


if __name__ == "__main__":
    urls = ['https://www.imdb.com/name/nm0425005/',
            'https://www.imdb.com/name/nm1165110/',
            'https://www.imdb.com/name/nm0000375/',
            'https://www.imdb.com/name/nm0474774/',
            'https://www.imdb.com/name/nm0000329/',
            'https://www.imdb.com/name/nm0177896/',
            'https://www.imdb.com/name/nm0001191/',
            'https://www.imdb.com/name/nm0424060/',
            'https://www.imdb.com/name/nm0005527/',
            'https://www.imdb.com/name/nm0262635/']

    main(urls, ACTORS_SEARCH_LIMIT, MOVIES_SEARCH_LIMIT, MAX_DEPTH_SEARCH)
