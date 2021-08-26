import aiohttp
import asyncio
import itertools
import networkx as nx
import os
import pickle
import re
import requests
from bs4 import BeautifulSoup
from math import inf


DISTANCE_STEP = 0.5
HEADERS = {'Accept-Language': 'en', 'X-FORWARDED-FOR': '2.21.184.0'}


def get_correct_url(url):
    if 'www' not in url:
        link = re.search(r'(imdb.+/(?:nm|tt)\d+/)', url)[0]
        url = f'https://www.{link}'
    else:
        url = re.search(r'(.+/(?:nm|tt)\d+/)', url)[0]
    return url


def set_is_full_movie_is_realised(movie_soup):
    return not re.search(re.compile(r'(>[\s{0, 1}]\([A-Za-z\s]+\))'),
                         str(movie_soup)) \
        and not re.search(re.compile(r'(\(<.+>\))'),
                          str(movie_soup))


def get_actor_name_by_url(actor_url):
    response = requests.get(actor_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'lxml')
    name = soup.find('span', attrs={'class': 'itemprop'}).text
    return name


def create_graph_checkpoint(graph):
    nx.write_gml(graph, 'graph.gml')


def create_visited_nodes_checkpoint(visited):
    with open('visited.dump', 'wb') as f:
        pickle.dump(visited, f)


def create_labels_checkpoint(labels):
    with open('labels.dump', 'wb') as f:
        pickle.dump(labels, f)


def create_visited_pairs_checkpoint(visited_pairs):
    with open('visited_pairs.dump', 'wb') as f:
        pickle.dump(visited_pairs, f)


def read_graph_from_checkpoint():
    return nx.read_gml('graph.gml')


def read_visited_nodes_from_checkpoint():
    with open('visited.dump', 'rb') as f:
        visited = pickle.load(f)
        return visited


def read_labels_from_checkpoint():
    with open('labels.dump', 'rb') as f:
        labels = pickle.load(f)
        return labels


def read_visited_pairs_from_checkpoint():
    with open('visited_pairs.dump', 'rb') as f:
        visited_pairs = pickle.load(f)
        return visited_pairs


semaphore = asyncio.Semaphore(10)


async def get_response(url):
    async with semaphore:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(url, headers=HEADERS)as response:
                response_html = await response.text()
                return response_html


def get_soup(response):
    return BeautifulSoup(response, 'lxml')


async def get_pages_for_description(urls):
    tasks = []
    for url in urls:
        tasks.append(get_response(url))
    pages = await asyncio.gather(*tasks)
    return list(zip(urls, pages))


async def get_all_pages(urls):
    tasks = []
    for url in urls:
        if 'title' in url:
            url = f'{url}fullcredits'
        tasks.append(get_response(url))
    pages = await asyncio.gather(*tasks)
    return list(zip(urls, pages))


def get_graph(actor_start_url,
              actor_end_url,
              get_actors_by_movie_soup,
              get_movies_by_actor_soup,
              num_of_actors_limit,
              num_of_movies_limit,
              num_of_depth_level_limit):
    if os.path.exists('graph.gml'):
        G_all_actors = read_graph_from_checkpoint()
        visited = read_visited_nodes_from_checkpoint()
        labels = read_labels_from_checkpoint()
    else:
        G_all_actors = nx.Graph()
        labels = dict()
        visited = dict()
    level = [actor_start_url]
    depth_level_counter = 0
    while depth_level_counter != num_of_depth_level_limit:
        next_level_total = set()
        not_visited = []
        for url in level:
            if url in visited:
                next_level = visited[url]
                next_level_total.update(next_level)
            else:
                not_visited.append(url)
        if not_visited:
            if 'title' in not_visited[0]:
                limit = num_of_actors_limit
                is_actor = 0
            else:
                limit = num_of_movies_limit
                is_actor = 1
            loop = asyncio.get_event_loop()
            urls_zip_pages = loop.run_until_complete(
                get_all_pages(not_visited)
            )
            for el in urls_zip_pages:
                soup = get_soup(el[1])
                if is_actor:
                    urls_with_names = get_movies_by_actor_soup(soup, limit)
                else:
                    urls_with_names = get_actors_by_movie_soup(soup, limit)
                next_level = set(map(lambda x: x[1], urls_with_names))
                labels.update(map(lambda x: (x[1], x[0]), urls_with_names))
                visited[el[0]] = next_level
                if el[0] not in G_all_actors.nodes():
                    G_all_actors.add_node(el[0])
                G_all_actors.add_nodes_from(next_level)
                G_all_actors.add_edges_from(itertools.product([el[0]],
                                                              next_level))
                create_graph_checkpoint(G_all_actors)
                create_labels_checkpoint(labels)
                create_visited_nodes_checkpoint(visited)
                next_level_total.update(next_level)
        if actor_end_url in next_level_total:
            break
        level = list(next_level_total)
        depth_level_counter += DISTANCE_STEP


def get_results_csv(urls):
    G_all_actors = read_graph_from_checkpoint()
    labels = read_labels_from_checkpoint()
    pairs = itertools.combinations(urls, 2)
    with open('distances_from_full_graph.csv', 'w', encoding='utf-8') as file:
        file.write('url_from,url_to,distance,path\n')
        for pair in pairs:
            url_from = get_correct_url(pair[0])
            url_to = get_correct_url(pair[1])
            url_from_name = labels[url_from]
            url_to_name = labels[url_to]
            if nx.has_path(G_all_actors, url_from, url_to):
                distance = int(nx.shortest_path_length(G_all_actors,
                                                       url_from, url_to)
                               * DISTANCE_STEP)
            else:
                distance = inf

            path = ' -> '.join(list(map(lambda x: labels[x],
                                        nx.shortest_path(G_all_actors,
                                                         url_from,
                                                         url_to))))

            string = f'{url_from_name},{url_to_name},{distance},{path}\n'
            file.write(string)
