'''
*
* models.py: DCS Aircraft Command Entry - Database Models Module            *
*                                                                           *
* Copyright (C) 2023 Atcz                                                   *
*                                                                           *
* This program is free software: you can redistribute it and/or modify it   *
* under the terms of the GNU General Public License as published by the     *
* Free Software Foundation, either version 3 of the License, or (at your    *
* option) any later version.                                                *
*                                                                           *
* This program is distributed in the hope that it will be useful, but       *
* WITHOUT ANY WARRANTY; without even the implied warranty of                *
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General  *
* Public License for more details.                                          *
*                                                                           *
* You should have received a copy of the GNU General Public License along   *
* with this program. If not, see <https://www.gnu.org/licenses/>.           *
'''

from peewee import (Model, IntegerField, CharField, ForeignKeyField, 
                    FloatField, SqliteDatabase, IntegrityError)

db = SqliteDatabase(None, pragmas={'foreign_keys': 1})

class ProfileModel(Model):
    name = CharField(unique=True)
    aircraft = CharField(unique=False)

    class Meta:
        database = db


class SequenceModel(Model):
    identifier = IntegerField()
    profile = ForeignKeyField(ProfileModel, backref='sequences')

    class Meta:
        database = db


class CommandModel(Model):
    device_type = CharField()
    msg = CharField()
    step = FloatField(null=True)
    limitLow = FloatField(null=True)
    limitHigh = FloatField(null=True)
    description = CharField()
    value = FloatField(null=True)
    number = IntegerField(null=True)
    wp_type = CharField(default="CMD")
    profile = ForeignKeyField(ProfileModel, backref='commands')
    sequence = ForeignKeyField(SequenceModel, backref='commands', null=True)

    class Meta:
        database = db
