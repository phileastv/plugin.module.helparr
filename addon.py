# General python libs
import sys, requests, json, os
from urllib.parse import parse_qsl

# Kodi libs
import xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs, xbmc

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

def get_cache_path():
    """Get the addon cache directory path"""
    addon_data_path = xbmcvfs.translatePath("special://userdata/addon_data/plugin.module.helparr/")
    if not xbmcvfs.exists(addon_data_path):
        xbmcvfs.mkdirs(addon_data_path)
    return addon_data_path

def fetch_quality_profiles(manager):
    """Fetch quality profiles from Radarr/Sonarr API"""
    xbmc.log(f"[HELPARR] Fetching quality profiles for {manager}", xbmc.LOGINFO)
    
    status, response = arr_get(manager, "qualityprofile", "")
    if status and isinstance(response.json() if hasattr(response, 'json') else response, list):
        profiles = response.json() if hasattr(response, 'json') else response
        xbmc.log(f"[HELPARR] Found {len(profiles)} quality profiles for {manager}", xbmc.LOGINFO)
        return profiles
    else:
        xbmc.log(f"[HELPARR] Failed to fetch quality profiles for {manager}: {response}", xbmc.LOGERROR)
        return []

def cache_quality_profiles(manager, profiles):
    """Cache quality profiles to addon data folder"""
    cache_path = get_cache_path()
    cache_file = os.path.join(cache_path, f"{manager.lower()}_profiles.json")
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(profiles, f)
        xbmc.log(f"[HELPARR] Cached {len(profiles)} quality profiles for {manager}", xbmc.LOGINFO)
        return True
    except Exception as e:
        xbmc.log(f"[HELPARR] Failed to cache quality profiles for {manager}: {e}", xbmc.LOGERROR)
        return False

def load_cached_quality_profiles(manager):
    """Load cached quality profiles from addon data folder"""
    cache_path = get_cache_path()
    cache_file = os.path.join(cache_path, f"{manager.lower()}_profiles.json")
    
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                profiles = json.load(f)
            xbmc.log(f"[HELPARR] Loaded {len(profiles)} cached quality profiles for {manager}", xbmc.LOGINFO)
            return profiles
    except Exception as e:
        xbmc.log(f"[HELPARR] Failed to load cached quality profiles for {manager}: {e}", xbmc.LOGERROR)
    
    return []

def refresh_quality_profiles(manager):
    """Refresh quality profiles for a specific manager"""
    xbmc.log(f"[HELPARR] Refreshing quality profiles for {manager}", xbmc.LOGINFO)
    
    # Show progress dialog
    progress = xbmcgui.DialogProgress()
    progress.create("Refreshing Quality Profiles", f"Fetching {manager} quality profiles...")
    
    try:
        profiles = fetch_quality_profiles(manager)
        if profiles:
            cache_quality_profiles(manager, profiles)
            progress.update(100, f"Successfully refreshed {len(profiles)} profiles")
            xbmc.sleep(1000)  # Show success for 1 second
            return True
        else:
            progress.update(100, f"Failed to fetch {manager} quality profiles")
            xbmc.sleep(2000)
            return False
    finally:
        progress.close()

def get_quality_profile_by_id(manager, profile_id):
    """Get quality profile name by ID"""
    profiles = load_cached_quality_profiles(manager)
    for profile in profiles:
        if profile.get("id") == profile_id:
            return profile.get("name", f"Profile {profile_id}")
    return f"Profile {profile_id}"

