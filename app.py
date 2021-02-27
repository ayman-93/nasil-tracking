from DB.models import Trip, Location
from DB.db import initialize_db
from flask_socketio import SocketIO, emit, join_room, close_room
from flask import Flask, request, Response, jsonify
from mongoengine.document import NotUniqueError
from utilities.calculateDist import getDistanceBettwenTwo
from utilities.calculateTime import getDuration
import json
from datetime import datetime

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
        set__driverId=driverId, set__updatedAt=datetime.now())

    if(updatedTrip == 1):
        return Response(json.dumps({"update": "true"}), mimetype="application/json", status=200)
    else:
        return Response(json.dumps({"update": "false"}), mimetype="application/json", status=400)
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

# get routes from start to end (isInWay=true) by tripId


@app.route('/get-full-route/<tripId>', methods=["GET"])
def fetFullRoute(tripId):
    try:
        trip = Trip.objects.get(tripId=tripId)
        return Response(json.dumps({"route": trip.getFullRoute()}), mimetype="application/json", status=200)
    except Trip.DoesNotExist:
        return Response(json.dumps({"msg": "Trip does not exist"}), mimetype="application/json", status=404)


@app.route('/get-trip-route/<tripId>', methods=["GET"])
def getTripRoute(tripId):
    try:
        trip = Trip.objects.get(tripId=tripId)
        return Response(json.dumps({"route": trip.getTripRoute(), "distance": trip.distance}), mimetype="application/json", status=200)
    except Trip.DoesNotExist:
        return Response(json.dumps({"msg": "Trip does not exist"}), mimetype="application/json", status=404)


@app.route('/end-trip/<tripId>', methods=["GET"])
def endTrip(tripId):
    try:
        Trip.objects(tripId=tripId).update_one(set__isActive=False)
    except Trip.DoesNotExist:
        return Response(json.dumps({"msg": "Trip does not exist"}), mimetype="application/json", status=404)
    try:
        close_room(tripId)
    except Exception as e:
        return Response(json.dumps({"msg": "Error"+str(e)}), mimetype="application/json", status=404)

# company, user or driver
@socketio.on('joinTrip')
def newLocation(data):
    print("test")
    join_room(str(data["tripId"]))
    emit("joined", {"message": "done", "trip_id": str(
        data["tripId"])}, room=data["tripId"])


# this comes from driver, data = { "driverId" : "123" , "location": { "lat": "234", "lng": "543" } }
# send to user and company who joind the trip
@socketio.on('newLocation')
def newLocation(data):
    driverId = data['driverId']
    lat = data['location']['lat']
    lng = data['location']['lng']
    # isInWay = data['isInWay']
    # print str(data)

    isInWay = 1

    location = Location(lat=lat, lng=lng, isInWay=isInWay, time=datetime.now())
    try:
        trip = Trip.objects.get(driverId=driverId, isActive=True)
        tripId = trip.tripId
        LocationsInWay = list(filter(lambda x: x.isInWay == True, trip.route))
        newTimeInWay = "00:00"
        if(len(LocationsInWay) > 0 and isInWay == 1):

            firstInWayTime = LocationsInWay[0].time
            # newTime = datetime.now() - firstInWayTime
            timeFromFirstInWayToNow = datetime.now() - firstInWayTime
            newTimeInWay = getDuration(
                timeFromFirstInWayToNow, "default")
            Trip.objects(tripId=tripId).update_one(set__timeInWay=newTimeInWay)

            # trip.timeInWay = trip.timeInWay + timeBetweenRequests
            # print(trip.route[-1].time - datetime.now)
        else:
            print("not in way")
        # time = trip.route[-1].time
        oldDistance = trip.distance
        try:
            newDistance = oldDistance + getDistanceBettwenTwo(
                trip.route[-1].lat, trip.route[-1].lng, lat, lng)
        except:
            newDistance = oldDistance + 0
        emit("driverLocation", {"lat": lat, "lng": lng,
                                "distance": newDistance, "time": newTimeInWay}, room=tripId)
        trip.updateRoute(location)
        Trip.objects(tripId=tripId).update_one(set__distance=newDistance)
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
