import re, urllib, datetime
import xbmc
from resources.lib import text
from resources.lib import meta_info
from resources.lib import play_base
from resources.lib import meta_players

def play_movie(tmdb_id):
	from resources.lib.TheMovieDB import Movies
	play_plugin = meta_players.ADDON_SELECTOR.id
	players = meta_players.get_players('movies')
	players = [p for p in players if p.id == play_plugin] or players
	if not players or len(players) == 0:
		xbmc.executebuiltin('Action(Info)')
		play_base.action_cancel()
		return
	movie = Movies(tmdb_id).info(language='en', append_to_response='external_ids,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating')
	movie_info = meta_info.get_movie_metadata(movie)
	trakt_ids = play_base.get_trakt_ids('tmdb', tmdb_id, movie['original_title'], 'movie', text.parse_year(movie['release_date']))
	params = {}
	for lang in meta_players.get_needed_langs(players):
		if lang == 'en':
			tmdb_data = movie
		else:
			tmdb_data = Movies(tmdb_id).info(language=lang, append_to_response='external_ids,alternative_titles,credits,images,keywords,releases,videos,translations,similar,reviews,lists,rating')
		params[lang] = get_movie_parameters(tmdb_data)
		if trakt_ids != None:
			params[lang].update(trakt_ids)
		params[lang]['info'] = movie_info
		params[lang] = text.to_unicode(params[lang])
	link = play_base.on_play_video(players, params, trakt_ids)
	if link:
		movie = Movies(tmdb_id).info(language='en')
		play_base.action_play(
			{
				'label': movie_info['title'],
				'path': link,
				'info': movie_info,
				'is_playable': True,
				'info_type': 'video',
				'thumbnail': movie_info['poster'],
				'poster': movie_info['poster'],
				'properties': {'fanart_image': movie_info['fanart']}
			})

def get_movie_parameters(movie):
	parameters = {}
	parameters['date'] = movie['release_date']
	parameters['premiered'] = movie['release_date']
	parameters['year'] = text.parse_year(movie['release_date'])
	parameters['released'] = movie['release_date']
	parameters['id'] = movie['id']
	parameters['imdb'] = movie['imdb_id']
	parameters['title'] = movie['title'].replace('&', '%26')
	parameters['striptitle'] = ' '.join(re.compile('[\W_]+').sub(' ', movie['title']).split())
	parameters['urltitle'] = urllib.quote(text.to_utf8(parameters['title']))
	parameters['sorttitle'] = text.to_utf8(parameters['title'])
	articles = ['a ', 'A ', 'An ', 'an ', 'The ', 'the ']
	for article in articles:
		if text.to_utf8(parameters['title']).startswith(article):
			parameters['sorttitle'] = text.to_utf8(parameters['title']).replace(article,'')
	parameters['shorttitle'] = text.to_utf8(parameters['title'][1:-1])
	if 'movie' in str(parameters['sorttitle']).lower():
		parameters['sortesttitle'] = str(parameters['sorttitle']).lower().replace(' movie', '')
	elif 'movi' in str(parameters['sorttitle']).lower():
		parameters['sortesttitle'] = str(parameters['sorttitle']).lower().replace(' movi', '')
	else:
		parameters['sortesttitle'] = parameters['sorttitle']
	parameters['original_title'] = movie['original_title'].replace('&', '%26')
	parameters['name'] = u'%s (%s)' % (parameters['title'], parameters['year'])
	parameters['urlname'] = urllib.quote(text.to_utf8(parameters['name']))
	parameters['released'] = movie['release_date']
	parameters['rating'] = movie['vote_average']
	studios = [x['name'] for x in movie['production_companies'] if not x == '']
	parameters['studios'] = ' / '.join(studios)
	genre = [x['name'] for x in movie['genres'] if not x == '']
	parameters['genres'] = ' / '.join(genre)
	if movie['runtime'] and movie['runtime'] != '' and movie['runtime'] != None:
		parameters['runtime'] = movie['runtime']
	else:
		parameters['runtime'] = '0'
	if movie['vote_count'] and movie['vote_count'] != '' and movie['vote_count'] != None and movie['vote_count'] != 0:
		parameters['votes'] = movie['vote_count']
	else:
		parameters['votes'] = '0'
	if movie['vote_average'] and movie['vote_average'] != '' and movie['vote_average'] != None and movie['vote_average'] != 0:
		parameters['rating'] = movie['vote_average']
	else:
		parameters['rating'] = '0'
	if movie['credits']['crew']:
		prewriters = [i['name'] for i in movie['credits']['crew'] if i['department'] == 'Writing']
		writers = []
		for item in prewriters:
			if item not in writers:
				writers.append(item)
		parameters['writers'] = ', '.join(writers)
	else:
		parameters['writers'] = ''
	if movie['credits']['crew']:
		predirectors = [i['name'] for i in movie['credits']['crew'] if i['department'] == 'Directing']
		directors = []
		for item in predirectors:
			if item not in directors:
				directors.append(item)
		parameters['directors'] = ', '.join(directors)
	else:
		parameters['directors'] = ''
	if movie['credits']['cast']:
		preactors = [i['name'] for i in movie['credits']['cast']]
		actors = []
		for item in preactors:
			if item not in actors:
				actors.append(item)
		parameters['actors'] = actors
	else:
		parameters['actors'] = ''
	if movie['releases']['countries'][0]['certification']:
		parameters['mpaa'] = movie['releases']['countries'][0]['certification']
	else:
		parameters['mpaa'] = ''
	parameters['duration'] = int(parameters['runtime']) * 60
	parameters['plot'] = movie['overview'].replace(':','').replace(';', '').replace('"', '')
	parameters['tagline'] = movie['tagline'].replace(':','').replace(';', '').replace('"', '')
	if 'https://image.tmdb.org/t/p/w300%s' % str(movie['poster_path']):
		parameters['poster'] = 'https://image.tmdb.org/t/p/w300%s' % str(movie['poster_path'])
	else:
		parameters['poster'] = 'https://image.tmdb.org/t/p/original%s' % str(movie['poster_path'])
	if 'https://image.tmdb.org/t/p/w1280%s' % str(movie['backdrop_path']):
		parameters['fanart'] = 'https://image.tmdb.org/t/p/w1280%s' % str(movie['backdrop_path'])
	else:
		parameters['fanart'] = 'https://image.tmdb.org/t/p/original%s' % str(movie['backdrop_path'])
	parameters['now'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
	trakt_ids = play_base.get_trakt_ids('tmdb', movie['id'], parameters['title'], 'movie', parameters['year'])
	if 'slug' in trakt_ids:
		if trakt_ids['slug'] != '' and trakt_ids['slug'] != None:
			parameters['slug'] = trakt_ids['slug']
		else:
			parameters['slug'] = parameters['title'].lower().replace('~','').replace('#','').replace('%','').replace('&','').replace('*','').replace('{','').replace('}','').replace('\\','').replace(':','').replace('<','').replace('>','').replace('?','').replace('/','').replace('+','').replace('|','').replace('"','').replace(' ','-').replace('--','-')
	return parameters