def update_quality_profile_settings(manager):
    """Update the quality profile dropdown settings after refresh"""
    profiles = load_cached_quality_profiles(manager)
    if not profiles:
        xbmc.log(f"[HELPARR] No profiles to update for {manager}", xbmc.LOGWARNING)
        return
    
    xbmc.log(f"[HELPARR] Updating settings.xml with {len(profiles)} quality profiles for {manager}", xbmc.LOGINFO)
    
    # Read current settings.xml
    settings_path = os.path.join(PLUGIN_PATH, "resources", "settings.xml")
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        # Create values and lvalues for the setting
        profile_names = ["Ask"] + [profile['name'].replace("|", "") for profile in profiles]  # Remove | chars that could break XML
        values = "|".join(profile_names)
        
        # Create label values (we'll just use the profile names as labels)
        lvalues = "30403"  # "Ask" label
        for i, profile in enumerate(profiles):
            # For now, we'll create a simple numbering system for labels
            # In a real implementation, you'd want to add these to strings.po
            lvalues += f"|{profile['name']}"
        
        # Update the settings content
        setting_id = f"{manager.lower()}_quality_profile"
        old_pattern = f'<setting label=".*?" type="select"    id="{setting_id}" default="0" values=".*?" lvalues=".*?"/>'
        new_setting = f'<setting label="30{2 if manager == "Radarr" else 3}05" type="select"    id="{setting_id}" default="0" values="{values}" lvalues="{lvalues}"/>'
        
        import re
        updated_content = re.sub(old_pattern, new_setting, settings_content)
        
        # Write back the updated settings
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        xbmc.log(f"[HELPARR] Successfully updated settings.xml for {manager}", xbmc.LOGINFO)
        
        # Store profile mapping for later use
        profile_mapping = {i+1: profile['id'] for i, profile in enumerate(profiles)}
        cache_path = get_cache_path()
        mapping_file = os.path.join(cache_path, f"{manager.lower()}_profile_mapping.json")
        
        with open(mapping_file, 'w') as f:
            json.dump(profile_mapping, f)
        
        xbmc.log(f"[HELPARR] Saved profile mapping for {manager}: {profile_mapping}", xbmc.LOGINFO)
        
    except Exception as e:
        xbmc.log(f"[HELPARR] Failed to update settings.xml for {manager}: {e}", xbmc.LOGERROR)

def get_profile_id_from_setting(manager, setting_index):
    """Convert setting index to actual profile ID"""
    if setting_index == "0":  # Ask
        return None  # Will trigger dialog
    
    try:
        cache_path = get_cache_path()
        mapping_file = os.path.join(cache_path, f"{manager.lower()}_profile_mapping.json")
        
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                profile_mapping = json.load(f)
            
            # Convert string keys back to int for lookup
            profile_mapping = {int(k): v for k, v in profile_mapping.items()}
            
            setting_idx = int(setting_index)
            if setting_idx in profile_mapping:
                profile_id = profile_mapping[setting_idx]
                xbmc.log(f"[HELPARR] Mapped setting index {setting_idx} to profile ID {profile_id}", xbmc.LOGINFO)
                return profile_id
    except Exception as e:
        xbmc.log(f"[HELPARR] Error getting profile ID from setting: {e}", xbmc.LOGERROR)
    
    return 1  # Default fallback

def get_selected_quality_profile(manager):
    """Get the selected quality profile ID based on settings"""
    profile_setting = f"{manager.lower()}_quality_profile"
    setting_value = xbmcaddon.Addon().getSetting(profile_setting)
    
    xbmc.log(f"[HELPARR] {manager} quality profile setting: {setting_value}", xbmc.LOGINFO)
    
    if setting_value == "0":  # Ask
        # Show dialog to select quality profile
        profiles = load_cached_quality_profiles(manager)
        if not profiles:
            xbmc.log(f"[HELPARR] No cached profiles for {manager}, using default", xbmc.LOGWARNING)
            return 1  # Default fallback
        
        profile_names = [f"{p['name']}" for p in profiles]
        selected = xbmcgui.Dialog().select(f"Select {manager} Quality Profile", profile_names)
        
        if selected >= 0:
            profile_id = profiles[selected]["id"]
            xbmc.log(f"[HELPARR] User selected {manager} profile: {profiles[selected]['name']} (ID: {profile_id})", xbmc.LOGINFO)
            return profile_id
        else:
            xbmc.log(f"[HELPARR] User cancelled {manager} profile selection, using default", xbmc.LOGINFO)
            return 1  # Default fallback
    else:
        # Use fixed profile from setting
        profile_id = get_profile_id_from_setting(manager, setting_value)
        if profile_id:
            return profile_id
        
        xbmc.log(f"[HELPARR] Invalid {manager} profile setting, using default", xbmc.LOGWARNING)
        return 1  # Default fallback

