import MySQLdb
from datetime import datetime
from operator import itemgetter

#db = MySQLdb.connect("localhost","root","","anime")
#cursor = db.cursor()

# indexes for animes table
ANIME_ID_IDX = 0
ANIME_TITLE_IDX = 1
ANIME_RANK_IDX = 2
ANIME_RATING_IDX = 3
ANIME_EPISODE_NUMBER_IDX = 4
ANIME_IMAGE_URL_IDX = 5
ANIME_GENRES_IDX = 6

# indexes for user table
USER_ID_IDX = 0
USER_NAME_IDX = 1
USER_COMPLETED_IDX = 2
USER_DAYS_SPENT_IDX = 3
USER_MEAN_SCORE_IDX = 4

# indexes for user_history table
HISTORY_USER_ID_IDX = 0
HISTORY_ANIME_ID_IDX = 1
HISTORY_ANIME_RATING_IDX = 2

# indexes for AnimeRating objects
ANIMERATING_ID_IDX = 0
ANIMERATING_IDX = 1

# minimum number of common animes betwen 2 users for similarity to be calculated
COMMON_THRESHOLD = 0

# max number of users --> for testing purposes
MAX_NUM_USERS = 5

# general info from an anime
class Anime:

    def __init__(self,id,title,rank,rating,episodeNumber,imageURL,genres):
        self.id = id
        self.title = title
        self.rank = rank
        self.rating = rating
        self.episodeNumber = episodeNumber
        self.imageURL = imageURL
        self.genres = genres


class User:

    def __init__(self,id,name,completed,daysSpent,meanScore,animeRatings):
        self.id = id
        self.name = name
        self.completed = completed
        self.daysSpent = daysSpent
        self.meanScore = meanScore
        self.animeRatings = animeRatings #list of Anime objects : use ANIMERATING_ID_IDX,ANIMERATING_IDX for selection
        self.animeIDs = self.getAnimeIDs()
    
    
    # return all animeIDs of watched ones
    def getAnimeIDs(self):
        lst=[]
        for anime in self.animeRatings:
            lst.append(anime[ANIMERATING_ID_IDX])
        return lst
            
    # return list of common anime ids of current user and otherUsr
    def getCommonAnimes(self,otherUsr):
        return list(set(self.animeIDs)&set(otherUsr.animeIDs))

    # returns similarity coeficient betwen current user and otherUsr
    def getSimilarityBetwenUsers(self,otherUsr):
        common = self.getCommonAnimes(otherUsr)
        meanScore = self.meanScore
        otherMeanScore = otherUsr.meanScore
        
        # go further only if number of common animes is higher than COMMON_THRESHOLD
        if len(common) < COMMON_THRESHOLD:
            return -1
        
        # for all common animes
        #   take all (rating - userMeanScore) product (from both users)
        #   and sum them
        # divide that sum by mean squared error

        # get all common animeRatings
        selfCommon = [[animeId,animeRating] for [animeId,animeRating] in self.animeRatings if animeId in common]
        otherCommon = [[animeId,animeRating] for [animeId,animeRating] in otherUsr.animeRatings if animeId in common]
        selfCommon.sort()
        otherCommon.sort()
        
        sum=0
        selfErr=0
        otherErr=0
        
        for i in range(len(common)):
            selfDif = selfCommon[i][ANIMERATING_IDX] - meanScore 
            otherDif = otherCommon[i][ANIMERATING_IDX] - otherMeanScore
            sum += selfDif * otherDif
            selfErr += selfDif**2
            otherErr += otherDif**2

        try:
            errProd = (selfErr*otherErr)**0.5
            retVal = float(sum) / errProd
        except:
            # division by zero
            return -2
            
        return retVal
        
# returns a list of Users (taken from the database)
def getUsersData():
    users = []
    
    fl = 0 ### to be deleted
    cursor.execute("SELECT * FROM USERS")
    history_cursor = db.cursor()
    for item in cursor:
        fl = fl + 1### to be deleted
        if fl==MAX_NUM_USERS:### to be deleted
            break;### to be deleted
        id,name,completed,daysSpent,meanScore =  [int(item[USER_ID_IDX]), item[USER_NAME_IDX],
        int(item[USER_COMPLETED_IDX]), float(item[USER_DAYS_SPENT_IDX]), float(item[USER_MEAN_SCORE_IDX])]
        
        query = "SELECT * FROM USER_HISTORY WHERE USER_ID = %s" %int(id)
        history_cursor.execute(query)
        animes = []
        for animeIt in history_cursor:
            anime_id,user_rating = [int(animeIt[HISTORY_ANIME_ID_IDX]),
            int(animeIt[HISTORY_ANIME_RATING_IDX])]
            animes.append([anime_id,user_rating])
        
        # here we have generic data from user + his anime list
        # so we can build the lists / user object
 
        users.append(User(id,name,completed,daysSpent,meanScore,animes))

    return users

    
