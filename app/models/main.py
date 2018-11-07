from app import db
from sqlalchemy.ext.declarative import declared_attr
from collections import OrderedDict
import uuid as uuid


####################################
#                  Base           #
####################################


class BaseMixin(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = db.Column(db.Integer, primary_key=True)

    def serialize(self):
        result = OrderedDict()
        for key in self.__mapper__.c.keys():
            result[key] = getattr(self, key)

        return result


####################################
#                Mixins            #
####################################
class ContactMixin(object):
    phone = db.Column('Phone', db.VARCHAR(12), index=True)
    email = db.Column(db.VARCHAR(128), index=True)


class NameMixin(object):
    first = db.Column(db.VARCHAR(128), index=True)
    last = db.Column(db.VARCHAR(128), index=True)


####################################
#               Tables             #
####################################

class Customer(BaseMixin, NameMixin, ContactMixin, db.Model):
    vehicle = db.relationship('Vehicle', backref='Customer', lazy='dynamic')


class Vehicle(BaseMixin, db.Model):
    year = db.Column("Year", db.SmallInteger)
    make = db.Column("Make", db.VARCHAR(128))
    model = db.Column("Model", db.VARCHAR(128))
    trim = db.Column("Trim", db.VARCHAR(128))
    color = db.Column("Color", db.VARCHAR(128))
    plate_state = db.Column("State", db.VARCHAR(2))
    plate_number = db.Column("License Plate", db.VARCHAR(12))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    services = db.relationship('Services', backref='Vehicle', lazy='dynamic')


class Services(BaseMixin, db.Model):
    date = db.Column("Date", db.DATE)
    type = db.Column("Type",db.VARCHAR(128))
    workplace = db.Column("Workplace",db.VARCHAR(128))
    checked_in = db.Column("Checked In Status", db.Boolean)
    latitude = db.Column("Latitude", db.Float)
    longitude = db.Column("Longitude", db.Float)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id', ondelete='CASCADE'))
    uuid = db.Column(db.String(length=32), default=uuid.uuid4().hex)




