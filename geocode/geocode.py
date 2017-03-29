import requests, os, json, re, Levenshtein
from urllib.parse import urlencode

SERVER = 'https://gis.detroitmi.gov/arcgis/rest/services/'
ADDRESS_PT = 'DoIT/AddressPointGeocoder/GeocodeServer/'
CENTERLINE = 'DoIT/StreetCenterlineGeocoder/GeocodeServer/'
ADDRESSES = 'Base/Addresses/FeatureServer/0/'

def split(address):
    """Split addresses and input into numbers and the street name"""
    m = re.match('(^[0-9]+)\s([0-9a-z\sA-Z]+)', address)
    return [m.group(1), m.group(2)]

# def slack_matched_address(matched, input):
#     webhook_url = os.environ['SLACK_ZZZ_HOOK']
#     message = "`sms-address` matched input `{}` to `{}`".format(input, matched)
#     slack_data = {'text': message}

#     response = requests.post(
#         webhook_url, data=json.dumps(slack_data),
#         headers={'Content-Type': 'application/json'}
#     )
#     if response.status_code != 200:
#         raise ValueError(
#             'Request to slack returned an error %s, the response is:\n%s'
#             % (response.status_code, response.text)
#         )

def address(address, point=True, sr=4326):
    """
    Retrieve the top match from our two geocoders.
    Defaults to address point; set point to False to use street centerline.
    """

    opts = {
        'Single Line Input': address,
        'outSR': sr,
        'outFields': '*',
        'returnGeometry': 'false',
        'geometryPrecision': 5,
        'f': 'pjson'
    }

    # use address points? or street centerline
    endpoint = ADDRESS_PT if point else CENTERLINE
    req = requests.get(SERVER + endpoint + 'findAddressCandidates?{}'.format(urlencode(opts)))
    resp = json.loads(req.text)
    # send back top match if there are matches
    if len(resp['candidates']) > 0:
        return resp['candidates'][0]
    else:
        return None

def parcels_near(coords, sr=4326, dist_in_ft=200):
    """Return a list of address points within 200 feet of a pair of coordinates"""
    opts = {
        'geometry': "{},\r\n{}".format(coords[0], coords[1]),
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': sr,
        'outSR': sr,
        'distance': dist_in_ft,
        'units': 'esriSRUnit_Foot',
        'returnGeometry': 'false',
        'outFields': '*',
        'f': 'pjson'
    }
    req = requests.get(SERVER + ADDRESSES + 'query?{}'.format(urlencode(opts)))
    resp = json.loads(req.text)
    return ["{} {}".format(r['attributes']['house_number'], r['attributes']['street_name']) for r in resp['features']]

def compare_address(address, parcel_addrs):
    """
    Gets the closest parcel address from an input and a set of parcels.
    Filters on odd/even match and a rough match ratio in the street name.
    From that set, it picks the one with the smallest house number difference.
    """

    print("Matching {}..".format(address))
    top_match = (None, 1000)
    input_housenum = int(split(address)[0])
    input_stname = split(address)[1]
    for a in parcel_addrs:
        housenum = int(split(a)[0])
        stname = split(a)[1]
        num_diff = input_housenum - housenum
        str_diff = 1 - Levenshtein.ratio(input_stname.upper(), stname.upper())
        if abs(num_diff) <= top_match[1] and num_diff % 2 == 0 and str_diff < 0.5:
            top_match = (a, abs(num_diff))
        else:
            pass
    if top_match[0]:
        return top_match[0]
    else:
        return None

def best_parcel_match(input):
    """
    Find the best match for an address and return address, centroid, parcel id.
    It will first try to find an address point
    If there no match, picks from best street centerline candidates.
    """
    point_match = address(input)
    street_match = address(input, point=False)
    if point_match:
        # return point_match
        attr = point_match['attributes']
        coords = point_match['location']
        return { 'address': attr['Match_addr'][:-7],
                 'coords': [round(coords['x'], 5), round(coords['y'], 5)],
                 'parcelid': attr['User_fld'] }
    elif street_match:
        coords = [street_match['location']['x'], street_match['location']['y']]
        compared = compare_address(input, parcels_near(coords))
        match = address(compared)
        if match:
            attr = match['attributes']
            coords = match['location']
            # slack_matched_address(attr['Match_addr'][:-7], input)
            return { 'address': attr['Match_addr'][:-7],
                     'coords': [round(coords['x'], 5), round(coords['y'], 5)],
                     'parcelid': attr['User_fld'] }
    else:
        return None

if __name__ == "__main__":
    print(best_parcel_match("12171 Grand River"))
    print(best_parcel_match("2806 Cambridge"))
