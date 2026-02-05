from OR_based_single_route_op import *
import h3
import numpy as np
import pandas as pd
from db_conn import *
from config import db_config


def execute_pg_query(query):
    """
    Executing a specific Postgres query
    :param query:
    :return: The result set.
    """
    connection_pool = PostgresConnectionPool(
        host=db_config.HOST,
        port=db_config.PORT,
        database=db_config.DATABASE,
        user=db_config.USER,
        password=db_config.PASSWORD
    )

    pg_client = PostgresClient(connection_pool)
    res = pg_client.execute_query(query)

    return res


def extract_top3_routes(df):
    top3_routes = (
        df.loc[df.groupby("route_id")["dist_km"].idxmin()]
        .nsmallest(1, "dist_km")
    )
    return top3_routes


def extract_customer_list_from_route(route_id):
    route_query = f"select c.customer_id, c.h3_res_9, crm.route_id  from locinsights.customer_route_mapping crm join locinsights.customer c " \
                  f"on crm.customer_id = c.customer_id " \
                  f"where crm.route_id = '{str(route_id)}' limit 10"
    result = execute_pg_query(route_query)
    final_res = []
    for row in result:
        final_res.append({
            "customer_id": row[0],
            "h3_res": row[1]
        })
    return pd.DataFrame(final_res)


def extract_new_customer_details(cust_df):
    new_customer = {"customer_name": cust_df["customer_name"], "customer_id": 2000,
                    "h3_res": h3.latlng_to_cell(cust_df["latitude"], cust_df["longitude"], 9)}
    return pd.DataFrame(new_customer)


def extract_route_dc(route_id):
    dc_query = f"select distinct location_id, lat, lng from locinsights.planned_visit " \
               f"where location_type not ilike '%customer%' and " \
               f"route_id = '{str(route_id)}' limit 1"
    result = execute_pg_query(dc_query)
    final_res = {}
    for row in result:
        final_res['customer_id'] = int(row[0]),
        final_res['h3_res'] = h3.latlng_to_cell(row[1], row[2], 9),
        final_res['route_id'] = route_id
    return pd.DataFrame(final_res)


def re_optimization(customer_route_json):
    cust_df = pd.read_json(customer_route_json)
    new_customer = extract_new_customer_details(cust_df)
    nearest_cust_df = pd.DataFrame.from_records(cust_df['nearest_customers'].to_list()[0])
    sorted_cust_df = nearest_cust_df.sort_values(by=['dist_km'], ascending=[True])
    top3_routes = extract_top3_routes(sorted_cust_df)

    routes = {}
    i = 1

    for row in top3_routes.itertuples():
        route_id = row.route_id
        route_cust_df = extract_customer_list_from_route(route_id) # combine all the data to dc in one single query
        route_cust_df = pd.concat([route_cust_df, new_customer], ignore_index=True)
        dc_details = extract_route_dc(route_id)
        route_cust_df = pd.concat([dc_details, route_cust_df], ignore_index=True)
        route_cust_df = pd.concat([route_cust_df, dc_details], ignore_index=True)
        route_cust_df["dwell_time"] = 33
        route_cust_df["avg_pallets"] = 11
        route_cust_df["format"] = 'S'
        print(f"route cust df == {route_cust_df}")
        proposed_route = reoptimize_all_routes(route_cust_df)
        print(proposed_route)

    return proposed_route


# if __name__ == "__main__":
#     temp_json = '''[
#       {
#         "customer_name": "Walmart ",
#         "address": "1202 S Kirkwood Rd, Kirkwood, MO 63122, United States",
#         "latitude": 38.5631543,
#         "longitude": -90.4030029,
#         "nearest_customers": [
#           {
#             "customer_id": 2003562112,
#             "customer_name": "WALMART SC #2694",
#             "route_id": "USF6AO",
#             "dist_km": 0.029869383967916503
#           }
#         ]
#       }
#     ]'''
#     re_optimization(temp_json)
