from app import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref
from sqlalchemy.ext.hybrid import hybrid_property
from collections import OrderedDict
from app.models.uuid import GUID
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

    @hybrid_property
    def full_name(self):
        return '{0}, {1}'.format(self.last, self.first)


####################################
#               Tables             #
####################################

class Customer(BaseMixin, NameMixin, ContactMixin, db.Model):
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))


class Vehicle(BaseMixin, db.Model):
    year = db.Column('Year', db.SmallInteger)
    make = db.Column("Make", db.VARCHAR(128))
    model = db.Column("Model", db.VARCHAR(128))
    trim = db.Column("Trim", db.VARCHAR(128))
    color = db.Column("Color", db.VARCHAR(128))
    plate_state = db.Column("State", db.VARCHAR(2))
    plate_number = db.Column("License Plate", db.VARCHAR(12))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))


class Services(BaseMixin, db.Model):
    date = db.Column("Date", db.DATE)
    type = db.Column("Type",db.VARCHAR(128))
    workplace = db.Column("Workplace",db.VARCHAR(128))
    checked_in = db.Column("Checked In Status", db.Boolean)
    latitude = db.Column("Latitude", db.Float)
    longitude = db.Column("Longitude", db.Float)
    uuid = db.Column(GUID(), default=uuid.uuid4, nullable=False, unique=True)



