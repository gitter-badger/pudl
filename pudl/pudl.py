from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm.collections import attribute_mapped_collection

#import eiaf923
import fercf1

"""
The Public Utility Data Liberation (PUDL) project integrates several different
public data sets into one well normalized database allowing easier access and
interaction between all of them.

This module defines database tables using the SQLAlchemy Object Relational
Mapper (ORM) and initializes the database from several sources:

 - US Energy Information Agency (EIA):
   - Form 860 (eia860)
   - Form 861 (eia861)
   - Form 923 (eia923)
 - US Federal Energy Regulatory Commission (FERC):
   - Form 1 (ferc1)
   - Form 714 (ferc714)
 - US Environmental Protection Agency (EPA):
   - Air Market Program Data (epaampd)
   - Greenhouse Gas Reporting Program (epaghgrp)

"""

Base = declarative_base()

class UtilityFERC1(Base):
    """
    """ #{{{
    __tablename__ = 'utilities_ferc1'
    respondent_id = Column(Integer, primary_key=True)
    respondent_name = Column(String, nullable=False)
    util_id_pudl = Column(Integer, ForeignKey('utilities.id'), nullable=False)
#}}}

class PlantFERC1(Base):
    """
    """ #{{{
    __tablename__ = 'plants_ferc1'
    respondent_id = Column(Integer,
                           ForeignKey('utilities_ferc1.respondent_id'),
                           primary_key=True)
    plant_name = Column(String, primary_key=True, nullable=False)
    plant_id_pudl = Column(Integer, ForeignKey('plants.id'), nullable=False)
#}}}

class UtilityEIA923(Base):
    """
    """ #{{{
    __tablename__ = 'utilities_eia923'
    operator_id = Column(Integer, primary_key=True)
    operator_name = Column(String, nullable=False)
    util_id_pudl = Column(Integer,
                   ForeignKey('utilities.id'),
                   nullable=False)
#}}}

class PlantEIA923(Base):
    """
    """ #{{{
    __tablename__ = 'plants_eia923'
    plant_id = Column(Integer, primary_key=True)
    plant_name = Column(String, nullable=False)
    plant_id_pudl = Column(Integer, ForeignKey('plants.id'), nullable=False)
#}}}

class Utility(Base):
    """
    An object describing an electric utility operating in the US.
    
    The ElecUtil object is populated with publicly reported data collected from
    FERC, EIA, EPA and state Public Utility Commission proceedings.
    """ #{{{
    __tablename__ = 'utilities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    utilities_eia923 = relationship("UtilityEIA923")
    utilities_ferc1 = relationship("UtilityFERC1")
#}}}

class Plant(Base):
    """
    A co-located collection of electricity generating infrastructure.
    """ # {{{
    __tablename__ = 'plants'
    id = Column(Integer, primary_key=True)
    name = Column(String)
#    us_state = Column(String, ForeignKey('us_states.abbr'))
#    primary_fuel = Column(String, ForeignKey('fuels.name')) # or ENUM?
#    total_capacity = Column(Float)

    plants_ferc1 = relationship("PlantFERC1")
    plants_eia923 = relationship("PlantEIA923")
#}}}

class State(Base):
    """
    A list of US states.
    """ #{{{
    __tablename__ = 'us_states'
    abbr = Column(String, primary_key=True)
    name = Column(String)
#}}}

class Fuel(Base):
    """
    A list of strings denoting possible fuel types.
    """ #{{{
    __tablename__ = 'fuels'
    name = Column(String, primary_key=True)
#}}}

class Year(Base):
    """A list of valid data years."""
    __tablename__ = 'years'
    year = Column(Integer, primary_key=True)

class Month(Base):
    """A list of valid data months."""
    __tablename__ = 'months'
    month = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class Quarter(Base):
    """A list of fiscal/calendar quarters."""
    __tablename__ = 'quarters'
    q = Column(Integer, primary_key=True) # 1, 2, 3, 4
    end_month = Column(Integer, nullable=False) # 3, 6, 9, 12

class RTOISO(Base):
    """A list of valid Regional Transmission Organizations and Independent
       System Operators."""
    __tablename__ = 'rto_iso'
    name = Column(String, primary_key=True)

class FuelUnit(Base):
    """A list of strings denoting possible fuel units of measure."""
    __tablename__ = 'fuel_units'
    unit = Column(String, primary_key=True)

class PrimeMover(Base):
    """A list of strings denoting different types of prime movers."""
    __tablename__ = 'prime_movers'
    prime_mover = Column(String, primary_key="True")

