# -*- coding: utf-8 -*-

"""
	Plugin for streaming video content from www.sdarot.co.in
"""
import urllib, urllib2, re, os, sys, base64
import xbmcaddon, xbmc, xbmcplugin, xbmcgui
import HTMLParser
import json
import cookielib
import unicodedata

##General vars		
__plugin__ = "Sdarot.TV Video"
__author__ = "Cubicle"
__image_path__ = ''
__settings__ = xbmcaddon.Addon(id='plugin.video.sdarot.tv')
__language__ = __settings__.getLocalizedString
addonName = __settings__.getAddonInfo("name")
addonIcon = __settings__.getAddonInfo('icon')
__PLUGIN_PATH__ = __settings__.getAddonInfo('path')
LIB_PATH = xbmc.translatePath( os.path.join( __PLUGIN_PATH__, 'resources', 'lib' ) )
sys.path.append (LIB_PATH)
fanart = xbmc.translatePath(os.path.join( __PLUGIN_PATH__,"fanart.jpg"))


dbg = False # used for simple downloader logging

DOMAIN=base64.b64decode('aHR0cHM6Ly93d3cuc2Rhcm90LmxpdmU=')
#DOMAIN = __settings__.getSetting("domain")

#print "Sdarot Domain=" + DOMAIN

from sdarotcommon import *

path = xbmc.translatePath(__settings__.getAddonInfo("profile"))
cookie_path = os.path.join(path, 'sdarot-cookiejar.txt')
#print("Loading cookies from :" + repr(cookie_path))
cookiejar = cookielib.LWPCookieJar(cookie_path)

if os.path.exists(cookie_path):
	try:
		cookiejar.load()
	except:
		pass
elif not os.path.exists(path):
	os.makedirs(path) 
	
cookie_handler = urllib2.HTTPCookieProcessor(cookiejar)
opener = urllib2.build_opener(cookie_handler)
urllib2.install_opener(opener)
#print "built opener:" + str(opener)


def MAIN_MENU():
	CHECK_LOGIN()
	addDir('[COLOR blue]Clean chache - ניקוי מטמון[/COLOR]',"clean",7,fanart, isFolder=False)
	addDir('[COLOR red]Search - חפש[/COLOR]',DOMAIN+"/search",6,fanart)
	addDir("הכל א-ת","all-heb",2,fanart,'no');
	addDir("הכל a-z","all-eng",2,fanart,'no');
	page = getData(DOMAIN+'/series',referer=DOMAIN)
	matches = re.compile('text="בחירת ז\'אנר">(.*?)</select>', re.S).findall(page)
	matches = re.compile('<option value="(.*?)" >(.*?)</option>').findall(matches[0])
	for match in matches:
		 addDir(str(match[1]),"all-heb",2,fanart,str(match[0]))
	
def SearchSdarot(url,search_entered):
	search_entered= ''
	keyboard = xbmc.Keyboard("", "חפש כאן")
	keyboard.doModal()
	if keyboard.isConfirmed():
		search_entered = keyboard.getText()
	page = getData(url=url,timeout=0,postData="term=" + search_entered)
	
	matches = re.compile('href="/watch/(\d+)-(.*?)">').findall(page)

	#needs to remove duplicted result (originaly in site
	matches = [matches[i] for i,x in enumerate(matches) if x not in matches[i+1:]]
	#print matches
	for match in matches:
		series_id = match[0]
		link_name = match[1]
		image_link = DOMAIN+"/media/series/"+str(match[0])+".jpg"
		series_link = DOMAIN+"/watch/"+str(match[0])+"/"+match[1]
		if link_name.find('episode') == -1:
			addDir(link_name,series_link,"3&image="+urllib.quote(image_link)+"&series_id="+series_id+"&series_name="+urllib.quote(link_name),image_link)
		
def INDEX_AZ(url,page):
	if page == 'no':
		page = DOMAIN + '/ajax/series?loadMore=9999&start=1&search%5Bfrom%5D=&search%5Bto%5D=&search%5Border%5D=&search%5Bdir%5D='
	else:
		page = DOMAIN + '/ajax/series?loadMore=9999&start=1&search%5Bgenre%5D%5B%5D={0}&search%5Bfrom%5D=&search%5Bto%5D=&search%5Border%5D=&search%5Bdir%5D='.format(page)
	page = getData(page)
	matches = re.compile('<img.*?src="(.*?)".*?<h4>(.*?)</h4>.*?<h5>(.*?)</h5>.*?href="(.*?)"', re.S).findall(page)
	sr_arr = []
	for match in matches:
	  heb_name = HTMLParser.HTMLParser().unescape(match[1].decode("utf-8")).strip()
	  eng_name = HTMLParser.HTMLParser().unescape(match[2].decode("utf-8")).strip()
	  if url == "all-eng":
		sr_arr.append(( match[0], match[3], eng_name ))
	  else:
		sr_arr.append(( match[0], match[3], heb_name ))
	sr_sorted = sorted(sr_arr,key=lambda sr_arr: sr_arr[2])
	  
	for key in sr_sorted:
	  series_link = DOMAIN + str(key[1])
	  image_link = 'https:' + str(key[0])
	  series_id = image_link[image_link.rfind('/')+1:image_link.rfind('.')]
	  addDir(key[2],series_link,"3&image="+urllib.quote(image_link)+"&series_id="+series_id+"&series_name="+urllib.quote(key[2].encode("utf-8")),image_link)
	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	  
