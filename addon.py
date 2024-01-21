# General python libs
import sys, requests
from urllib.parse import parse_qsl

# Kodi libs
import xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs

# The plugin is called with these arguments (strings)
# arg 0: Plugin URL ("plugin://plugin.module.helparr/")
# arg 1: Handle
# arg 2: Parameters from the URL ("?key=value")
# arg 3: resume:false
# Create global variables with specific types for ease of use
PLUGIN_URL      = sys.argv[0]
PLUGIN_HANDLE   = int(sys.argv[1])
PLUGIN_PARAMS   = dict(parse_qsl(sys.argv[2][1:]))
# Additional info
PLUGIN_PATH     = xbmcaddon.Addon().getAddonInfo("path")


def arr_get(manager, api_path, arguments):
    if manager == "Radarr":
        address = xbmcaddon.Addon().getSetting("radarr_addr")
        api_key = xbmcaddon.Addon().getSetting("radarr_api")
    elif manager == "Sonarr":
        address = xbmcaddon.Addon().getSetting("sonarr_addr")
        api_key = xbmcaddon.Addon().getSetting("sonarr_api")
    else:
        response = "Internal error"
        status = False
    
    url = f"{address}/api/v3/{api_path}?apikey={api_key}&{arguments}"
    
    status = False
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        response = f"HTTP Error:\n{repr(e)}"
    except requests.exceptions.ConnectionError as e:
        response = f"Error Connecting:\n{repr(e)}"
    except requests.exceptions.Timeout as e:
        response = f"Timeout Error:\n{repr(e)}"
    except requests.exceptions.RequestException as e:
        response = f"Error:\n{repr(e)}"
    else:
        status = True
    
    return status, response

def arr_post(manager, api_path, data):
    if manager == "Radarr":
        address = xbmcaddon.Addon().getSetting("radarr_addr")
        api_key = xbmcaddon.Addon().getSetting("radarr_api")
    elif manager == "Sonarr":
        address = xbmcaddon.Addon().getSetting("sonarr_addr")
        api_key = xbmcaddon.Addon().getSetting("sonarr_api")
    else:
        response = "Internal error"
        status = False
    
    url = f"{address}/api/v3/{api_path}?apikey={api_key}"
    
    status = False
    try:
        response = requests.post(url, json=data, timeout=3)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        response = f"HTTP Error:\n{repr(e)}"
    except requests.exceptions.ConnectionError as e:
        response = f"Error Connecting:\n{repr(e)}"
    except requests.exceptions.Timeout as e:
        response = f"Timeout Error:\n{repr(e)}"
    except requests.exceptions.RequestException as e:
        response = f"Error:\n{repr(e)}"
    else:
        status = True
    
    if status:
        response_json = response.json()
        if response_json.get("severity") == "error":
            response = response_json.get("errorMessage")
            status = False
        else:
            response = response_json
    
    return status, response

def exit_success():
    xbmcgui.Dialog().ok("Success", "Content added!")
    xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(offscreen=True, path=PLUGIN_PATH+"resources/data/dummy.mp4"))

def exit_fail(error):
    ret = xbmcgui.Dialog().yesno("Fail", f"{error}\n\nOpen add-on settings?")
    if ret:
        xbmcaddon.Addon().openSettings()

if __name__ == "__main__":
    # Check the parameters passed to the plugin
    if "movie" in PLUGIN_PARAMS:
        tmdb_id = PLUGIN_PARAMS["movie"]
        directory = xbmcaddon.Addon().getSetting("radarr_dir")
        if directory != "":
            data = {
                    "title": "title",
                    "qualityProfileId": 1,
                    "tmdbId": tmdb_id,
                    "rootFolderPath": directory
                }
            # Add to Radarr
            success, response = arr_post("Radarr", "movie", data)
        else:
            response = "No root folder defined"
            success = False
        
        if success:
            exit_success()
        else:
            exit_fail(response)
    elif "tvshow" in PLUGIN_PARAMS:
        tvdb_id = PLUGIN_PARAMS["tvshow"]
        directory = xbmcaddon.Addon().getSetting("sonarr_dir")
        if directory != "":
            data = {
                    "title": "title",
                    "qualityProfileId": 1,
                    "tvdbId": tvdb_id,
                    "rootFolderPath": directory
                }
            # Add to Sonarr
            success, response = arr_post("Sonarr", "series", data)
        else:
            response = "No root folder defined"
            success = False
        
        if success:
            exit_success()
        else:
            exit_fail(response)
    elif "action" in PLUGIN_PARAMS:
        action = PLUGIN_PARAMS["action"]
        if action == "AddToTmdbh":
            # First check if TheMovieDB Helper is installed
            ret = xbmcvfs.exists("special://userdata/addon_data/plugin.video.themoviedb.helper/")
            if ret:
                ret = xbmcvfs.copy(f"{PLUGIN_PATH}/resources/data/Helparr.json", "special://userdata/addon_data/plugin.video.themoviedb.helper/players/Helparr.json") 
            if ret:
                xbmcgui.Dialog().ok("Success", "Helparr added to TheMovieDb Helper.")
                #TODO: openSettings for another add-on only works if the current settings are closed
                #ret = xbmcgui.Dialog().yesno("Success", "Helparr added to TheMovieDb Helper.\nDo you want to open the settings for configuring Helparr as default player there?")
                #if ret:
                #    xbmcaddon.Addon(id='plugin.video.themoviedb.helper').openSettings()
            else:
                xbmcgui.Dialog().ok("Failed", "Something went wrong, is TheMovieDb Helper installed?")
    else:
        # No supported parameter was found, just open the settings
        xbmcaddon.Addon().openSettings()
