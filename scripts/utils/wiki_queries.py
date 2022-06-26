import requests
import json
from pywikibot.data import api

WIKI_BASE_URL = "https://www.wikidata.org"
WIKI_QUERY_URL = "https://query.wikidata.org/sparql"


def fetch_search_results(site, keyword, language="en"):
    """search wikidata for a given keyword"""
    # https://stackoverflow.com/a/45050455
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "errorformat": "plaintext",
        "language": language,
        "uselang": language,
        "type": "item",
        "search": keyword,
    }
    api_request = api.Request(site=site, parameters=params)
    result = api_request.submit()

    return result["search"]


def process_search_results(results, language="en"):
    """format wbsearchentities results from wikidata"""
    count = len(results)
    if count == 0:
        return []
    else:
        tmp = []
        for result in results:
            description = result["description"] if "description" in result else None
            if "label" in result:
                label = result["label"]
            elif "aliases" in result:
                label = result["aliases"][0]
            else:
                label = None

            tmp.append(
                {
                    "id": result["id"],
                    "label": label,
                    "description": description,
                    "url": result["url"],
                    "language": language,
                }
            )
        return tmp


def search_keyword(site, keyword, language="en"):
    results = fetch_search_results(site, keyword, language)
    return process_search_results(results, language)


def wikidata_query(query):
    # https://stackoverflow.com/a/66223213
    try:
        headers = {"Content-Type": "application/sparql-query"}
        response = requests.post(
            WIKI_QUERY_URL, data=query, headers=headers, params={"format": "json"}
        )
        return response.json()["results"]["bindings"]
    except json.JSONDecodeError as e:
        raise Exception("Invalid query", e)


def process_wikidata_properties(results):
    data = {}
    for result in results:
        pid = result["property"]["value"].split("/")[-1]
        value = result["propertyLabel"]["value"]
        data[pid] = value

    return data


def process_wikidata_items(results):
    data = {}
    for result in results:
        qid = result["item"]["value"].split("/")[-1]
        value = result["itemLabel"]["value"]
        data[qid] = value

    return data


def fetch_all_properties():
    """
    get all properties from wikidata

    https://stackoverflow.com/questions/25100224/how-to-get-a-list-of-all-wikidata-properties
    """

    query = """
    SELECT ?property ?propertyLabel WHERE {
        ?property a wikibase:Property .

        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
    }
    """

    return wikidata_query(query)


def fetch_and_format_all_properties():
    results = fetch_all_properties()
    return process_wikidata_properties(results)


def fetch_external_id_properties():
    """
    get all external id properties from wikidata
    """

    query = """
    SELECT ?property ?propertyLabel WHERE {
        ?property wikibase:propertyType wikibase:ExternalId .

        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """

    return wikidata_query(query)


def fetch_and_format_external_id_properties():
    results = fetch_external_id_properties()
    return process_wikidata_properties(results)


def fetch_labels_for_ids_sqarql(ids):
    """
    get labels for a given list of Q ids and property ids from wikidata using
    sparql.

    https://stackoverflow.com/a/66223213
    """

    query = """
    SELECT ?item ?itemLabel WHERE {
        VALUES ?item { %s }

        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """ % " ".join(
        ["wd:" + id for id in ids]
    )

    return wikidata_query(query)


def fetch_and_format_labels_for_ids_sqarql(ids):
    results = fetch_labels_for_ids_sqarql(ids)
    return process_wikidata_items(results)


def fetch_and_format_labels_for_ids(ids, lang="en"):
    """
    get labels for a given list of Q ids and property ids from wikidata

    https://stackoverflow.com/questions/29179564/get-description-of-a-wikidata-property
    https://www.wikidata.org/w/api.php?action=help&modules=wbgetentities
    """

    # split ids list into multiple lists because wikidata API has max limit of 50 ids
    chunk_size = 50
    chunked_list = [ids[i : i + chunk_size] for i in range(0, len(ids), chunk_size)]

    data = {}

    for chunk_ids in chunked_list:
        ids_str = "|".join(chunk_ids)
        link = (
            f"{WIKI_BASE_URL}/w/api.php?action=wbgetentities"
            f"&ids={ids_str}&props=labels&languages={lang}&format=json"
        )
        response = requests.get(link)

        if response.status_code == 200:
            json = response.json()
            if "error" not in json:
                results = json["entities"]
                for prop, value in results.items():
                    if "labels" in value and lang in value["labels"]:
                        data[prop] = value["labels"][lang]["value"]
                    else:
                        data[prop] = ""
            else:
                raise ValueError(json["error"]["info"])
        else:
            raise ValueError("Could not get labels for ids from wikidata API.")

    return data


def fetch_commons_media_metadata(site, files):
    """search wikimedia for commons media files and return the metadata"""
    params = {
        "action": "query",
        "prop": "imageinfo",
        "format": "json",
        "iiprop": "url|size|mime|thumbmime|mediatype",
        "iiurlwidth": 300,
        "titles": "|".join(files),
    }
    api_request = api.Request(site=site, parameters=params)
    results = api_request.submit()
    if "pages" in results["query"]:
        return list(results["query"]["pages"].values())
    else:
        return []


def format_commons_metadata_for_file(fields, file_data):
    tmp = {"title": file_data["title"]}
    for field in fields:
        if field in file_data["imageinfo"][0]:
            tmp[field] = file_data["imageinfo"][0][field]
    return tmp


def format_commons_media_metadata(files_data):
    image_fields = [
        "mediatype",
        "size",
        "url",
        "descriptionurl",
        "width",
        "height",
        "mime",
        "thumburl",
        "thumbwidth",
        "thumbheight",
        "thumbmime",
    ]
    audio_fields = [
        "mediatype",
        "size",
        "url",
        "descriptionurl",
        "duration",
        "mime",
    ]
    video_fields = image_fields + ["duration"]
    office_fields = image_fields + ["pagecount"]

    data = {}
    for file_data in files_data:
        if "imageinfo" not in file_data:
            continue

        if file_data["imageinfo"][0]["mediatype"] in ["BITMAP", "DRAWING", "3D"]:
            tmp = format_commons_metadata_for_file(image_fields, file_data)
        elif file_data["imageinfo"][0]["mediatype"] == "AUDIO":
            tmp = format_commons_metadata_for_file(audio_fields, file_data)
        elif file_data["imageinfo"][0]["mediatype"] == "VIDEO":
            tmp = format_commons_metadata_for_file(video_fields, file_data)

        elif file_data["imageinfo"][0]["mediatype"] == "OFFICE":
            tmp = format_commons_metadata_for_file(office_fields, file_data)

        data[file_data["title"]] = tmp

    return data


def fetch_and_format_commons_media_metadata(site, files):
    """pywikibot ItemPage only includes the file name for commons media. we
    need to  do a separate api call to get other metadata for the media.
    """
    results = fetch_commons_media_metadata(site, files)
    return format_commons_media_metadata(results)