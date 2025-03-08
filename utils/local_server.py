"""
Local HTTP server for serving overlay files.
"""
import http.server
import socketserver
import os
import threading
import logging

logger = logging.getLogger("TwitchTracker.LocalServer")

def start_local_server(directory_path, port=8000):
    """
    Start a local HTTP server to serve overlay files.
    
    Args:
        directory_path: Path to the directory containing overlay files
        port: Port number for the server
        
    Returns:
        tuple: (server_url, server_thread)
    """
    try:
        # Create a custom handler that allows CORS
        class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                super().end_headers()
                
            def log_message(self, format, *args):
                # Redirect logs to our logger
                logger.debug(format % args)
        
        # We're serving from the parent directory of 'directory_path'
        # This way, the files will be accessed as /static/filename.html
        parent_dir = os.path.dirname(os.path.abspath(directory_path))
        
        logger.info(f"Starting server from directory: {parent_dir}")
        logger.info(f"Static files located in: {os.path.basename(directory_path)}")
        
        # Change to parent directory
        original_dir = os.getcwd()
        os.chdir(parent_dir)
        
        # Try to find an available port if the default is in use
        for attempt_port in range(port, port + 10):
            try:
                httpd = socketserver.TCPServer(("", attempt_port), CORSHTTPRequestHandler)
                actual_port = attempt_port
                break
            except OSError:
                logger.warning(f"Port {attempt_port} is in use, trying next port...")
                if attempt_port == port + 9:  # Last attempt
                    logger.error("Could not find an available port")
                    os.chdir(original_dir)  # Restore original directory
                    return None, None
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        
        server_url = f"http://localhost:{actual_port}"
        logger.info(f"Started local server at {server_url}")
        
        # Change back to original directory
        os.chdir(original_dir)
        
        # Return the server URL and the folder name to use in URLs
        static_folder = os.path.basename(directory_path)
        return f"{server_url}/{static_folder}", server_thread
    except Exception as e:
        logger.error(f"Failed to start local server: {e}")
        return None, None