def monitor_command_progress(manager, command_id, content_title):
    """Monitor the progress of a command and show progress dialog"""
    xbmc.log(f"[HELPARR] Starting progress monitor for {manager} command {command_id}", xbmc.LOGINFO)
    
    # Get progress monitoring interval from settings
    progress_interval = int(xbmcaddon.Addon().getSetting("progress_interval"))
    xbmc.log(f"[HELPARR] Using progress monitoring interval: {progress_interval} seconds", xbmc.LOGINFO)
    
    # Create progress dialog
    progress = xbmcgui.DialogProgress()
    progress.create("Searching for Content", f"Searching for '{content_title}'...")
    
    # Monitor progress
    max_attempts = (5 * 60) // progress_interval  # Monitor for up to 5 minutes
    attempt = 0
    minimized = False
    
    while attempt < max_attempts:
        if progress.iscanceled() and not minimized:
            # Ask user if they want to continue in background
            continue_background = xbmcgui.Dialog().yesno(
                "Continue in background?", 
                f"Search is still running for '{content_title}'.\n\nContinue monitoring in the background?"
            )
            if continue_background:
                minimized = True
                progress.close()
                xbmc.log("[HELPARR] User chose to continue monitoring in background", xbmc.LOGINFO)
            else:
                progress.close()
                xbmc.log("[HELPARR] User cancelled progress monitoring", xbmc.LOGINFO)
                return
        
        # Get command status
        status, response = arr_get(manager, f"command/{command_id}", "")
        
        if status and hasattr(response, 'json'):
            command_data = response.json()
            command_status = command_data.get('status', 'unknown')
            command_name = command_data.get('commandName', 'Search')
            
            xbmc.log(f"[HELPARR] Command {command_id} status: {command_status}", xbmc.LOGINFO)
            
            if command_status == 'completed':
                if not minimized:
                    progress.update(100, f"{command_name} completed for '{content_title}'!")
                    xbmc.sleep(1500)
                    progress.close()
                
                # Show notification
                xbmcgui.Dialog().notification(
                    "Helparr", 
                    f"Search completed for '{content_title}'", 
                    xbmcgui.NOTIFICATION_INFO, 
                    3000
                )
                
                # Check if content was found/downloaded
                check_content_status(manager, content_title, command_data)
                return
                
            elif command_status == 'failed':
                if not minimized:
                    progress.update(100, f"{command_name} failed!")
                    xbmc.sleep(2000)
                    progress.close()
                
                xbmcgui.Dialog().notification(
                    "Helparr", 
                    f"Search failed for '{content_title}'", 
                    xbmcgui.NOTIFICATION_ERROR, 
                    5000
                )
                return
                
            elif command_status in ['queued', 'started']:
                # Show progress
                progress_percent = min(90, (attempt * 90) // max_attempts)  # Max 90% until completed
                if not minimized:
                    progress.update(progress_percent, f"{command_name} in progress...")
            
        elif not minimized:
            # API call failed
            progress.update(50, "Monitoring connection issues...")
        
        # Wait before next check
        if not minimized and progress.iscanceled():
            continue  # Handle cancellation at top of loop
        
        xbmc.sleep(progress_interval * 1000)  # Convert seconds to milliseconds
        attempt += 1
    
    # Timeout reached
    if not minimized:
        progress.close()
    
    xbmcgui.Dialog().notification(
        "Helparr", 
        f"Progress monitoring timed out for '{content_title}'", 
        xbmcgui.NOTIFICATION_WARNING, 
        3000
    )

def check_content_status(manager, content_title, command_data):
    """Check if content was actually found and downloaded"""
    # This could be expanded to check download queue, etc.
    # For now, just show completion notification
    xbmc.log(f"[HELPARR] Search completed for {content_title} in {manager}", xbmc.LOGINFO)
    
    # Could add logic here to:
    # - Check if files were found
    # - Monitor download progress
    # - Show detailed results

def arr_search_command(manager, content_type, content_id):
    """
    Trigger search command for specific content in Radarr/Sonarr
    """
    xbmc.log(f"[HELPARR] arr_search_command called with manager={manager}, content_type={content_type}, content_id={content_id}", xbmc.LOGINFO)
    
    # Ensure content_id is an integer
    try:
        content_id = int(content_id)
        xbmc.log(f"[HELPARR] Converted content_id to integer: {content_id}", xbmc.LOGINFO)
    except (ValueError, TypeError):
        error_msg = f"Invalid content_id: {content_id}"
        xbmc.log(f"[HELPARR] Error: {error_msg}", xbmc.LOGERROR)
        return False, error_msg
    
    if manager == "Radarr" and content_type == "movie":
        command_name = "MoviesSearch"
        data = {"name": command_name, "movieIds": [content_id]}
        xbmc.log(f"[HELPARR] Radarr movie search command data: {data}", xbmc.LOGINFO)
    elif manager == "Sonarr" and content_type == "series":
        command_name = "SeriesSearch"
        data = {"name": command_name, "seriesId": content_id}
        xbmc.log(f"[HELPARR] Sonarr series search command data: {data}", xbmc.LOGINFO)
    else:
        error_msg = "Unsupported manager or content type"
        xbmc.log(f"[HELPARR] Error: {error_msg}", xbmc.LOGERROR)
        return False, error_msg
    
    status, response = arr_post(manager, "command", data)
    xbmc.log(f"[HELPARR] Search command result - status: {status}, response: {response}", xbmc.LOGINFO)
    return status, response

def exit_success():
    xbmcgui.Dialog().ok("Success", "Content added!")
    xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(offscreen=True, path=PLUGIN_PATH+"resources/data/dummy.mp4"))