def init_db(Base):
    """
    """ #{{{
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import pandas as pd

    engine = create_engine('postgresql://catalyst@localhost:5432/pudl_sandbox')

    # Wipe it out and start anew for testing purposes...
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    session.add_all([State(abbr=k, name=v) for k,v in us_states.items()])
    session.commit()

    # Populate the tables which define the mapping of EIA and FERC IDs to our
    # internal PUDL IDs, for both plants and utilities, so that we don't need
    # to use those poorly defined relationships any more.  These mappings were
    # largely determined by hand in an Excel spreadsheet, and so may be a
    # little bit imperfect. We're pulling that information in from the
    # "results" directory...

    map_eia923_ferc1_file = '../results/id_mapping/mapping_eia923_ferc1.xlsx'

    plant_map = pd.read_excel(map_eia923_ferc1_file,'plants_output',
                              converters={'plant_id':int,
                                          'plant_name':str,
                                          'respondent_id_ferc1':int,
                                          'respondent_name_ferc1':str,
                                          'plant_name_ferc1':str,
                                          'plant_id_eia923':int,
                                          'plant_name_eia923':str,
                                          'operator_name_eia923':str,
                                          'operator_id_eia923':int})

    util_map  = pd.read_excel(map_eia923_ferc1_file,'utilities_output',
                              converters={'utility_id':int,
                                          'utility_name':str,
                                          'respondent_id_ferc1':int,
                                          'respondent_name_ferc1':str,
                                          'operator_id_eia923':int,
                                          'operator_name_eia923':str})

    plants = plant_map[['plant_id','plant_name']]
    plants = plants.drop_duplicates('plant_id')

    plants_eia923 = plant_map[['plant_id_eia923','plant_name_eia923','plant_id']]
    plants_eia923 = plants_eia923.drop_duplicates('plant_id_eia923')

    plants_ferc1 = plant_map[['plant_name_ferc1','respondent_id_ferc1','plant_id']]
    plants_ferc1 = plants_ferc1.drop_duplicates(['plant_name_ferc1','respondent_id_ferc1'])

    utils = util_map[['utility_id','utility_name']]
    utils = utils.drop_duplicates('utility_id')

    utils_eia923 = util_map[['operator_id_eia923','operator_name_eia923','utility_id']]
    utils_eia923 = utils_eia923.drop_duplicates('operator_id_eia923')

    utils_ferc1 = util_map[['respondent_id_ferc1','respondent_name_ferc1','utility_id']]
    utils_ferc1 = utils_ferc1.drop_duplicates('respondent_id_ferc1')

    # At this point there should be at most one row in each of these data
    # frames with NaN values after we drop_duplicates in each. This is because
    # there will be some plants and utilities that only exist in FERC, or only
    # exist in EIA, and while they will have PUDL IDs, they may not have
    # FERC/EIA info (and it'll get pulled in as NaN)

    for df in [plants_eia923, plants_ferc1, utils_eia923, utils_ferc1]:
        assert(df[pd.isnull(df).any(axis=1)].shape[0]<=1)
        df.dropna(inplace=True)

    for p in plants.itertuples():
        session.add(Plant(id = int(p.plant_id), name = p.plant_name))

    for p in plants_eia923.itertuples():
        session.add(PlantEIA923(plant_id      = int(p.plant_id_eia923),
                                plant_name    = p.plant_name_eia923,
                                plant_id_pudl = int(p.plant_id)))

    for p in plants_ferc1.itertuples():
        session.add(PlantFERC1(respondent_id = int(p.respondent_id_ferc1),
                               plant_name    = p.plant_name_ferc1,
                               plant_id_pudl = int(p.plant_id)))

    for u in utils.itertuples():
        session.add(Utility(id = int(u.utility_id), name = u.utility_name))

    for u in utils_eia923.itertuples():
        session.add(UtilityEIA923(operator_id   = int(u.operator_id_eia923),
                                  operator_name = u.operator_name_eia923,
                                  util_id_pudl  = int(u.utility_id)))

    for u in utils_ferc1.itertuples():
        session.add(UtilityFERC1(respondent_id   = int(u.respondent_id_ferc1),
                                 respondent_name = u.respondent_name_ferc1,
                                 util_id_pudl    = int(u.utility_id)))

    session.commit()
    session.close_all()

    # Populate the static lists:
    # State
    # Fuel
    # Month
    # Year
    # Quarter
    # RTOISO
    # FuelUnit
    # PrimeMover

#}}}

# Static data for populating lists in the DB...

us_states = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NA': 'National',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}

#{{{

#class Boiler(Base):
#    __tablename__ = 'boiler'
#
#class Generator(Base):
#    __tablename__ = 'generator'
#
#class PlantOwnership(Base):
#    """Describes plant ownership shares by utility."""
#    __tablename__ = 'plant_ownership'
#    util_id = Column(Integer, primary_key=True, ForeignKey('utils_pudl.id'))
#    plant_id = Column(Integer, primary_key=True, ForeignKey('plants_pudl.id'))
#    ownership_share = Column(Float, nullable=False)

#class FuelDeliveryFERC1(Base):
#    __tablename__ = 'ferc_f1_fuel_delivery'
#
#class FuelDeliveryEIA923(Base):
#    __tablename__ = 'eia_f923_fuel_delivery'
#
#class FuelDelivery(Base):
#    __tablename__ = 'fuel_delivery'
#
#class PowerPlantUnit(Base):
#    __tablename__ = 'power_plant_unit'


#}}}