import urllib, urllib2, base64

# Const
VERSION  = '2.0.1'
ART      = 'art-default.png'
ICON     = 'icon-default.png'
PREFIX   = '/video/oz-eon'
HOST     = 'core.oz.com'
WAYPOINT = 'https://'+HOST+'/'
AGENT    = 'OZ2.bundle '+VERSION+' (Plex Media Server)'


####################################################################################################
def Start():

  Log('Starting OZ v%s', VERSION)
  ObjectContainer.title1 = 'OZ Eon'

  if 'access_token' not in Dict:
    Authenticate()


####################################################################################################
def Request(Path):
  url = WAYPOINT + Path
  request = {}
  headers = {}
  headers['User-Agent'] = AGENT
  headers["Authorization"] = "Bearer " + Dict['access_token']
  body = urllib2.urlopen(urllib2.Request(url, None, headers)).read()
  response = JSON.ObjectFromString(body)

  return response


####################################################################################################
@handler(PREFIX, 'OZ Eon', art=ART, thumb=ICON)
def MainMenu():

  oc = ObjectContainer()

  oc.add(DirectoryObject(key = Callback(DiscoverMenu),                 title = L('Discover')))
  oc.add(DirectoryObject(key = Callback(ChannelMenu),                  title = L('Channels')))
  oc.add(InputDirectoryObject(key = Callback(Search, title = L('Search')), prompt = L('Search'), title = L('Search')))

  return oc


####################################################################################################
@handler(PREFIX + '/discover')
def DiscoverMenu():

  oc = ObjectContainer(title2 = L('Discover'))

  if len(oc) < 1:
    return NoContentFound(oc, title)

  return oc


####################################################################################################
@route(PREFIX + '/channels')
def ChannelMenu():

  oc = ObjectContainer(title2 = L('Channels'))

  channels = Request('users/me/channels')

  if len(oc) < 1:
    return NoContentFound(oc, title)

  return oc


####################################################################################################
@route(PREFIX + '/collections', channel = object)
def ChannelMenu():

  oc = ObjectContainer(title2 = L(channel['title']))


  return oc

####################################################################################################
@route(PREFIX + '/search')
def Search(query = ''):

  oc = ObjectContainer(title2 = L('Search results'))

  if len(oc) < 1:
    return NoContentFound(oc, title)

  return oc

####################################################################################################
def NoContentFound(oc, title):
  oc.header  = title
  oc.message = L('No content found')
  return oc