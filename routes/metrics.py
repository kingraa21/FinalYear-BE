from flask import Blueprint, jsonify, request
from collections import Counter
import pandas as pd
import requests
import io

api_blueprint = Blueprint('api', __name__)

# # Function to load CSV data from a URL
# def load_data_from_url(file_url):
#     response = requests.get(file_url)
#     response.raise_for_status()  # Check if the request was successful
#     data = response.content.decode('utf-8')
#     df = pd.read_csv(io.StringIO(data))
#     return df

# # Preprocess the data
# def preprocess_data(df):
#     df['date_published'] = pd.to_datetime(df['date_published'])
#     df['month'] = df['date_published'].dt.to_period('M')
#     return df

# # Compute statistics
# def compute_statistics(df):
#     # Number of advisories for each technology for each month
#     technology_by_month = df.groupby(['month', 'technology_name']).size().unstack(fill_value=0).reset_index().sort_values(by='month', ascending=False)

#     technology_by_month_count = df.groupby(['vendor_name', 'month']).size().reset_index(name='count').sort_values(by=['month', 'count'], ascending=[False, False])
    
#     technology_by_month['month'] = technology_by_month['month'].astype(str)
#     technology_by_month_count['month'] = technology_by_month_count['month'].astype(str)

#     # Number of advisories by technology
#     tech_count = df['technology_name'].value_counts().reset_index(name='count').rename(columns={'index': 'technology_name'}).sort_values(by='count', ascending=False)

#     # Number of advisories by vendor
#     vendor_count = df['vendor_name'].value_counts().reset_index(name='count').rename(columns={'index': 'vendor_name'}).sort_values(by='count', ascending=False)

#     # Number of advisories by each unique vendor and technology
#     vendor_tech = df.groupby(['vendor_name', 'technology_name']).size().reset_index(name='count').sort_values(by='count', ascending=False)

#     return {
#         'tech_month': technology_by_month.to_dict(orient='records'),
#         'tech_month_count': technology_by_month_count.to_dict(orient='records'),
#         'tech_count': tech_count.to_dict(orient='records'),
#         'vendor_count': vendor_count.to_dict(orient='records'),
#         'vendor_tech': vendor_tech.to_dict(orient='records')
#     }


# @api_blueprint.route('/statistics', methods=['GET'])
# def get_statistics():
#     file_url = request.args.get('file_url')
#     if file_url:
#         try:
#             df = load_data_from_url(file_url)
#             df = preprocess_data(df)
#             stats = compute_statistics(df)
#             return jsonify(stats)
#         except Exception as e:
#             return jsonify({'message': str(e)}), 400
#     else:
#         return jsonify({'message': 'No file_url provided'}), 400


# Load and preprocess the data
# response = requests.get("https://innovictus.s3.amazonaws.com/vendor_advisories.csv")
# response.raise_for_status()  # Check if the request was successful
# data = response.content.decode('utf-8')
# df = pd.read_csv(io.StringIO(data))
# df['date_published'] = pd.to_datetime(df['date_published'])
# df['month'] = df['date_published'].dt.to_period('M')

def fetch_and_prepare_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return None, str(e)
    
    data = response.content.decode('utf-8')
    df = pd.read_csv(io.StringIO(data))
    df['date_published'] = pd.to_datetime(df['date_published'])
    df['month'] = df['date_published'].dt.to_period('M')
    return df, None

def top_n_others(series, n=6, others_label='Others'):
    counts = Counter(series)
    top_counts = counts.most_common(n)
    top_n = [{'name': label, 'value': count} for label, count in top_counts]
    others_count = sum(counts.values()) - sum(count for _, count in top_counts)
    if others_count > 0:
        top_n.append({'name': others_label, 'value': others_count})
    return top_n

@api_blueprint.route('/severity-count', methods=['GET'])
def severity_count():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    df, error = fetch_and_prepare_data(url)
    if error:
        return jsonify({'error': error}), 400

    data = top_n_others(df['severity'], n=3)
    return jsonify(data)

@api_blueprint.route('/vendor-count', methods=['GET'])
def vendor_count():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    df, error = fetch_and_prepare_data(url)
    if error:
        return jsonify({'error': error}), 400

    data = top_n_others(df['vendor_name'])
    return jsonify(data)

@api_blueprint.route('/technology-count', methods=['GET'])
def technology_count():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    df, error = fetch_and_prepare_data(url)
    if error:
        return jsonify({'error': error}), 400

    data = top_n_others(df['technology_name'])
    return jsonify(data)

@api_blueprint.route('/month-count', methods=['GET'])
def month_count():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    df, error = fetch_and_prepare_data(url)
    if error:
        return jsonify({'error': error}), 400

    data = df.groupby('month').size().reset_index(name='count')
    data['month'] = data['month'].astype(str)
    return jsonify(data.to_dict(orient='records'))

@api_blueprint.route('/vendor-severity-count', methods=['GET'])
def vendor_severity_count():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    df, error = fetch_and_prepare_data(url)
    if error:
        return jsonify({'error': error}), 400

    data = df.groupby(['vendor_name', 'severity']).size().reset_index(name='count')
    data = data[data['severity'].isin(['High', 'Low', 'Medium'])]  # Filter for desired severity levels
    pivot_data = data.pivot_table(index='vendor_name', columns='severity', values='count', aggfunc='sum', fill_value=0)
    pivot_data = pivot_data.reset_index()
    pivot_data = pivot_data.rename(columns={'vendor_name': 'label'})
    pivot_data = pivot_data.to_dict(orient='records')
    return jsonify(pivot_data)