# return User with "id"
def getUserData(id):
    query = "SELECT * FROM USERS WHERE ID = %s" %id
    cursor.execute(query)
    data = cursor.fetchone()
    [id,name,completed,daysSpent,meanScore] = [int(data[USER_ID_IDX]),data[USER_NAME_IDX],
    int(data[USER_COMPLETED_IDX]),float(data[USER_DAYS_SPENT_IDX]),float(data[USER_MEAN_SCORE_IDX])]
    
    query = "SELECT * FROM USER_HISTORY WHERE USER_ID = %s" %int(id)
    cursor.execute(query)
    animes = []
    for animeIt in cursor:
        anime_id,user_rating = [int(animeIt[HISTORY_ANIME_ID_IDX]),
        int(animeIt[HISTORY_ANIME_RATING_IDX])]
        animes.append([anime_id,user_rating])
    
    return User(id,name,completed,daysSpent,meanScore,animes)
    
    
# returns Anime for the anime with "id"
# exception for id not found not handled yet
def getAnimeData(id):
    query = "SELECT * FROM ANIMES WHERE ID = %s" %id
    cursor.execute(query)
    anime = cursor.fetchone()
    
    [id,title,rank,rating,episodeNumber,imageURL,genres] = [int(anime[ANIME_ID_IDX]),anime[ANIME_TITLE_IDX],
    int(anime[ANIME_RANK_IDX]),float(anime[ANIME_RATING_IDX]),int(anime[ANIME_EPISODE_NUMBER_IDX]),anime[ANIME_IMAGE_URL_IDX],
    anime[ANIME_GENRES_IDX]]
    
    return Anime(id,title,rank,rating,episodeNumber,imageURL,genres)
    

# return a matrix with all user similarities
def formUserSimilarityMatrix(users):    
    sims = []
    for i in range(len(users)-1):
        currUser = users[i]
        simsj=[]
        for j in range(i+1,len(users)):
            sim = currUser.getSimilarityBetwenUsers(users[j])
            simsj.append(sim)
        sims.append(simsj)
    return sims
    
    
# returns a list of all similarities for user with userIndex + otherUserIndex
def getAllSimilaritiesToUser(sims,userIndex):
    
#   Similarity matrix looks like this: 
#
#    0   1   2   3
#    _______________
#  0|s01 s02 s03 s04            
#  1|s12 s13 s14
#  2|s23 s24
#  3|s34
#     
    allSims=[]
    # get similarities from above userIndex line
    for i in range(userIndex):
        allSims.append((i,sims[i][userIndex-i-1]))
        
        
    # get similarities from userIndex line
    for j in range(len(sims)-userIndex):
        allSims.append((j+userIndex+1,sims[userIndex][j]))
        
    return allSims
   
# return list of pairs (userIndex,similarity) 
# relative to user with userIndex
def getKMostSimilarToUser(k,sims,userIndex):
    allSims = getAllSimilaritiesToUser(sims,userIndex)
    allSimsSorted = sorted(allSims,key=itemgetter(1),reverse=True) #sort after similarity
    return allSimsSorted[0:k]
    
    
def getKNeighbours(k,sims,users,userIndex):
    neighRaw = getKMostSimilarToUser(k,sims,userIndex)
    neighbours=[]
    for neigh in neighRaw:
        nIdx=neigh[0]
        neighbours.append(users[nIdx])
    return neighbours
    
# check if animeId is in user anime list
def isAnimeInUserAnimeList(user,animeId):    
    if animeId in user.animeIDs:
        return True
    return False

def getAnimeRatingFromUser(user,animeId):
    for anime in user.animeRatings:
        if anime[ANIMERATING_ID_IDX] == animeId:
            return anime[ANIMERATING_IDX]
    return -1
    
# get prediction coeficient: (coef,similarityWithUser) for otherUser to recommend animeId to user with userIndex
def getPredictonCoeficient(animeId,users,userIndex,otherUser):
        currUser = users[userIndex]
        sim = currUser.getSimilarityBetwenUsers(otherUser)
        otherMeanScore = otherUser.meanScore
        otherAnimeRating = getAnimeRatingFromUser(otherUser,animeId)
        
        return (sim * (otherAnimeRating-otherMeanScore),sim)
    
