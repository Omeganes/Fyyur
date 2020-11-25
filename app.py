#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from operator import add
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
# from flask_wtf import FlaskForm
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    shows = db.relationship('Show', backref='Venue', lazy=True)
    

    def __init__(self, name, city, state, address, phone, genres, facebook_link):
        self.name = name
        self.city = city
        self.state = state
        self.address = address
        self.phone = phone
        self.genres = genres
        self.facebook_link = facebook_link
        


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='Artist', lazy=True)

    def __init__(self, name, city, state, phone, genres, facebook_link):
        self.name = name
        self.city = city
        self.state = state
        self.phone = phone
        self.genres = genres
        self.facebook_link = facebook_link


class Show(db.Model):
    __tablename__ = 'Show'
    
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, artist_id, venue_id, start_time):
        self.artist_id = artist_id
        self.venue_id = venue_id
        self.start_time = start_time

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
      return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = []
    venues = Venue.query.all()
    cities = []
    for venue in venues:
        if venue.city not in cities:
            cities.append(venue.city)
            areas.append(
                {
                    "city": venue.city,
                    "state": venue.state,
                    "venues": []
                }
            )
    for venue in venues:
        for area in areas:
            if venue.city == area['city'] and venue.state == area['state']:
                area['venues'].append(
                    {
                        "id": venue.id,
                        "name": venue.name,
                        "num_upcoming_shows": len(venue.shows),
                    }
                )
                break
    return render_template('pages/venues.html', areas=areas);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    venues = Venue.query.filter(func.lower(Venue.name).like('%' + func.lower(request.form['search_term']) + '%')).order_by(Venue.name).all()
    response={
        "count": len(venues),
        "data": []
    }
    for venue in venues:
        response['data'].append(
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(venue.shows)
            }
        )
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    data = {}
    error = False
    found = False
    try:
        venue = Venue.query.get(venue_id)
        if venue:
            found = True
            data = {
                "id": venue.id,
                "name": venue.name,
                "genres": venue.genres[1:-1].split(','),
                "address": venue.address,
                "city": venue.city,
                "state": venue.state,
                "phone": venue.phone,
                "website": venue.website,
                "facebook_link": venue.facebook_link,
                "seeking_talent": venue.seeking_talent,
                "image_link": venue.image_link,
                "past_shows": [],
                "upcoming_shows": [],
                "past_shows_count": 0,
                "upcoming_shows_count": 0,
            }
            for show in venue.shows:
                if show.start_time > datetime.today():
                    data['upcoming_shows_count'] +=1
                    data['upcoming_shows'].append(
                        {
                            "artist_id": show.Artist.id,
                            "artist_name": show.Artist.name,
                            "artist_image_link": show.Artist.image_link,
                            "start_time": str(show.start_time)
                        }
                    )
                else:
                    data['past_shows_count'] +=1
                    data['past_shows'].append(
                        {
                            "artist_id": show.Artist.id,
                            "artist_name": show.Artist.name,
                            "artist_image_link": show.Artist.image_link,
                            "start_time": str(show.start_time)
                        }
                    )
    except:
        error = True
        print(sys.exc_info())
    if error:
        abort(400)
    elif not found:
        flash('Oops.. Not Found')
        return redirect(redirect_url())
    
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    venue_form = VenueForm(request.form)
    error = False
    if (venue_form.validate_on_submit()):
        try:
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            address = request.form['address']
            phone = request.form['phone']
            genres = request.form.getlist('genres')
            facebook_link = request.form['facebook_link']
            venue = Venue(
                name, city, state, address, phone, genres, facebook_link
            )
            db.session.add(venue)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
            print(sys.exc_info())
        finally:
            db.session.close()
    else:
        error = True
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    flash('Venue deleted!')
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    error = False
    try:
        artists = Artist.query.all()
        for artist in artists:
            data.append(
                {
                    "id": artist.id,
                    "name": artist.name
                }
            )
    except:
        error = True
        print(sys.exc_info())
    if error:
        abort(400)
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    artists = Artist.query.filter(func.lower(Artist.name).like('%' + func.lower(request.form['search_term']) + '%')).order_by(Artist.name).all()
    response={
        "count": len(artists),
        "data": []
    }
    for artist in artists:
        response['data'].append(
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": len(artist.shows)
            }
        )
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = {}
    error = False
    found = False
    try:
        artist = Artist.query.get(artist_id)
        if artist:
            found = True
            data = {
                "id": artist.id,
                "name": artist.name,
                "genres": artist.genres[1:-1].split(','),
                "city": artist.city,
                "state": artist.state,
                "phone": artist.phone,
                "website": artist.website,
                "facebook_link": artist.facebook_link,
                "seeking_venue": artist.seeking_venue,
                "seeking_description": artist.seeking_description,
                "image_link": artist.image_link,
                "past_shows": [],
                "upcoming_shows": [],
                "past_shows_count": 0,
                "upcoming_shows_count": 0,
            }
            for show in artist.shows:
                if show.start_time > datetime.today():
                    data['upcoming_shows_count'] +=1
                    data['upcoming_shows'].append(
                        {
                            "venue_id": show.Venue.id,
                            "venue_name": show.Venue.name,
                            "venue_image_link": show.Venue.image_link,
                            "start_time": str(show.start_time)
                        }
                    )
                else:
                    data['past_shows_count'] +=1
                    data['past_shows'].append(
                        {
                            "venue_id": show.Venue.id,
                            "venue_name": show.Venue.name,
                            "venue_image_link": show.Venue.image_link,
                            "start_time": str(show.start_time)
                        }
                    )
    except:
        error = True
        print(sys.exc_info())
    if error:
        abort(400)
    elif not found:
        flash('Oops.. Not Found')
        return redirect(redirect_url())
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if artist:
        data = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres[1:-1].split(','),
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link
        }
        return render_template('forms/edit_artist.html', form=form, artist=data)
    else:
        flash('Oops.. Not Found')
        return redirect(redirect_url())
        

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist_form = ArtistForm(request.form)
    error = False
    if (artist_form.validate_on_submit()):
        try:
            artist = Artist.query.get(artist_id)
            artist.name = request.form['name']
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            artist.genres = request.form.getlist('genres')
            artist.facebook_link = request.form['facebook_link']
            print(artist.name)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
    else:
        redirect(url_for('edit_artist', artist_id=artist_id))
    if error:
        flash('An error occured. Artist'+ request.form['name'] +' could not be edited')
    else:
        flash('Artist '+ request.form['name'] + ' was successfully edited!')
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if venue:
        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres[1:-1].split(','),
            "city": venue.city,
            "state": venue.state,
            "address": venue.address,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "image_link": venue.image_link
        }
        return render_template('forms/edit_venue.html', form=form, venue=data)
    else:
        flash('Oops.. Not Found')
        return redirect(redirect_url())

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue_form = VenueForm(request.form)
    error = False
    if (venue_form.validate_on_submit()):
        try:
            venue = Venue.query.get(venue_id)
            venue.name = request.form['name']
            venue.city = request.form['city']
            venue.state = request.form['state']
            venue.address = request.form['address']
            venue.phone = request.form['phone']
            venue.genres = request.form.getlist('genres')
            venue.facebook_link = request.form['facebook_link']
            db.session.commit()
        except:
            db.session.rollback()
            error = True
        finally:
            db.session.close()
    else:
        return redirect(url_for('edit_venue', venue_id=venue_id))
    if error:
        flash('An error occured. Venue '+ request.form['name'] +' could not be edited')
    else:
        flash('Artist '+ request.form['name'] + ' was successfully edited!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    artist_form = ArtistForm(request.form)
    error = False
    if (artist_form.validate_on_submit()):
        try:
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            phone = request.form['phone']
            genres = request.form.getlist('genres')
            facebook_link = request.form['facebook_link']
            artist =Artist(
                name, city, state, phone, genres, facebook_link
            )
            db.session.add(artist)
            db.session.commit()
        except:
            db.session.rollback()
            error = True
            print(sys.exc_info())
        finally:
            db.session.close()
    else:
        error = True
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data=[{
        "venue_id": 1,
        "venue_name": "The Musical Hop",
        "artist_id": 4,
        "artist_name": "Guns N Petals",
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": "2019-05-21T21:30:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 5,
        "artist_name": "Matt Quevedo",
        "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
        "start_time": "2019-06-15T23:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-01T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-08T20:00:00.000Z"
    }, {
        "venue_id": 3,
        "venue_name": "Park Square Live Music & Coffee",
        "artist_id": 6,
        "artist_name": "The Wild Sax Band",
        "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
        "start_time": "2035-04-15T20:00:00.000Z"
    }]
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
