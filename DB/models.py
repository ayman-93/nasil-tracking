from .db import db
from datetime import datetime


class Location(db.EmbeddedDocument):
    lat = db.StringField(required=True)
    lng = db.StringField(required=True)
    time = db.DateTimeField(required=True, default=datetime.now())


class Trip(db.Document):
    tripId = db.StringField(unique=True, required=True)
    copmanyId = db.StringField(required=True)
    driverId = db.StringField(required=True)
    userId = db.StringField(required=True)
    route = db.EmbeddedDocumentListField(Location)
    createdAt = db.DateTimeField()
    updatedAt = db.DateTimeField()
    isActive = db.BooleanField(default=True)

    def updateRoute(self, newLocation):
        self.route.append(newLocation)
        self.save()

    def to_json(self):
        return ({"id": self.id.__str__(), "tripId": self.tripId, "copmanyId": self.copmanyId, "driverId": self.driverId, "userId": self.userId, "route": self.route, "isActive": self.isActive, "createdAt": self.createdAt.__str__(), "updatedAt": self.updatedAt.__str__()})

    def save(self, *args, **kwargs):
        if not self.createdAt:
            self.createdAt = datetime.now()

        self.updatedAt = datetime.now()

        return super(Trip, self).save(*args, **kwargs)