def exit_success_with_search(manager, content_type, content_id, content_title):
    """
    Handle successful content addition with optional search functionality
    """
    xbmc.log(f"[HELPARR] exit_success_with_search called with manager={manager}, content_type={content_type}, content_id={content_id}, content_title={content_title}", xbmc.LOGINFO)
    
    search_mode_index = xbmcaddon.Addon().getSetting("search_mode")
    xbmc.log(f"[HELPARR] Search mode setting index: '{search_mode_index}'", xbmc.LOGINFO)
    
    # Convert index to actual mode (Kodi select settings return indices)
    search_modes = ["Always", "Ask", "Never"]
    try:
        search_mode = search_modes[int(search_mode_index)]
        xbmc.log(f"[HELPARR] Converted search mode: '{search_mode}'", xbmc.LOGINFO)
    except (ValueError, IndexError):
        search_mode = "Ask"  # Default fallback
        xbmc.log(f"[HELPARR] Invalid search mode index, using default: '{search_mode}'", xbmc.LOGWARNING)
    
    should_search = False
    if search_mode == "Always":
        should_search = True
        xbmc.log("[HELPARR] Search mode is Always - will search automatically", xbmc.LOGINFO)
    elif search_mode == "Ask":
        xbmc.log("[HELPARR] Search mode is Ask - showing dialog", xbmc.LOGINFO)
        should_search = xbmcgui.Dialog().yesno("Search for missing content", f"Content added successfully!\n\nStart search for '{content_title}'?")
        xbmc.log(f"[HELPARR] User dialog response: {should_search}", xbmc.LOGINFO)
    else:
        xbmc.log(f"[HELPARR] Search mode is Never - skipping search", xbmc.LOGINFO)
    # search_mode == "Never" - should_search remains False
    
    if should_search:
        xbmc.log("[HELPARR] Starting search command", xbmc.LOGINFO)
        success, response = arr_search_command(manager, content_type, content_id)
        if success:
            # Extract command ID for progress monitoring
            command_id = None
            if isinstance(response, dict):
                command_id = response.get('id')
            
            if command_id:
                xbmc.log(f"[HELPARR] Search started with command ID: {command_id}", xbmc.LOGINFO)
                
                # Start progress monitoring in the background
                import threading
                progress_thread = threading.Thread(
                    target=monitor_command_progress, 
                    args=(manager, command_id, content_title)
                )
                progress_thread.daemon = True
                progress_thread.start()
                
                # Show initial success message
                xbmcgui.Dialog().notification(
                    "Helparr", 
                    f"Search started for '{content_title}'", 
                    xbmcgui.NOTIFICATION_INFO, 
                    2000
                )
            else:
                success_msg = f"Content added and search started for '{content_title}'!"
                xbmc.log(f"[HELPARR] Search successful: {success_msg}", xbmc.LOGINFO)
                xbmcgui.Dialog().ok("Search started", success_msg)
        else:
            error_msg = f"Content added successfully, but search failed:\n{response}"
            xbmc.log(f"[HELPARR] Search failed: {response}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Search failed", error_msg)
    else:
        xbmc.log("[HELPARR] Not searching - showing standard success dialog", xbmc.LOGINFO)
        xbmcgui.Dialog().ok("Success", "Content added!")
    
    xbmc.log("[HELPARR] Setting resolved URL", xbmc.LOGINFO)
    xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(offscreen=True, path=PLUGIN_PATH+"resources/data/dummy.mp4"))

