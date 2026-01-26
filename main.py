# from OR_based_generate_routes import *
import h3
import numpy as np
import pandas as pd

from OR_based_generate_routes import create_routing_model
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


def create_distance_matrix(route_cust_df):
    """
    Extract distance based on h3 hex cells.
    :param route_cust_df: Dataframe having the customer ids and their h3 resolutions.
    :return: the complete distance matrix
    """
    customers = route_cust_df["customer_id"].values
    h3_cells = route_cust_df["h3_res"].values
    n = len(customers)

    distance_matrix = np.zeros((n, n))

    for i in range (0, n):
        for j in range (0, n):
            if i == j:
                continue
            else:
                dist = h3.grid_distance(h3_cells[i], h3_cells[j])
                distance_matrix[i][j] = dist

    return pd.DataFrame(distance_matrix, index=customers, columns=customers)


def extract_top3_routes(df):
    top3_routes = (
        df.loc[df.groupby("route_id")["dist_km"].idxmin()]
        .nsmallest(3, "dist_km")
    )
    return top3_routes


def extract_customer_list_from_route(route_id):
    route_query = f"select c.customer_id, c.h3_res_9, crm.route_id  from locinsights.customer_route_mapping crm join locinsights.customer c " \
                  f"on crm.customer_id = c.customer_id " \
                  f"where crm.route_id = 'USF09V'--'{str(route_id)}'"
    print(route_query)
    result = execute_pg_query(route_query)
    print(f"Result == {result}, \n type of result == {type(result)}")
    final_res = []
    for row in result:
        print(f"row == {row}, \n type of row == {type(row)}")
        final_res.append({
            "customer_id": row[0],
            "h3_res": row[1]
        })

    return pd.DataFrame(final_res)


def extract_new_customer_details(cust_df):
    new_customer = {"customer_name": cust_df["customer_name"]}
    new_customer["h3_res"] = h3.latlng_to_cell(cust_df["latitude"], cust_df["longitude"], 9)
    return pd.DataFrame(new_customer)


def create_route(route_cust_df):
    customer_ids = route_cust_df.index.toList()
    create_routing_model(route_cust_df, customer_ids)


def re_optimization(customer_route_json):
    cust_df = pd.read_json(customer_route_json)
    new_customer = extract_new_customer_details(cust_df)
    nearest_cust_df = pd.DataFrame.from_records(cust_df['nearest_customers'].to_list()[0])
    sorted_cust_df = nearest_cust_df.sort_values(by=['dist_km'], ascending=[False])
    top3_routes = extract_top3_routes(sorted_cust_df)

    routes = {}

    for row in top3_routes.itertuples():
        route_id = row.route_id
        route_cust_df = extract_customer_list_from_route(route_id)
        route_cust_df = pd.concat([route_cust_df, new_customer], ignore_index=True)
        dist_route_cust_df = create_distance_matrix(route_cust_df)
        proposed_route = create_route(dist_route_cust_df)









if __name__ == "__main__":
    temp_json = '''[
      {
        "customer_name": "Walmart ",
        "address": "1202 S Kirkwood Rd, Kirkwood, MO 63122, United States",
        "latitude": 38.5631543,
        "longitude": -90.4030029,
        "nearest_customers": [
          {
            "customer_id": 2003562112,
            "customer_name": "WALMART SC #2694",
            "route_id": "USF6AO",
            "dist_km": 0.029869383967916503
          }
        ]
      }
    ]'''
    re_optimization(temp_json)