# users = userMatrix
# neighbours = most similar users
# return list of (animeId,predictionCoef)
def getKPredictions(k,users,neighbours,userIndex): 
    currUser = users[userIndex]
    pred=[] # list of (animeId,predictionCoef)
    predSum=0
    simSum=0
    predRaw=[]
    
    # for every neighbour
    for neigh in neighbours:
        for animeId in neigh.animeIDs:
            # get all animes that currUser hasn't watch
            if isAnimeInUserAnimeList(currUser,animeId):
                continue
            else:
                (p,sim) = getPredictonCoeficient(animeId,users,userIndex,neigh)
                predRaw.append((animeId,(p,sim)))
        
        
    # we have for every unwatched anime by currUser a tuple like this:
    # (animeId, (p,sim) )
    # he have to group by animeId and calculate sum(p)/sum(sim)
    predRaw = sorted(predRaw,key=itemgetter(0))
    prevId = predRaw[0][0]
    for anime in predRaw:
        currId = anime[0]
        # we have the list grouped by animeID
        # so we have to sum up untill the currId changes
        if(prevId==currId):
            predSum+= anime[1][0]
            simSum+= anime[1][1]
        else:
            # ended reducing predRaw for prevID animeID
            val=0
            try:
                val = predSum/simSum
            except:
                # division by zero mean simSum is 0 => low prediction
                val = -2
            # we now have final value for animeID = prevID
            pred.append((prevId,val))
            # start summing for next ID
            predSum = anime[1][0]
            simSum = anime[1][1]
        
        # take next step
        prevId = currId
        
        
    # sort the list after prediction coeficient
    pred = sorted(pred,key=itemgetter(1),reverse=True)
    return pred[0:k]
            
def pickleAnimeData():
    pass

#############################    
### testing purposes only ###
#############################
def getAnimeRatingStr(animeR):
    str="{"
    for an in animeR:
        str += `an[ANIMERATING_ID_IDX]` + " " + `an[ANIMERATING_IDX]` + "\t"
    str += "}"
    return str

#############################    
### testing purposes only ###
#############################    
def printUserData(user):
    str = `user.id` + " " +  user.name + " " + `user.completed` + " " + `user.daysSpent` + " " + `user.meanScore` + "->"
    str += getAnimeRatingStr(user.animeRatings)
    print str
    
    
#############################    
### testing purposes only ###
#############################
def printSimilarityMatrix(m):
    for i in range(len(m)):
        str=""
        for j in range(len(m)):
            if(i+j+1 > len(m)):
                break
            str += `m[i][j]` + " "
        print str
    
    
def test_suite_2():

    
    usr = getUserData("5145867")
    printUserData(usr)
    
    an = getAnimeData(usr.animeIDs[0])
    print `an.id` + " " + an.title + " " + `an.rank` + " " + `an.rating` + " " + `an.episodeNumber` + " " + an.genres

    
    print "done"


    
def test_suite_1():

    ############################
    # test 1:
    # get time for getUsersData()
    start = datetime.now()
    #usrs =  getUsersData()
    usrs=[]
    stop = datetime.now()
    dif = stop-start
    print "Test1:\t getUsersData --> ", `dif.seconds`
    ############################
    
    
    ############################################################
    # test 2:
    # get time for passing through all users and their animelist
    start = datetime.now()
    for us in usrs:
        for an in us.animeRatings:
            us.id = 0
    stop = datetime.now()
    dif = stop-start
    print "Test2:\t passing through users --> ", `dif.seconds`
    ############################################################
    
    
    ###########################################
    # test 3:
    # test how the similarity algorhitm behaves
    r1 = [[1,8],[2,7],[3,5],[5,7]] 
    r2 = [[1,5],[2,6],[5,6],[3,6]]
    r3 = [[1,7]]
    r4 = [[1,8],[4,7]]
    u1 = User(1,"a",1,1,7,r1)
    u2 = User(2,"b",2,2,5,r2)
    u3 = User(3,"c",1,1,7,r3)
    u4 = User(4,"c",1,1,8,r4)
    
    print "Test3:\t SIM ALGO: "
    print "\t\t",u1.getSimilarityBetwenUsers(u2)
    print "\t\t",u1.getSimilarityBetwenUsers(u3)
    print "\t\t",u2.getSimilarityBetwenUsers(u3)
    ###########################################
    
    
    ##########################
    # test 4:
    # test similarities matrix
    usrs = []
    usrs.append(u1)
    usrs.append(u2)
    usrs.append(u3)
    usrs.append(u4)
    sims = formUserSimilarityMatrix(usrs)
    print "Test4:\t Test SimilarityMatrix"
    printSimilarityMatrix(sims)
    print sims
    ##########################
    
    print "Test5.1:\t All similarities"
    print getAllSimilaritiesToUser(sims,3)
    
    print "Test5.2:\t K Most similar (3)"
    print getKMostSimilarToUser(3,sims,3)
    
    print "Test5.3:\t Neighbours"
    neighs = getKNeighbours(3,sims,usrs,3)
    for n in neighs:
        print n.animeIDs
   
    
    print "Test6:\t K Predictions"
    print getKPredictions(10,usrs,neighs,3)
    
    print "done"

def main():
    test_suite_1()
    
if __name__ == "__main__":
    main()