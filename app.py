from DB.models import Trip, Location
from DB.db import initialize_db
from flask_socketio import SocketIO, emit, join_room, close_room
from flask import Flask, request, Response, jsonify
from mongoengine.document import NotUniqueError
import json

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

app.config["MONGODB_HOST"] = "mongodb+srv://ayman:753258@aymancluster-ddsk0.mongodb.net/nasil?retryWrites=true&w=majority"
initialize_db(app)


@app.route('/')
def index():
    return "api is working.."

# for company


@app.route('/add-trip', methods=["POST"])
def addTrip():
    try:
        request_json = request.get_json()
        tripId = request_json["tripId"]
        copmanyId = request_json["copmanyId"]
        driverId = request_json["driverId"]
        userId = request_json["userId"]
    except Exception as e:
        return Response(json.dumps({"msg": "You are missing " + str(e)}))
    try:
        trip = Trip(tripId=tripId, copmanyId=copmanyId,
                    driverId=driverId, userId=userId).save()
    except (NotUniqueError):
        return Response(json.dumps({"msg": "Trip already exist"}))
    trip = trip.to_json()
    return Response(json.dumps(trip), mimetype="application/json", status=200)


@app.route('/update-trip', methods=["POST"])
def updateTrip():
    try:
        request_json = request.get_json()
        tripId = request_json["tripId"]
        driverId = request_json["driverId"]
    except Exception as e:
        return Response(json.dumps({"msg": "You are missing " + str(e)}))

    updatedTrip = Trip.objects(tripId=tripId).update_one(
        set__driverId=driverId)

    if(updatedTrip == 1):
        return Response(json.dumps({"update": "true"}), mimetype="application/json", status=200)
    else:
        return Response(json.dumps({"update": "false"}), mimetype="application/json", status=200)

# for user


@app.route('/user-check-trip/<userId>', methods=["GET"])
def userCheckTrip(userId):
    try:
        trip = Trip.objects.get(userId=userId, isActive=True)
        return Response(json.dumps({"TripId": trip.tripId}), mimetype="application/json", status=200)
    except Trip.DoesNotExist:
        return Response(json.dumps({"msg": "Trip does not exist"}), mimetype="application/json", status=404)

# for driver


@app.route('/driver-check-trip/<driverId>', methods=["GET"])
def driverCheckTrip(driverId):
    try:
        trip = Trip.objects.get(driverId=driverId, isActive=True)
        return Response(json.dumps({"TripId": trip.tripId}), mimetype="application/json", status=200)
    except Trip.DoesNotExist:
        return Response(json.dumps({"msg": "Trip does not exist"}), mimetype="application/json", status=404)


# company, user or driver
@socketio.on('joinTrip')
def newLocation(data):
    join_room(data["tripId"])


# this comes from driver, data = { "driverId" : "123" , "location": { "lat": "234", "lng": "543" } }
# send to user and company who joind the trip
@socketio.on('newLocation')
def newLocation(data):
    driverId = data['driverId']
    lat = data['location']['lat']
    lng = data['location']['lng']
    location = Location(lat=lat, lng=lng)
    try:
        trip = Trip.objects.get(driverId=driverId, isActive=True)
        tripId = trip.tripId
        emit("driverLocation", {"lat": lat, "lng": lng}, room=tripId)
        trip.updateRoute(location)
    except Trip.DoesNotExist:
        print("Trip does not exist")


@socketio.on('endTrip')
def newLocation(data):
    driverId = data['driverId']
    trip = Trip.objects.get(driverId=driverId, isActive=True)
    tripId = trip.tripId
    Trip.objects(
        tripId=tripId).update_one(set__isActive=False)
    close_room(tripId)


if __name__ == '__main__':
    socketio.run(app, debug=True)
