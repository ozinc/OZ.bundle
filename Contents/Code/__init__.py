import urllib, urllib2, base64

# Const
NAME     = 'OZ2.bundle'
VERSION  = '2.0.1'
ART      = 'art-default.jpg'
ICON     = 'icon-default.png'
PREFIX   = '/video/oz2'
HOST     = 'core.oz.com'
WAYPOINT = 'https://'+HOST+'/'
AGENT    = NAME+' '+VERSION+' (Plex Media Server)'
SECRET   = 'An7qRnAAaz270enMn'


####################################################################################################
def Start():

  Log('Starting OZ v%s', VERSION)
  ObjectContainer.title1 = 'OZ'

  if 'access_token' not in Dict:
    Authenticate()


####################################################################################################
def Authenticate():
  url = WAYPOINT + 'oauth2/token'
  request = {}
  headers = {}
  headers['User-Agent'] = AGENT
  headers['Content-Type'] = 'application/x-www-form-urlencoded'
  data = {}
  data['username'] = Prefs['username']
  data['password'] = Prefs['password']
  data['client_id'] = 'Plex'
  data['client_secret'] = SECRET
  data['grant_type'] = 'password'
  body = urllib2.urlopen(urllib2.Request(url, urllib.urlencode(data), headers)).read()
  response = JSON.ObjectFromString(body)

  Dict['access_token'] = response['access_token']


####################################################################################################
def Request(Path, Token = None):
  if not Token:
    Token = Dict['access_token']
  url = WAYPOINT + Path
  request = {}
  headers = {}
  headers['User-Agent'] = AGENT
  headers["Authorization"] = "Bearer " + Token
  body = urllib2.urlopen(urllib2.Request(url, None, headers)).read()
  response = JSON.ObjectFromString(body)

  return response


####################################################################################################
@handler(PREFIX, 'OZ', art=ART, thumb=ICON)
def MainMenu():

  oc = ObjectContainer(title2 = L('Channels'))


  channels = Request('channels?status=listed&items=100&order=name', '1a9ea68a8b8c4d7eb409e3982a3399742da10503')

  for channel in channels['data']:
    logo = channel['iconUrl']
    color = channel['brandColor'][1:]
    brandedLogo = logo.replace('/upload', '/upload/w_256,h_256,c_pad,g_center,b_rgb:' + color + ',bo_10px_solid_rgb:' + color)
    brandedLogo = brandedLogo.replace('.png', '.jpg')
    item = DirectoryObject(
      key = Callback(ChannelMenu, channelName = channel['name'], channelId = channel['id']),
      title = channel['name'],
      thumb = brandedLogo
    )
    oc.add(item)

  if len(oc) < 1:
    return NoContentFound(oc, title)

  oc.add(InputDirectoryObject(key = Callback(SearchChannels, title = L('Search channels')), prompt = L('Search channels'), title = L('Search channels'), thumb = R('icon-search.png')))

  return oc


####################################################################################################
@route(PREFIX + '/channels', channelName = str, channelId = str)
def ChannelMenu(channelName, channelId):

  oc = ObjectContainer(title2 = channelName)

  oc.add(DirectoryObject(key = Callback(VideosMenu, channelName = channelName, channelId = channelId), title = L('Videos'), thumb = R('icon-videos.png')))
  oc.add(DirectoryObject(key = Callback(CollectionsMenu, channelName = channelName, channelId = channelId), title = L('Collections'), thumb = R('icon-collections.png')))
  oc.add(DirectoryObject(key = Callback(MomentsMenu, channelName = channelName, channelId = channelId), title = L('Moments'), thumb = R('icon-moments.png')))

  return oc


