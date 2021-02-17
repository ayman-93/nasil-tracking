from .db import db
from datetime import datetime


class Location(db.EmbeddedDocument):
    lat = db.StringField(required=True)
    lng = db.StringField(required=True)
    isInWay = db.BooleanField(default=False)
    time = db.DateTimeField(required=True, default=datetime.now())


class Time(db.EmbeddedDocument):
    hours = db.IntField()
    minutes = db.IntField()
    seconds = db.IntField()


class Trip(db.Document):
    tripId = db.StringField(unique=True, required=True)
    copmanyId = db.StringField(required=True)
    driverId = db.StringField(required=True)
    userId = db.StringField(required=True)
    route = db.EmbeddedDocumentListField(Location)
    distance = db.FloatField(default=0)
    timeInWay = db.EmbeddedDocumentField(Time)
    createdAt = db.DateTimeField()
    updatedAt = db.DateTimeField()
    isActive = db.BooleanField(default=True)

    def getFullRoute(self):
        fullRoute = []
        for point in self.route:
            fullRoute.append({"lat": point.lat, "lng": point.lng,
                              "isInWay": point.isInWay, "time": str(point.time)})
        return fullRoute

    def getTripRoute(self):
        fullRoute = []
        for point in self.route:
            if(point.isInWay == True):
                fullRoute.append({"lat": point.lat, "lng": point.lng,
                                  "isInWay": point.isInWay, "time": str(point.time)})
        return fullRoute

    def updateRoute(self, newLocation):
        self.route.append(newLocation)
        self.save()

    def to_json(self):
        return ({"id": self.id.__str__(), "tripId": self.tripId, "copmanyId": self.copmanyId, "driverId": self.driverId, "userId": self.userId, "route": self.route, "distance": self.distance, "isActive": self.isActive, "createdAt": self.createdAt.__str__(), "updatedAt": self.updatedAt.__str__()})

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now()

        self.updatedAt = datetime.now()

        return super(Trip, self).save(*args, **kwargs)
