import logging
from load_into_redshift import REDSHIFT_URL, IAM_ROLE_ARN

VALID_COMPLAINT_TYPES = {
    "Animal Abuse",
    "Unsanitary Animal Pvt Property",
    "Dead Animal",
    "Unsanitary Animal Facility",
    "Animal Facility - No Permit",
    "Blocked Driveway",
    "Dirty Conditions"
}

def pass_data_quality_checks(sparkSession):

    min_date = sparkSession.sql('''
        SELECT year, date_key
        FROM dim_date
        WHERE date_key = (SELECT MIN(date_key) FROM dim_date)
    ''').collect()[0]

    if(min_date["year"] < 2014):
        logging.error(f"Transformed data has earlier dates than the specified date range. [minimal_date={min_date['date_key']}]")
        return False

    distinct_complaint_types = sparkSession.sql('''
        SELECT DISTINCT complaint_type
        FROM fact_service_request
    ''').collect()

    for complaint_type in distinct_complaint_types:
        if complaint_type['complaint_type'] not in VALID_COMPLAINT_TYPES:
            logging.error(f"Found invalid complaint type in transformed data. [complaint_type={complaint_type['complaint_type']}]")
            return False
    
    duplicate_unique_keys = sparkSession.sql('''
        SELECT unique_key, COUNT(*) AS count_of_unique_key
        FROM fact_service_request
        GROUP BY unique_key
        HAVING count_of_unique_key > 1
    ''').collect()

    if len(duplicate_unique_keys) != 0:
        logging.error(f"Found duplicate unique keys. [duplicate_unique_keys={','.join(row['unique_key'] for row in duplicate_unique_keys)}]")
        return False

    return True