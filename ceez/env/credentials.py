import json


def test_cred():
    api_key = 'SEpuiXmItjx3i6AGdPEwRW3zSXnYfd3P6AidqlePcuBqhjQyAt2mhnFWKab946Cp'
    api_secret = '58yJBlnGO469DPHZVD2uSSsmMa0XY5YMZT0S0H3DPbpw8eH0C1Y67vBSIKvdyfpG'
    # with open('../usr/credentials.json') as cj:
    #     usr_cred = dict(json.load(cj))
    # if usr_cred['usable']:
    #     api_key = usr_cred["api_key"]
    #     api_secret = usr_cred["api_secret"]
    # cj.close()
    return api_key, api_secret