def exit_fail(error):
    ret = xbmcgui.Dialog().yesno("Fail", f"{error}\n\nOpen add-on settings?")
    if ret:
        xbmcaddon.Addon().openSettings()

if __name__ == "__main__":
    xbmc.log("[HELPARR] Addon started", xbmc.LOGINFO)
    xbmc.log(f"[HELPARR] Plugin params: {PLUGIN_PARAMS}", xbmc.LOGINFO)
    
    # Check the parameters passed to the plugin
    if "movie" in PLUGIN_PARAMS:
        xbmc.log("[HELPARR] Processing movie request", xbmc.LOGINFO)
        tmdb_id = PLUGIN_PARAMS["movie"]
        xbmc.log(f"[HELPARR] TMDB ID: {tmdb_id}", xbmc.LOGINFO)
        directory = xbmcaddon.Addon().getSetting("radarr_dir")
        xbmc.log(f"[HELPARR] Radarr directory: {directory}", xbmc.LOGINFO)
        if directory != "":
            # Get selected quality profile
            quality_profile_id = get_selected_quality_profile("Radarr")
            
            data = {
                    "title": "title",
                    "qualityProfileId": quality_profile_id,
                    "tmdbId": tmdb_id,
                    "rootFolderPath": directory
                }
            xbmc.log(f"[HELPARR] Radarr POST data: {data}", xbmc.LOGINFO)
            # Add to Radarr
            success, response = arr_post("Radarr", "movie", data)
            xbmc.log(f"[HELPARR] Radarr add result - success: {success}", xbmc.LOGINFO)
            if success:
                xbmc.log(f"[HELPARR] Radarr response data: {response}", xbmc.LOGINFO)
        else:
            response = "No root folder defined"
            success = False
            xbmc.log("[HELPARR] No Radarr root folder defined", xbmc.LOGERROR)
        
        if success:
            xbmc.log("[HELPARR] Movie added successfully, calling search function", xbmc.LOGINFO)
            # Extract the internal ID and title from the response for search
            if isinstance(response, dict):
                content_id = response.get("id", tmdb_id)  # Use internal Radarr ID
                content_title = response.get("title", f"Movie {tmdb_id}")  # Use actual title
                xbmc.log(f"[HELPARR] Extracted Radarr movie ID: {content_id}, title: '{content_title}'", xbmc.LOGINFO)
            else:
                content_id = tmdb_id  # Fallback
                content_title = f"Movie {tmdb_id}"
                xbmc.log("[HELPARR] Could not extract movie details from response, using fallback", xbmc.LOGWARNING)
            exit_success_with_search("Radarr", "movie", content_id, content_title)
        else:
            xbmc.log(f"[HELPARR] Movie add failed: {response}", xbmc.LOGERROR)
            exit_fail(response)
    elif "tvshow" in PLUGIN_PARAMS:
        xbmc.log("[HELPARR] Processing TV show request", xbmc.LOGINFO)
        tvdb_id = PLUGIN_PARAMS["tvshow"]
        xbmc.log(f"[HELPARR] TVDB ID: {tvdb_id}", xbmc.LOGINFO)
        directory = xbmcaddon.Addon().getSetting("sonarr_dir")
        xbmc.log(f"[HELPARR] Sonarr directory: {directory}", xbmc.LOGINFO)
        if directory != "":
            # Get selected quality profile
            quality_profile_id = get_selected_quality_profile("Sonarr")
            
            data = {
                    "title": "title",
                    "qualityProfileId": quality_profile_id,
                    "tvdbId": tvdb_id,
                    "rootFolderPath": directory
                }
            xbmc.log(f"[HELPARR] Sonarr POST data: {data}", xbmc.LOGINFO)
            # Add to Sonarr
            success, response = arr_post("Sonarr", "series", data)
            xbmc.log(f"[HELPARR] Sonarr add result - success: {success}", xbmc.LOGINFO)
            if success:
                xbmc.log(f"[HELPARR] Sonarr response data: {response}", xbmc.LOGINFO)
        else:
            response = "No root folder defined"
            success = False
            xbmc.log("[HELPARR] No Sonarr root folder defined", xbmc.LOGERROR)
        
        if success:
            xbmc.log("[HELPARR] TV show added successfully, calling search function", xbmc.LOGINFO)
            # Extract the internal ID and title from the response for search
            if isinstance(response, dict):
                content_id = response.get("id", tvdb_id)  # Use internal Sonarr ID
                content_title = response.get("title", f"Series {tvdb_id}")  # Use actual title
                xbmc.log(f"[HELPARR] Extracted Sonarr series ID: {content_id}, title: '{content_title}'", xbmc.LOGINFO)
            else:
                content_id = tvdb_id  # Fallback
                content_title = f"Series {tvdb_id}"
                xbmc.log("[HELPARR] Could not extract series details from response, using fallback", xbmc.LOGWARNING)
            exit_success_with_search("Sonarr", "series", content_id, content_title)
        else:
            xbmc.log(f"[HELPARR] TV show add failed: {response}", xbmc.LOGERROR)
            exit_fail(response)
    elif "action" in PLUGIN_PARAMS:
        action = PLUGIN_PARAMS["action"]
        xbmc.log(f"[HELPARR] Processing action: {action}", xbmc.LOGINFO)
        
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
        elif action == "RefreshRadarrProfiles":
            success = refresh_quality_profiles("Radarr")
            if success:
                # Update settings dropdown
                update_quality_profile_settings("Radarr")
            else:
                xbmcgui.Dialog().ok("Error", "Failed to refresh Radarr quality profiles.\nCheck your Radarr connection settings.")
        elif action == "RefreshSonarrProfiles":
            success = refresh_quality_profiles("Sonarr")
            if success:
                # Update settings dropdown
                update_quality_profile_settings("Sonarr")
            else:
                xbmcgui.Dialog().ok("Error", "Failed to refresh Sonarr quality profiles.\nCheck your Sonarr connection settings.")
    else:
        # No supported parameter was found, just open the settings
        xbmcaddon.Addon().openSettings()
