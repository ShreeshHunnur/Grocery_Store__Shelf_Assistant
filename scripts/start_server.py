#!/usr/bin/env python3
"""
Start the Retail Shelf Assistant API server.
"""
import uvicorn
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # Use different port when running under Electron to avoid conflicts
    port = 8001 if os.environ.get('ELECTRON_APP') == '1' else 8000
    
    print("Starting Retail Shelf Assistant API server...")
    print(f"Server will be available at: http://localhost:{port}")
    print(f"API documentation: http://localhost:{port}/docs")
    print(f"Health check: http://localhost:{port}/health")
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Disable auto-reload when running under the Electron wrapper to avoid
        # the reloader spawning behavior which can make the server appear
        # unavailable briefly (causing connection refused in Electron).
        use_reload = True
        if os.environ.get('ELECTRON_APP') == '1':
            use_reload = False

        uvicorn.run(
            "src.api.main:app",
            host="127.0.0.1",
            port=port,
            reload=use_reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
