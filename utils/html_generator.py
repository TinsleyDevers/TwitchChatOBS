"""
HTML overlay generator for the Twitch Tracker application.
"""
import os
import logging

logger = logging.getLogger("TwitchTracker.HTMLGenerator")


def create_html_overlay(output_path: str, server_url: str = None) -> bool:
    """
    Create an HTML overlay file for OBS browser source.
    
    Args:
        output_path: Path where the HTML file should be saved
        server_url: Optional URL of the local server (for fetch requests)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the HTML content
        html_content = get_html_overlay_content(server_url)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Created HTML overlay at {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to create HTML overlay: {e}")
        return False


def get_html_overlay_content(server_url: str = None) -> str:
    """
    Get the HTML content for the overlay.
    
    Args:
        server_url: Optional URL of the local server (for fetch requests)
        
    Returns:
        str: HTML content
    """
    # Start with standard HTML
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Twitch Emote/Word Tracker Overlay</title>
    <style>
        :root {
            --accent-color: #5a32a8;
            --text-color: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.7);
            --bg-color: rgba(0, 0, 0, 0.3);
        }
        
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Arial', sans-serif;
            background-color: transparent;
        }
        
        #debug {
            position: fixed;
            top: 10px;
            left: 10px;
            color: var(--text-color);
            font-size: 12px;
            z-index: 100;
            background-color: var(--bg-color);
            padding: 5px;
            border-radius: 3px;
            max-width: 80%;
            overflow: hidden;
            display: none; /* Initially hidden */
        }
        
        #container {
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: flex-start;
            padding: 20px;
            box-sizing: border-box;
        }
        
        .counter-item {
            text-align: left;
            color: var(--text-color);
            text-shadow: 2px 2px 4px var(--shadow-color);
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            background-color: var(--bg-color);
            border-radius: 10px;
            padding: 8px 15px;
            backdrop-filter: blur(2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            border-left: 4px solid var(--accent-color);
        }
        
        .emote-container {
            display: flex;
            align-items: center;
        }
        
        .emote {
            font-size: 42px;
            margin-right: 5px;
        }
        
        .emote-img {
            height: 36px;
            vertical-align: middle;
            margin-right: 10px;
        }
        
        .combo {
            font-size: 24px;
            opacity: 0.9;
            margin-left: 10px;
            background-color: var(--accent-color);
            border-radius: 5px;
            padding: 2px 8px;
        }
        
        .contributors {
            font-size: 14px;
            opacity: 0.7;
            margin-left: 10px;
            font-weight: normal;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes slide {
            from { transform: translateX(-50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease forwards;
        }
        
        .bounce {
            animation: bounce 0.6s ease;
        }
        
        .pulse {
            animation: pulse 0.6s ease;
        }
        
        .slide {
            animation: slide 0.5s ease forwards;
        }
        
        /* Container positioning */
        .top-left {
            justify-content: flex-start;
            align-items: flex-start;
        }
        
        .top-right {
            justify-content: flex-start;
            align-items: flex-end;
        }
        
        .bottom-left {
            justify-content: flex-end;
            align-items: flex-start;
        }
        
        .bottom-right {
            justify-content: flex-end;
            align-items: flex-end;
        }
    </style>
</head>
<body>
    <div id="container" class="bottom-left">
        <!-- Combo items will be inserted here -->
    </div>
    
    <div id="debug"></div>

    <script>
        // Configuration (will be updated by overlay_data.json)
        let config = {
            position: 'bottom-left',
            scale: 1.0,
            font: 'Arial',
            accentColor: '#5a32a8'
        };
        
        // DEBUGGING
        const debugElement = document.getElementById('debug');
        let debugMode = false; // Start with debug off

        function debug(message) {
            if (!debugMode) return;
            
            if (typeof message === 'object') {
                message = JSON.stringify(message, null, 2);
            }
            
            const timestamp = new Date().toTimeString().split(' ')[0];
            debugElement.innerHTML = `[${timestamp}] ${message}`;
            console.log(`[${timestamp}] ${message}`);
        }

        // Toggle debug mode with 'd' key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'd') {
                debugMode = !debugMode;
                debugElement.style.display = debugMode ? 'block' : 'none';
                debug(debugMode ? "Debug mode enabled" : "Debug mode disabled");
            }
        });

        // Apply configuration
        function applyConfig(config) {
            // Set position
            const container = document.getElementById('container');
            container.className = config.position || 'bottom-left';
            
            // Set scale
            document.documentElement.style.setProperty('--scale', config.scale || 1.0);
            document.body.style.fontSize = `${(config.scale || 1.0) * 100}%`;
            
            // Set accent color
            document.documentElement.style.setProperty('--accent-color', config.accentColor || '#5a32a8');
            
            // Set font
            if (config.font) {
                document.body.style.fontFamily = config.font + ', sans-serif';
            }
        }

        // MAIN FUNCTIONALITY
        const container = document.getElementById('container');
        let activeItems = {}; // Track all active combo items
        
        // Function to get the base URL for server
        function getBaseUrl() {
            // If the URL already includes the server URL, use that
            const pathSegments = window.location.pathname.split('/');
            const lastSegment = pathSegments[pathSegments.length - 1];
            
            // If the last segment is overlay.html, we're in the static directory
            if (lastSegment === 'overlay.html') {
                return '';
            }
            
            return '';
        }
        
        function updateDisplay(data) {
            debug("Updating display with data: " + JSON.stringify(data));
            
            // Update config if provided
            if (data.config) {
                config = { ...config, ...data.config };
                applyConfig(config);
            }
            
            // Ensure data has the expected structure
            if (!data || !data.items || !Array.isArray(data.items)) {
                debug("Invalid data format: missing items array");
                return;
            }
            
            // Clear container if no items
            if (data.items.length === 0) {
                debug("No items to display, clearing container");
                container.innerHTML = '';
                activeItems = {};
                return;
            }
            
            // Filter out expired items from the incoming data
            const now = Date.now();
            const validItems = data.items.filter(item => {
                const isExpired = item.expires && now > item.expires;
                if (isExpired) {
                    debug(`Ignoring already-expired item: ${item.text}`);
                }
                return !isExpired;
            });
            
            // If all items are expired, clear the display
            if (validItems.length === 0) {
                debug("All items are expired, clearing display");
                container.innerHTML = '';
                activeItems = {};
                return;
            }
            
            // Process each valid item
            validItems.forEach(item => {
                if (!item || !item.text) {
                    debug(`Skipping invalid item: ${JSON.stringify(item)}`);
                    return;
                }
                
                const id = `item-${item.text.replace(/[^a-zA-Z0-9]/g, '')}`;
                debug(`Processing item ${id}: ${JSON.stringify(item)}`);
                
                // Check if this item already exists
                let itemElement = document.getElementById(id);
                let isNewItem = false;
                
                if (!itemElement) {
                    debug(`Creating new element for ${id}`);
                    // Create new element
                    itemElement = document.createElement('div');
                    itemElement.id = id;
                    itemElement.className = 'counter-item fade-in';
                    container.appendChild(itemElement);
                    isNewItem = true;
                } else {
                    debug(`Updating existing element for ${id}`);
                    // Update animation if combo increased
                    const oldCombo = activeItems[id] ? activeItems[id].combo : 0;
                    if (item.combo > oldCombo) {
                        const animation = item.animation || 'bounce';
                        itemElement.classList.remove('bounce', 'pulse', 'slide');
                        void itemElement.offsetWidth; // Trigger reflow to restart animation
                        itemElement.classList.add(animation);
                    }
                }
                
                // Build the HTML content
                let displayHtml = '';
                
                // Create emote/word display
                displayHtml += '<div class="emote-container">';
                
                if (item.is_emote) {
                    // First try to use local emote path if available
                    if (item.local_emote_path) {
                        const baseUrl = getBaseUrl();
                        const localEmoteUrl = `${baseUrl}${item.local_emote_path}`;
                        debug(`Using local emote path for ${item.text}: ${localEmoteUrl}`);
                        displayHtml += `<img src="${localEmoteUrl}" class="emote-img" alt="${item.text}" onerror="this.onerror=null; this.src='${item.emote_url || ''}'; if(!this.src) { this.innerHTML='${item.text}'; this.className='emote'; }">`;
                    } else if (item.emote_url) {
                        debug(`Using emote image URL for ${item.text}: ${item.emote_url}`);
                        displayHtml += `<img src="${item.emote_url}" class="emote-img" alt="${item.text}" onerror="this.onerror=null; this.innerHTML='${item.text}'; this.className='emote';">`;
                    } else if (item.emote_id) {
                        debug(`Using emote image ID for ${item.text}: ${item.emote_id}`);
                        const emoteUrl = `https://static-cdn.jtvnw.net/emoticons/v2/${item.emote_id}/default/dark/3.0`;
                        displayHtml += `<img src="${emoteUrl}" class="emote-img" alt="${item.text}" onerror="this.onerror=null; this.innerHTML='${item.text}'; this.className='emote';">`;
                    } else {
                        debug(`Using text for emote ${item.text} (no ID available)`);
                        displayHtml += `<span class="emote">${item.text}</span>`;
                    }
                } else {
                    debug(`Using text for word ${item.text}`);
                    displayHtml += `<span>${item.text}</span>`;
                }
                
                displayHtml += '</div>';
                
                // Add combo counter
                if (item.combo && item.combo > 1) {
                    debug(`Adding combo count ${item.combo} for ${item.text}`);
                    displayHtml += `<span class="combo">x${item.combo}</span>`;
                }
                
                // Add contributors (limit to first 3)
                if (item.contributors && item.contributors.length > 0) {
                    const displayContributors = item.contributors.slice(0, 3).join(', ');
                    const extraCount = item.contributors.length > 3 ? ` +${item.contributors.length - 3}` : '';
                    displayHtml += `<span class="contributors">by ${displayContributors}${extraCount}</span>`;
                }
                
                // Update the element
                itemElement.innerHTML = displayHtml;
                
                // Calculate expiration - use provided or default to 10 seconds from now
                const now = Date.now();
                const expires = item.expires && !isNaN(item.expires) 
                    ? parseInt(item.expires) 
                    : now + 10000;
                
                // Update tracking info
                activeItems[id] = {
                    timestamp: now,
                    expires: expires,
                    combo: item.combo
                };
                
                debug(`Item ${id} will expire at ${new Date(expires).toTimeString()}`);
            });
            
            // Remove items not in the current data
            const currentIds = validItems
                .filter(item => item && item.text)
                .map(item => `item-${item.text.replace(/[^a-zA-Z0-9]/g, '')}`);
            
            Array.from(container.children).forEach(child => {
                if (!currentIds.includes(child.id)) {
                    // Only remove if not already being removed
                    if (!activeItems[child.id] || !activeItems[child.id].removing) {
                        debug(`Removing element ${child.id} as it's no longer active`);
                        // Add fade-out animation then remove
                        child.style.transition = 'opacity 0.5s ease';
                        child.style.opacity = '0';
                        
                        // Mark as removing
                        if (activeItems[child.id]) {
                            activeItems[child.id].removing = true;
                        }
                        
                        setTimeout(() => {
                            try {
                                if (child.parentNode) {
                                    container.removeChild(child);
                                    debug(`Removed element ${child.id} from DOM`);
                                }
                            } catch (err) {
                                debug(`Error removing element: ${err.message}`);
                            }
                            delete activeItems[child.id];
                            debug(`Removed ${child.id} from tracking`);
                        }, 500);
                    }
                }
            });
        }
        
        function cleanupExpiredItems() {
            const now = Date.now();
            
            Object.entries(activeItems).forEach(([id, info]) => {
                // Only process items that have an expiration time, aren't already being removed,
                // and have passed their expiration time
                if (info.expires && !info.removing && now > info.expires) {
                    debug(`Item ${id} expired at ${new Date(info.expires).toTimeString()}, current time: ${new Date(now).toTimeString()}`);
                    
                    // Mark the item as being removed so we don't try to remove it again
                    activeItems[id].removing = true;
                    
                    const element = document.getElementById(id);
                    if (element) {
                        // Add fade-out animation then remove
                        element.style.transition = 'opacity 0.5s ease';
                        element.style.opacity = '0';
                        
                        setTimeout(() => {
                            try {
                                if (element.parentNode) {
                                    container.removeChild(element);
                                    debug(`Removed element ${id} from DOM`);
                                }
                            } catch (err) {
                                debug(`Error removing element: ${err.message}`);
                            } finally {
                                // Always remove from tracking, even if DOM removal fails
                                delete activeItems[id];
                                debug(`Removed ${id} from tracking`);
                            }
                        }, 500);
                    } else {
                        // If element doesn't exist, just remove from tracking
                        delete activeItems[id];
                        debug(`No DOM element for ${id}, removed from tracking only`);
                    }
                }
            });
        }
        
        // Function to load data with error handling"""
    
    # Insert the server-specific fetch code
    fetch_code = """
        function loadData() {
            const cacheBuster = `?t=${Date.now()}`;
            const xhr = new XMLHttpRequest();
            xhr.overrideMimeType("application/json");
            xhr.open('GET', `overlay_data.json${cacheBuster}`, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            const data = JSON.parse(xhr.responseText);
                            debug("Fetched new data successfully");
                            updateDisplay(data);
                            cleanupExpiredItems();
                        } catch (error) {
                            debug(`Error parsing JSON: ${error.message}`);
                        }
                    } else {
                        debug(`Error fetching data: Status ${xhr.status}`);
                    }
                }
            };
            xhr.send(null);
        }
    """
    
    # If we have a server URL, modify the fetch code to use that URL
    if server_url:
        # The JSON data will still be in the static folder, so we need to use the correct path
        fetch_code = f"""
        function loadData() {{
            const cacheBuster = `?t=${{Date.now()}}`;
            fetch(`{server_url.rstrip('/')}/overlay_data.json${{cacheBuster}}`)
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error(`HTTP error ${{response.status}}`);
                    }}
                    return response.json();
                }})
                .then(data => {{
                    debug("Fetched new data successfully");
                    updateDisplay(data);
                    cleanupExpiredItems();
                }})
                .catch(error => {{
                    debug(`Error fetching data: ${{error.message}}`);
                    // Try to enable debug mode on error
                    if (!debugMode) {{
                        debugMode = true;
                        debugElement.style.display = 'block';
                        debug("Debug mode enabled automatically due to error");
                    }}
                }});
        }}
        """
    
    # Complete the HTML
    html_content += fetch_code + """
        
        // Apply initial config
        applyConfig(config);
        
        // Check for updates every 300ms
        setInterval(loadData, 300);
        
        // Initial load
        debug("Overlay initialized, loading initial data");
        loadData();
    </script>
</body>
</html>
"""
    
    return html_content