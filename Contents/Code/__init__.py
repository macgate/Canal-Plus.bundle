# -*- coding: utf-8 -*-
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

PLUGIN_PREFIX	= "/video/canalplus"

baseURL = "http://webservice.canal-plus.com/rest/bigplayer/"

def Start():
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, ListeCategories, "Canal Plus", "icon-default.png", "art-default.jpg")
	Plugin.AddViewGroup("infoList", viewMode="InfoList", mediaType="items")
	MediaContainer.title1    = 'Canal Plus'
	MediaContainer.viewGroup = 'infoList'
  	MediaContainer.art       = R("art-default.jpg")
	
def CreatePrefs():
	Prefs.Add(id='qualite', type='enum', default='HD', label='Qualité préférée (si disponible)', values='HD|HQ|LQ')
	
#Root categories
def ListeCategories():
	dir = MediaContainer()
	categories = XML.ElementFromURL(baseURL + 'initPlayer').xpath('//THEMATIQUE')
	for categorie in categories:
		nom = categorie.xpath("./NOM")[0].text.capitalize()
		idCategorie = categorie.xpath("./ID")[0].text
		icon = R("icon-folder"+idCategorie+".png")
		if(icon == None):
			icon = R('icon-folder.png')
			
		dir.Append(Function(DirectoryItem(ListeSousCategories, title = nom, thumb = icon), idCategorie = idCategorie, nomCategorie = nom))
		
	dir.Append(PrefsItem(L(u"Préférences"), thumb = R('icon-folder.png')))
	return dir
	
#Sub-categories
def ListeSousCategories(sender, idCategorie, nomCategorie):
	art = R("art-cat"+idCategorie+".png")
	if(art == None):
		art = R("art-default.jpg")
	dir = MediaContainer(title1 = "Canal Plus", title2 = nomCategorie, art = art)
	sousCategories = XML.ElementFromURL(baseURL + 'initPlayer').xpath("//THEMATIQUE[ID="+idCategorie+"]//SELECTIONS")[0]
	for sousCategorie in sousCategories:
		nom = sousCategorie.xpath("./NOM")[0].text.capitalize()
		idSousCategorie = sousCategorie.xpath("./ID")[0].text
		icon = R("icon-folder"+idCategorie+".png")
		if(icon == None):
			icon = R('icon-folder.png')
			
		dir.Append(Function(DirectoryItem(ListeVideos, title = nom, thumb = icon), idSousCategorie = idSousCategorie, nomSousCategorie = nom, art = art))
		
	return dir

#Chosen sub-category's videos
def ListeVideos(sender, idSousCategorie, nomSousCategorie, art):
	dir = MediaContainer(title1 = "Canal Plus", title2 = nomSousCategorie, art = art)
	videos = XML.ElementFromURL(baseURL + "getMEAs/" + idSousCategorie).xpath("//MEA[TYPE!='CHAINE LIVE']")
	for video in videos:
		idVideo = video.xpath('./ID')[0].text
		titre = video.xpath('./INFOS/TITRAGE/TITRE')[0].text
		soustitre = video.xpath('./INFOS/TITRAGE/SOUS_TITRE')[0].text
		if(soustitre.strip() != ""):
			titre =  titre + " - " + soustitre
			
		description = video.xpath('./INFOS/DESCRIPTION')[0].text
		thumb = video.xpath('./MEDIA/IMAGES/GRAND')[0].text
		dir.Append(Function(DirectoryItem(ListeVideosLiees, title = titre, summary = description, thumb = thumb), idVideo = idVideo, nomSousCategorie = nomSousCategorie, art = art))
	
	return dir

#Video chosen + related videos
def ListeVideosLiees(sender, idVideo, nomSousCategorie, art):
	dir = MediaContainer(title1 = "Canal Plus", title2 = nomSousCategorie, art = art)
	
	videosXml = XML.ElementFromURL(baseURL + "getVideosLiees/" + idVideo)
	videos = videosXml.xpath("//VIDEO[ID='"+idVideo+"']")
	
	videos.extend(videosXml.xpath("//VIDEO[ID!='"+idVideo+"']"))
	for video in videos:
		titre = video.xpath('./INFOS/TITRAGE/TITRE')[0].text
		soustitre = video.xpath('./INFOS/TITRAGE/SOUS_TITRE')[0].text
		if(soustitre.strip() != ""):
			titre =  titre + " - " + soustitre
			
		description = video.xpath('./INFOS/DESCRIPTION')[0].text
		thumb = video.xpath('.//MEDIA/IMAGES/GRAND')[0].text
		dir.Append(ElementVideo(video, titre, description, thumb))
		
	return dir

#Create the correct video element depending on the video's URL
def ElementVideo(video, titre, description, thumb):
	
	#Available qualities
	try:
		lienHD = video.xpath('.//MEDIA/VIDEOS/HD')[0].text
	except:
		lienHD = None
		
	try:
		lienHQ = video.xpath('.//MEDIA/VIDEOS/HAUT_DEBIT')[0].text
	except:
		lienHQ = None
		
	try:
		lienLQ = video.xpath('.//MEDIA/VIDEOS/BAS_DEBIT')[0].text
	except:
		lienLQ = None
	
	#Use the wanted quality, if it exists. If not use a lower quality
	qualitePreferee = Prefs.Get('qualite')
	if(qualitePreferee == 'LQ'):
		lien = lienLQ
		
	elif(qualitePreferee == 'HQ'):
		if(lienHQ == None):
			lien = lienLQ
		else:
			lien = lienHQ
			
	elif(qualitePreferee == 'HD'):
		if(lienHD == None):
			if(lienHQ == None):
				lien = lienLQ
			else:
				lien = lienHQ
				
		else:
			lien = lienHD
	
	#If RTMP, get url and clip parts
	if(lien.startswith("rtmp://")):
		if(lien.startswith("rtmp://vod-fms.canalplus.fr/ondemand")):
			lien = lien.replace("rtmp://vod-fms.canalplus.fr/ondemand/","")
			url = "rtmp://vod-fms.canalplus.fr/ondemand"
			
		if(lien.startswith("rtmp://geo2-vod-fms.canalplus.fr/ondemand")):
			lien = lien.replace("rtmp://geo2-vod-fms.canalplus.fr/ondemand","")
			url = "rtmp://geo2-vod-fms.canalplus.fr/ondemand"
			
		if (lien.endswith(".mp4")):
			lien = "mp4:/" + lien	
			lien = lien[:-4]
			
		elif(lien.endswith(".flv")):
			lien = lien[:-4]
	
	#Regular VideoItem if video available through http. RTMPVideoItem if not.
	if(lien.startswith("http://")):
		return VideoItem(lien, titre, summary = description, thumb = thumb)
	else:
		return RTMPVideoItem(url = url, width=640, height=375, clip = lien, title = titre, summary = description, thumb = thumb)	
		
