# General python libs
import sys
from urllib.parse import parse_qsl

# Kodi libs
import xbmcgui, xbmcaddon, xbmcplugin

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
PLUGIN_ID       = PLUGIN_URL[9:-1]
PLUGIN_PATH     = xbmcaddon.Addon(PLUGIN_ID).getAddonInfo("path")

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
    else:
        # No supported parameter was found, show a warning dialog
        xbmcgui.Dialog().ok("Attention", "This plugin can not be run independently.")
        #TODO Note to JSON/wiki
