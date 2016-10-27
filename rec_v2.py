import urllib
import re
import xmltodict
from bs4 import BeautifulSoup
import sys
from datetime import datetime

INF = 50000

# filenames
animelists_file = "lists.txt"
users_mean_score_file = "users_mean_score.txt"
users_file = "users_test.txt"
top_file = "anime_top50.txt"
anime_genre_file = "anime_mean_scores_and_genres.txt"

# xmltodict animeLists
# usage example: 
#    lists[0]['myanimelist']['anime'][1]['series_title'] -> 2nd anime title
#                            in the list of the 1st user
# call readUserAnimeListsAndScores to populate
# type: list[dict] 
anime_lists = []

# array of pairs (user_mean_score,user_days_watched)
# call readUserAnimeListsAndScores to populate
# type: list[(float,float)]
user_scores = []


#   ########################################
#   ////////////////////////////////////////
#                  ANIME INFO
#   \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#   ########################################


# Returns a list of
# [title,img_URL,rating,episode_number,#rank,genres]
# of the anime_id anime
def getAnimeInfo(anime_id):
    url = "https://myanimelist.net/anime/" + anime_id
    data = urllib.urlopen(url).read()
    soup = BeautifulSoup(data,"html.parser")
    
    # Rating:
    rating = soup.find(itemprop="ratingValue")    
    if rating == None :
        rating = soup.find(class_="po-r js-statistics-info di-ib").getText().split("\n")[2][0:4]
    else:
        rating = rating.getText()
    
    # Rank:
    rank = soup.find(class_="spaceit po-r js-statistics-info di-ib").getText()
    if(rank.split("\n")[2].find("N/A")==-1):
        rank = soup.find(class_="spaceit po-r js-statistics-info di-ib").getText().split("\n")[2][3:-1]
    else:
        rank = INF
    
    # Number of episodes:
    startPos = data.find("Episodes:")
    endPos = data.find("</div>",startPos)
    number = data[startPos:endPos].split("\n")[1]
    if(number.find("Unknown")!=-1):
        number = `INF`
    
    # Title:
    title = soup.find("title").getText().split("\n")[1].split("-")[0][:-1]
    
    # Genre:
    startPos = data.find("Genres")
    endPos = data.find("</div>",startPos)
    str = data[startPos:endPos]
    str = str.split(">")
    genres = []
    for i in xrange(2,len(str)-1,2):
        genres.append(str[i])
    for i in range(len(genres)):
        genres[i] = genres[i].replace("</a","")
    
    # Image URL:
    startPos = data.find("og:image")
    endPos = data.find("\">",startPos)
    img = data[startPos+19:endPos]
    
    return [title,img,float(rating),int(number),int(rank),genres]
    
    
# returns a list of all anime ids
# currently available at myanimelist.net
def collectAnimeInfo():
    url_base = "https://myanimelist.net/topanime.php?limit="
    lim = 0
    last = 12151
    ids=[]
    
    # get page by page (50 anime ids at once)
    for i in range(0,last,50):
        url = url_base + `i` 
        print url
        data = urllib.urlopen(url).read()
        soup = BeautifulSoup(data,"html.parser")
        entries = soup.findAll(class_="di-ib clearfix")
        # take id of every of the 50 animes on current page
        for e in entries:
            str = "%s" %e
            start = str.find("id=\"#area")
            end = str.find("\"",start+4)
            ids.append(int(str[start+9:end]))
    
    ids.sort()
    return ids
    
    

#   ########################################
#   ////////////////////////////////////////
#    USER INFO (including their animelists)
#   \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#   ########################################
    
    
# gets the animeList of user
# return type: dict
def getUserAnimeList(username):
    
    url = "http://myanimelist.net/malappinfo.php?u=" + username + "&status=all&type=anime"
    data = urllib.urlopen(url).read()
    return xmltodict.parse(data)
    
    
# gets the mean score and days watched
# for the user
# return type: (float,float)
def getUserMeanScoreAndDays(username):
    url = "https://myanimelist.net/profile/" + username
    data = urllib.urlopen(url).read()
    soup = BeautifulSoup(data,"html.parser")
    html_tags = soup.find_all("div", class_="stat-score di-t w100 pt8")
    return (float(html_tags[0].get_text().split("\n")[2][12::]),float(html_tags[0].get_text().split("\n")[1][6::]))
    

#   ########################################
#     Parse myanimelist entries from dict
#   ########################################
    
# returns "My Info" from a dict entry
def getMyInfo(entry):
    return entry['myanimelist']['myinfo']

# returns user_name
def getUsername(entry):
    return entry['myanimelist']['myinfo']['user_name']

# returns user_id
def getUserId(entry):
    return entry['myanimelist']['myinfo']['user_id']

# returns user_completed
def getUserCompleted(entry):
    return entry['myanimelist']['myinfo']['user_completed']

# returns user_plantowatch
def getUserPlantowatch(entry):
    return entry['myanimelist']['myinfo']['user_plantowatch']

# returns user_days_spent_watching
def getUserDaysSpentWatching(entry):
    return entry['myanimelist']['myinfo']['user_days_spent_watching']

# returns animes info
def getUserAnimes(entry):
    return entry['myanimelist']['anime']

# returns anime info for anime idx
def getUserAnime(entry,idx):
    return entry['myanimelist']['anime'][idx]

# returns anime id for anime idx
def getUserAnimeId(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_animedb_id']

def getUserAnimeTitle(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_title']

# returns a list of synonims for the title
def getUserAnimeSynonims(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_synonyms'].split("; ")

def getUserAnimeImageURL(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_image']

def getUserAnimeWatchedEpisodes(entry,idx):
    return entry['myanimelist']['anime'][idx]['my_watched_episodes']

def getUserAnimeScore(entry,idx):
    return entry['myanimelist']['anime'][idx]['my_score']

def getUserAnimeTags(entry,idx):
    return entry['myanimelist']['anime'][idx]['my_tags']

    
# *ongoing / test purposes*
def main():

###populate anime db

    # get some ids
    ids = []
    f = open("ids.txt","r")
    ids = f.read().split("\n")
    f.close()
    ids = ids[0:10]
    
    
    # get the animeinfo for those animes
    animes = [] #[title,img_URL,rating,episode_number,#rank,genres]
    for id in ids:
        animes.append(getAnimeInfo(id))
    
    for an in animes:
        print an
        print "\n"
    
###populate user db

    f = open("users_test.txt","r")
    users = f.read().split("\n")
    f.close()
    animeLists = []
    for usr in users:
        animeLists.append(getUserAnimeList(usr))
        
    for al in animeLists:
        print getUsername(al) + " " + getUserId(al) + getUserAnimeTitle(al,0)
        
    print "done"
    
    
main()