def sdarot_series(url):
	series_id=urllib.unquote_plus(params["series_id"])
	series_name=urllib.unquote_plus(params["series_name"])
	image_link=urllib.unquote_plus(params["image"])
	try:
		page = getData(url,referer=DOMAIN+'/series')
	except urllib2.URLError, e:
		print 'sdarot_season: got http error ' +str(e.code) + ' fetching ' + url + "\n"
		raise e
	matches = re.compile('תקציר הסדרה.*?<p>(.*?)</p>', re.S).findall(page)
	summary = matches[0] if len(matches) == 1 else ""
		
	seasons_list = re.compile('id="season">(.*?)</ul>',re.S).findall(page)[0]
	matches = re.compile('>(\d+)</a').findall(seasons_list)
			
	for season in matches:
		addDir("עונה "+ str(season),url,"5&image="+urllib.quote(image_link)+"&season_id="+str(season)+"&series_id="+str(series_id)+"&series_name="+urllib.quote(series_name),image_link,summary=summary)
	#xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	xbmc.executebuiltin('Container.SetViewMode(504)')
	  
def sdarot_season(url, summary):
	series_id=urllib.unquote_plus(params["series_id"])
	series_name=urllib.unquote_plus(params["series_name"])
	season_id=urllib.unquote_plus(params["season_id"])
	image_link=urllib.unquote_plus(params["image"])
	page = getData(url=DOMAIN+"/ajax/watch?episodeList="+series_id+"&season="+season_id,timeout=0,referer=url);
	episodes = re.compile('<li data-episode="(.*?)"').findall(page)
	if episodes is None or (len(episodes)==0):
		xbmcgui.Dialog().ok('Error occurred',"לא נמצאו פרקים לעונה")
		return
	
	for epis in episodes:
		addVideoLink("פרק "+epis, url, "4&episode_id="+epis+"&image="+urllib.quote(image_link)+"&season_id="+str(season_id)+"&series_id="+str(series_id)+"&series_name="+urllib.quote(series_name),image_link, summary)		 
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	xbmc.executebuiltin('Container.SetViewMode(504)')
		
def sdarot_movie(url, summary, m_quality=None):
	referer=url
	series_id=urllib.unquote_plus(params["series_id"])
	series_name=urllib.unquote_plus(params["series_name"])
	season_id=urllib.unquote_plus(params["season_id"])
	image_link=urllib.unquote_plus(params["image"])
	episode_id=urllib.unquote_plus(params["episode_id"])
	title = series_name + ", עונה " + season_id + ", פרק " + episode_id
	i = url.rfind('/')
	url = '{0}-{1}/season/{2}/episode/{3}'.format(url[:i], urllib.quote(url[i+1:]), season_id, episode_id)
	finalUrl, VID = getFinalVideoUrl(series_id, season_id, episode_id, url, m_quality=m_quality)
	page = getData(url=DOMAIN+"/ajax/watch",timeout=1,postData="count="+VID,referer=referer)
	liz = xbmcgui.ListItem(path=finalUrl)
	liz.setInfo(type="Video", infoLabels={ "Title": title, "Plot": urllib.unquote(summary) })	
	liz.setProperty('IsPlayable', 'true')
	xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz)
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=finalUrl, listitem=liz, isFolder=False)

def choose_quality(url, summary):
	series_id=urllib.unquote_plus(params["series_id"])
	series_name=urllib.unquote_plus(params["series_name"])
	season_id=urllib.unquote_plus(params["season_id"])
	image_link=urllib.unquote_plus(params["image"])
	episode_id=urllib.unquote_plus(params["episode_id"])
	title = series_name + ", עונה " + season_id + ", פרק " + episode_id
	qualities = getFinalVideoUrl(series_id, season_id, episode_id, url, m_quality='choose')
	for q in qualities:
		addVideoLink(title+" ("+ str(q) +")",url,"4&episode_id="+episode_id+"&image="+urllib.quote(image_link)+"&season_id="+str(season_id)+"&series_id="+str(series_id)+"&series_name="+urllib.quote(series_name)+"&quality="+str(q),image_link,summary,contextMenu=False)
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	xbmc.executebuiltin('Container.SetViewMode(504)')

def clean_cache():
	try:
		if os.path.isfile(cookie_path):
			os.unlink(cookie_path)
	except Exception as ex:
		xbmc.log(str(ex), 3)
	tempDir = xbmc.translatePath('special://temp/').decode("utf-8")
	for the_file in os.listdir(tempDir):
		if not '.fi' in the_file and the_file != 'cookies.dat':
			continue
		file_path = os.path.join(tempDir, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as ex:
			xbmc.log(str(ex), 3)
	
params = getParams(sys.argv[2])
#print "params:"
#print params
url=None
name=None
mode=None
module=None
page=None
summary=None
quality=None

try:
	url=urllib.unquote_plus(params["url"])
except:
	pass
try:
	name=urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode=int(params["mode"])
except:
	pass
try:
	module=urllib.unquote_plus(params["module"])
except:
	pass
try:
	page=urllib.unquote_plus(params["page"])
except:
	pass
try:
	summary=urllib.unquote_plus(params["summary"])
except:
	pass
try:
	quality=int(params["quality"])
except:
	pass

if mode==None or url==None or len(url)<1:
	MAIN_MENU()

elif mode==2:
	INDEX_AZ(url,module)
elif mode==3:
	sdarot_series(url)
elif mode==4:
	sdarot_movie(url, summary, quality)
elif mode==5:
	sdarot_season(url, summary)
elif mode==6:
	SearchSdarot(url,name)
elif mode==7:
	clean_cache()
	xbmc.executebuiltin("XBMC.Notification({0}, המטמון נמחק, {1}, {2})".format(addonName, 5000 ,addonIcon))
elif mode==8:
	choose_quality(url, summary)

xbmcplugin.setPluginFanart(int(sys.argv[1]),xbmc.translatePath( os.path.join( __PLUGIN_PATH__,"fanart.jpg") ))
xbmcplugin.endOfDirectory(int(sys.argv[1]))