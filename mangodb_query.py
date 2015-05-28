from pymongo import MongoClient

client = MongoClient('localhost:27017')
db = client.examples

print 'Size of the file: ', db.houston.count()
print 'Number of unique users: ', len(db.houston.distinct("created.user"))
print 'Number of nodes: ', db.houston.find({"type":"node"}).count()
print 'Number of ways: ', db.houston.find({"type":"way"}).count()
print 'Number of cafe: ', db.houston.find({"amenity": "cafe"}).count()
print 'Number of Starbucks: ', db.houston.find({"name": "Starbucks"}).count()
print 'Number of Starbucks labeled as cafe: ', db.houston.find({"amenity": "cafe", "name": "Starbucks"}).count()
print 'Top 1 contributing user: '
for ii in db.houston.aggregate([{'$group':{'_id':'$created.user', 'count':{'$sum':1}}},
                                {'$sort':{'count':-1}}, {'$limit': 1}]):
    print  ii
print 'Top 10 appearing restaurants: '
for ii in db.houston.aggregate([{"$match":{"cuisine":{"$exists":1},"amenity":'restaurant'}},{'$group':{'_id':'$cuisine', 'count':{'$sum':1}}},
                                {'$sort':{'count':-1}}, {'$limit': 10}]):
    print  ii
print 'Number of atms: ', db.houston.find({"amenity": "atm"}).count()
print 'Number of banks: ', db.houston.find({"amenity": "bank"}).count()
print 'Top 10 appearing amenities: '
for ii in db.houston.aggregate([{"$match":{"amenity":{"$exists":1}}},{'$group':{'_id':'$amenity', 'count':{'$sum':1}}},
                                {'$sort':{'count':-1}}, {'$limit': 10}]):
    print  ii