####################################################################################################
@route(PREFIX + '/videos', channelName = str, channelId = str)
def VideosMenu(channelName, channelId, page = 0, collection = None, collectionName = '', selected = None):

  title = '%s Videos' % channelName

  if collection:
    title = '%s in %s' % (title, collectionName)

  oc = ObjectContainer(title2 = title)

  videosUrl = 'channels/%s/videos?items=50&page=%s' % (channelId, page)

  if collection:
    videosUrl = '%s&collectionId=%s' % (videosUrl, collection)

  videos = Request(videosUrl)

  for video in videos['data']:

    title = video['title']
    description = 'No description available for this content'
    if 'description' in video['metadata']:
      description = video['metadata']['description']

    item = VideoClipObject(
      key = Callback(VideosMenu, channelName = channelName, channelId = channelId, page = page, collection = collection, collectionName = collectionName, selected = video['id']),
      rating_key = video['id'],
      title = title,
      summary = description,
      thumb = video['_links']['stillUrl'],
      duration = int(video['duration'] * 1000),
      items = [
        MediaObject(
          parts = [PartObject(key=HTTPLiveStreamURL(Callback(PlayStream, channelId = channelId, videoId = video['id'])))]
        )
      ]
    )

    if selected == None or selected == video['id']:
      oc.add(item)

  if len(oc) == 50:
    oc.add(NextPageObject(key = Callback(VideosMenu, channelName = channelName, channelId = channelId, page = int(page) + 1, collection = collection, collectionName = collectionName), title = L('More...')))

  return oc


####################################################################################################
@route(PREFIX + '/collections', channelName = str, channelId = str)
def CollectionsMenu(channelName, channelId, page = 0, selected = None):

  oc = ObjectContainer(title2 = '%s Collections' % channelName)

  collections = Request('channels/%s/collections?items=50&page=%s' % (channelId, page))

  for collection in collections['data']:

    item = DirectoryObject(
      key = Callback(VideosMenu, channelName = channelName, channelId = channelId, page = page, collection = collection['id'], collectionName = collection['name']),
      title = collection['name'],
      summary = collection['description'],
      thumb = collection['posterUrl']
    )

    oc.add(item)

  if len(oc) == 50:
    oc.add(NextPageObject(key = Callback(CollectionsMenu, channelName = channelName, channelId = channelId, page = int(page) + 1), title = L('More...')))

  return oc


####################################################################################################
@route(PREFIX + '/moments', channelName = str, channelId = str)
def MomentsMenu(channelName, channelId, page = 0, selected = None):

  oc = ObjectContainer(title2 = '%s Moments' % channelName)

  moments = Request('channels/%s/moments?items=50&page=%s' % (channelId, page))

  for moment in moments['data']:

    item = VideoClipObject(
      key = Callback(MomentsMenu, channelName = channelName, channelId = channelId, page = page, selected = moment['id']),
      rating_key = moment['id'],
      title = '%s @%s' % (moment['caption'], moment['user']['username']),
      thumb = moment['previewImageUrlLandscape'],
      items = [
        MediaObject(
          parts = [PartObject(key=HTTPLiveStreamURL(moment['videoFileUrlLandscape']))]
        )
      ]
    )

    if selected == None or selected == moment['id']:
      oc.add(item)

  if len(oc) == 50:
    oc.add(NextPageObject(key = Callback(MomentsMenu, channelName = channelName, channelId = channelId, page = int(page) + 1), title = L('More...')))

  return oc

####################################################################################################
@route(PREFIX + '/search-channels')
def SearchChannels(title, query = ''):

  oc = ObjectContainer(title2 = 'Search Results')

  channels =  Request('channels?order=name&items=100&search=%s' % query)

  for channel in channels['data']:
    logo = channel['iconUrl']
    color = channel['brandColor'][1:]
    brandedLogo = logo.replace('/upload', '/upload/w_256,h_256,c_pad,g_center,b_rgb:' + color + ',bo_10px_solid_rgb:' + color)
    brandedLogo = brandedLogo.replace('.png', '.jpg')
    item = DirectoryObject(
      key = Callback(ChannelMenu, channelName = channel['name'], channelId = channel['id']),
      title = channel['name'],
      thumb = brandedLogo
    )
    oc.add(item)

  if len(oc) < 1:
    return NoContentFound(oc, title)

  return oc


####################################################################################################
@route(PREFIX + '/playStream.m3u8', channelId = str, videoId = str)
def PlayStream(channelId, videoId):
  streamUrl = 'channels/%s/videos/%s/streamUrl' % (channelId, videoId)
  response = Request(streamUrl)
  return Redirect(response['data']['url'])


####################################################################################################
def NoContentFound(oc, title):
  oc.header  = title
  oc.message = L('No content found')
  return oc