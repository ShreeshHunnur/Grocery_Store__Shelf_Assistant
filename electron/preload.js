// Preload script - currently minimal. Keep contextIsolation enabled for security.
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Add APIs here if needed in the future
});
