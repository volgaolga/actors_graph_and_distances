#Project discription
---
    In this project, I collect, process, analyze and present data from
    imdb.com.
    Have you heard of the theory of six degrees of separation?
    The idea is simple: I introduce a special measure of the distance between
    the actors. How is it measured? If two actors played in the same film,
    the distance between them is 1. If two actors have never played in the same
    movie, but there is an actor who played in some movie with each of the
    actors, then the distance between the actors is 2. And so Further.

---

    There are three functions implemented in imdb_code.py:
    1) get_actors_by_movie_soup (cast_page_soup, num_of_actors_limit):
        retrns the list of movies the current actor has played. This function
        takes a beautifulsoup (cast_page_soup) page soup object for the cast
        and crew of the current movie. The function returns a list of all
        the actors who played in the movie. An actor defined by this pair:
        (name_of_actor, url_to_actor_page). So, the output of the function is 
        a list of such pairs. The function can take an optional argument
        num_of_actors, if the argument is 10, then the function will return
        the first 10 actors listed on the cast page, and nothing more.
        If the argument is None, the function will return all participants.
    2) get_movies_by_actor_soup (actor_page_soup, num_of_movies_limit):
        returns the list of actors who played in the current movie.
        This function takes a beautifulsoup soup (worker_page_soup) page object
        for the current actor. The function returns a list of all films in
        which the actor has played. A movie defined by this pair:
        (name_of_movie, url_to_movie_page). The result of the function is a
        list of such pairs. The function takes an optional num_of_movies_limit
        argument. If the argument is 10, then the function will return the last
        10 movies the actor played in, and no more. If the argument is None,
        then the function will return all movies. The function only returns
        movies that have already been released and all movies are full feature
        movies.
    3) get_movie_distance (actor_start_course, actor_end_course,
    num_of_actors_limit = None, num_of_movies_limit = None):
      This function has two required arguments: act_start_url, actor_end_url -
      url-addresses to imdb-pages of actors, between which the distance between
      movies is measured. This function returns an integer - the distance
      between the specified actors. The function can also receive the optional
      arguments num_of_actors and num_of_movies.
    
    I calculated the pairing distances for the highest paid actors of 2019:
    Dwayne Johnson, Chris Hemsworth, Robert Downey Jr., Akshay Kumar,
    Jackie Chan, Bradley Cooper, Adam Sandler, Scarlett Johansson,
    Sofia Vergara, Chris Evans.
    All data is collected asynchronously and saved to a file
    'distances_from_full_graph.csv'.

---
    The file 'imdb_helper_functions.py' contains helper functions for
    'imdb_code.py'.
    Dumb files contain saved information about already visited films and
    actors, which allows us to take information from there, and not from the
    imdb.com.
    The file 'graph.gml' contains a graph in which the nodes are actors and
    movies, edges are the connectivity between them.
    The file 'data_scraping_final_project.ipynb' contains the final report on
    the distances between the specified actors and wordclouds, consisting of
    the most common words in the descriptions of the films for each actor.
    The txt files with the names of the actors in the title contain
    the descriptions of the movies for each actor (to make wordclouds).
