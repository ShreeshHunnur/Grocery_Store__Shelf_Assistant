const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let serverProcess = null;

const PYTHON_SCRIPT = path.join(__dirname, '..', 'scripts', 'start_server.py');
const SERVER_HOST = '127.0.0.1';
const SERVER_PORT = 8000;
const SERVER_URL = `http://${SERVER_HOST}:${SERVER_PORT}`;
const HEALTH_PATH = '/health';

function waitForServer(timeoutMs = 30000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const req = http.get(`${SERVER_URL}${HEALTH_PATH}`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          if (Date.now() - start > timeoutMs) {
            reject(new Error('Server health check timed out'));
          } else {
            setTimeout(check, 500);
          }
        }
      });

      req.on('error', () => {
        if (Date.now() - start > timeoutMs) {
          reject(new Error('Server did not start in time'));
        } else {
          setTimeout(check, 500);
        }
      });
      req.setTimeout(2000, () => {
        req.abort();
      });
    };

    check();
  });
}

function startPythonServer() {
  // Spawn python process to run the FastAPI server script
  // Use 'python' from PATH; users can configure their environment if needed
  const pythonExe = process.env.PYTHON_EXECUTABLE || 'python';
  serverProcess = spawn(pythonExe, [PYTHON_SCRIPT], {
    cwd: path.join(__dirname, '..'),
    env: process.env,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  serverProcess.stdout.on('data', (data) => {
    console.log(`[server stdout] ${data.toString()}`);
  });

  serverProcess.stderr.on('data', (data) => {
    console.error(`[server stderr] ${data.toString()}`);
  });

  serverProcess.on('close', (code) => {
    console.log(`Server process exited with code ${code}`);
    // If main window still open, inform user
    if (mainWindow && !mainWindow.isDestroyed()) {
      dialog.showErrorBox('Backend stopped', 'The embedded Python server has stopped. The app may not function correctly.');
    }
  });
}

function stopPythonServer() {
  if (serverProcess && !serverProcess.killed) {
    try {
      serverProcess.kill();
    } catch (err) {
      console.error('Error killing server process:', err);
    }
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Load the UI endpoint on the local server
  const uiUrl = `${SERVER_URL}/ui`;
  mainWindow.loadURL(uiUrl).catch((err) => {
    console.error('Failed to load UI URL:', err);
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  startPythonServer();

  try {
    await waitForServer(30000);
    createWindow();
  } catch (err) {
    dialog.showErrorBox('Server start error', `Failed to start backend server: ${err.message}`);
    // Still create window pointing to server URL so user can see errors if any
    createWindow();
  }
});

app.on('window-all-closed', () => {
  // On Windows, quit the app when all windows closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopPythonServer();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Fallback to gracefully stop server on uncaught exceptions
process.on('uncaughtException', (err) => {
  console.error('Uncaught exception in Electron main:', err);
  stopPythonServer();
});
