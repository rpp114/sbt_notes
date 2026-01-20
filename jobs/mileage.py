import json, sys, os, datetime, calendar, time

import googlemaps

# add system directory to pull in app & models


from sbt_notes.config import GMAP_API_KEY as gmap_key
from sbt_notes.app import db, models

def build_mileage_obj(appts):
  temp_obj = {}

  for appt in appts:
    temp_obj[appt.therapist.id] = temp_obj.get(appt.therapist.id, {})
    temp_obj[appt.therapist.id][appt.start_datetime.strftime('%Y-%m-%d')] = temp_obj[appt.therapist.id].get(appt.start_datetime.strftime('%Y-%m-%d'),{'ids': [], 'locations': []})
    temp_obj[appt.therapist.id][appt.start_datetime.strftime('%Y-%m-%d')]['locations'].append(appt.location)
    temp_obj[appt.therapist.id][appt.start_datetime.strftime('%Y-%m-%d')]['ids'].append(appt.id)

  return temp_obj


def add_mileage(start_date, end_date):

  """Takes two date times to find appts between them and add the traveled mileage.  Starts and ends at company address."""

  gmaps = googlemaps.Client(key=gmap_key)

  start_date = start_date.replace(hour=00, minute=00, second=00)
  end_date = end_date.replace(hour=23, minute=59, second=59)

  appts = models.ClientAppt.query.filter(models.ClientAppt.start_datetime >= start_date, models.ClientAppt.start_datetime <= end_date, models.ClientAppt.cancelled == 0).order_by(models.ClientAppt.start_datetime).all()

  mileage_temp_obj = build_mileage_obj(appts)

  insert_mileage_obj = {}

  for therapist_id in mileage_temp_obj:
    therapist = models.Therapist.query.get(therapist_id)
    company_address = therapist.user.company.address + ' ' + therapist.user.company.city + ', ' + therapist.user.company.state + ' ' + therapist.user.company.zipcode
    therapist_appts = mileage_temp_obj[therapist_id]

    for day in therapist_appts:
      day_appts = therapist_appts[day]
      locations = [company_address] + day_appts['locations']
      ids = day_appts['ids'] + [0]

      if None in locations:
        continue
      appts_count = len(locations)

      for i in range(appts_count):
          
        appt_id = ids[i]

        start = locations[i]
        
        if appt_id == 0:
          appt_id = ids[i-1]
          end = locations[0]
        else:
          end = locations[i+1]
      
        matrix = distance_matrix = gmaps.distance_matrix([start], [end])
        
        row = matrix['rows'][0]

        insert_mileage_obj[appt_id] = insert_mileage_obj.get(appt_id, 0) + round(row['elements'][0]['distance']['value'] * .000621371)


  insert_list = [{'id': i, 'mileage': insert_mileage_obj[i]} for i in insert_mileage_obj]

  db.session.bulk_update_mappings(models.ClientAppt, insert_list)
  db.session.commit()

  return insert_list
