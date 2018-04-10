from flask import Flask, render_template
from flask_caching import Cache
from get_movie import list_of_films


app = Flask(__name__)
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'static/cache/'
})


@app.route('/')
@cache.cached(timeout=60)
def films_list():
    films = list_of_films()
    return render_template('films_list.html', films=films)


if __name__ == "__main__":
    app.run()
