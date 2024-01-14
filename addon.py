# General python libs
import sys
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


def exit_success():
    xbmcgui.Dialog().ok("Success", "Content added!")
    xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(offscreen=True, path=PLUGIN_PATH+"resources/data/dummy.mp4"))

if __name__ == "__main__":
    # Check the parameters passed to the plugin
    if "movie" in PLUGIN_PARAMS:
        # Add to Radarr
        #TODO
        xbmcgui.Dialog().ok("Movie", f"{PLUGIN_PARAMS}")
        #TODO
        if True:
            exit_success()
    elif "tvshow" in PLUGIN_PARAMS:
        # Add to Sonarr
        #TODO
        xbmcgui.Dialog().ok("TVShow", f"{PLUGIN_PARAMS}")
        #TODO
        if True:
            exit_success()
    elif "action" in PLUGIN_PARAMS:
        if PLUGIN_PARAMS["action"] == "AddToTmdbh":
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
