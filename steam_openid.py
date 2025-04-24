from flask import request, redirect
import urllib.parse

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

def get_steam_openid_url(return_to):
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": request.host_url,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return f"{STEAM_OPENID_URL}?{urllib.parse.urlencode(params)}"

def parse_steam_id(identity_url):
    return identity_url.split("/")[-1]
